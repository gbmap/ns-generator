"""creates scene resources"""

import base64
from collections import deque
from typing import List, Union
import pickle
import os
import yaml

from natural_stupidity import scene as sc
from natural_stupidity import command as cmd

from . import txt2img
from . import txt2spe
from . import sbboxpred
from . import sfx
from loguru import logger


CONFIG_PATH = os.environ.get("NS_GENERATOR_CONFIG_FILE", "config.yaml")


def get_config():
    with open(CONFIG_PATH, "r") as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
    return config


def generate_scene_resources(scene: sc.Scene, cmds: List[cmd.Command]):
    config = get_config()

    char_cache_queue = deque([], maxlen=len(scene.stage))

    logger.info("[🖼️  ] generating character frames")
    for name, character in scene.stage.items():
        if isinstance(character.frames, str):
            logger.info(f"\t{name}: {character.frames}")
            if _c := load_char_cache(name, character.frames):
                logger.info("\tfound cache.")
                scene.stage[name] = _c
                continue

            char_cache_queue.append((name, character.frames, character))
            character.frames = txt2img.generate_frames(
                [character.frames + " in a (((bland background)))"],
                ip=config["txt2img"]["hostname"],
                port=config["txt2img"]["port"],
            )[0].imgs

            if character.voice:
                character.frames = txt2img.postproc_char(
                    character.frames,
                    int(os.environ.get("NS_UPSCALE", 1)),
                    hostname=config["txt2img"]["hostname"],
                    port=config["txt2img"]["port"],
                )
            else:
                character.frames = txt2img.upscale(
                    character.frames,
                    int(os.environ.get("NS_UPSCALE", 1)),
                    hostname=config["txt2img"]["hostname"],
                    port=config["txt2img"]["port"],
                )

    logger.info("[👄] predicting mouth bbox")
    for name, character in scene.stage.items():
        if character.voice is None:
            continue
        if character.mouth is not None:
            continue
        logger.info(f"\t{name}")
        bbox_pred, index = None, 0
        while bbox_pred is None and index < len(character.frames):
            bbox_pred = sbboxpred.predict(
                character.frames[index],
                config["sbboxpred"]["hostname"],
                config["sbboxpred"]["port"],
            )
            index += 1

        if not bbox_pred and index == len(character.frames):
            raise ValueError(f"Couldn't predict mouth bounding box for {name}.")

        character.mouth = bbox_pred

    # cache characters
    while char_cache_queue:
        name, prompt, data = char_cache_queue.popleft()
        fname = cache_character(data, name, prompt)
        logger.debug(f"\tcached {name} to {fname}")

    logger.info("[🔊] generating character voice")
    for character in scene.audios.keys():
        logger.info(f"\t{character}")
        lines = list(scene.audios[character].keys())
        audios, sr = txt2spe.generate(
            lines,
            scene.stage[character].voice,
            config["tts"]["hostname"],
            config["tts"]["port"],
        )

        for audio, line in zip(audios, lines):
            scene.audios[character][line] = sc.Audio(audio, sr)

    for c in cmd.extract(cmds, lambda c: isinstance(c, cmd.Say)):
        c.duration = scene.audios[c.char][c.line].duration()

    logger.info("[ ] generating sound effects")
    prompts = []
    durations = []
    for c in cmd.extract(cmds, lambda c: isinstance(c, cmd.SFX)):
        prompts.append(c.prompt)
        durations.append(float(c.duration))

    sfxs = sfx.generate(
        prompts, durations, config["sfx"]["hostname"], config["sfx"]["port"]
    )
    for key, sound in sfxs.items():
        scene.sfx[key] = sc.Audio(sound["data"], sound["sample_rate"])


def cache_character(c: sc.Character, n: str, p: str) -> str:
    fname = os.path.join(
        os.environ.get("NS_CACHE_DIR", ".cache"),
        f'{n}_{base64.b64encode(f"{n};{p}".encode()).decode()[:16]}.pickle',
    )
    if not os.path.isfile(fname):
        with open(fname, "wb") as f:
            pickle.dump(c, f)
    return fname


def load_char_cache(n: str, p: str) -> Union[sc.Character, None]:
    fname = os.path.join(
        os.environ.get("NS_CACHE_DIR", ".cache"),
        f'{n}_{base64.b64encode(f"{n};{p}".encode()).decode()[:16]}.pickle',
    )
    if not os.path.isfile(fname):
        return None
    with open(fname, "rb") as f:
        return pickle.load(f)
