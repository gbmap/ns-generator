from dataclasses import dataclass
from typing import List, Tuple, Iterable, Optional
import io
import base64
import random

import requests

import numpy as np
import PIL.Image


@dataclass
class Txt2ImgResult:
    prompt: str
    imgs: Optional[Iterable[PIL.Image.Image]]
    seed: Optional[int]
    subseed_strength: Optional[float]
    sampler_index: Optional[str]


def pil_to_base64(pil_image):
    with io.BytesIO() as stream:
        pil_image.save(stream, "PNG", pnginfo=None)
        base64_str = str(base64.b64encode(stream.getvalue()), "utf-8")
        return "data:image/png;base64," + base64_str


def base64_to_pil(str_base64):
    return PIL.Image.open(io.BytesIO(base64.b64decode(str_base64)))


def sdui_response_to_pil(response) -> List[PIL.Image.Image]:
    return [
        PIL.Image.open(io.BytesIO(base64.b64decode(img_response.split(",", 1)[0])))
        for img_response in response.json()["images"]
    ]


def sdui_txt2img(
    prompt: str, resolution: Tuple[int, int], ip: str, port: int, **kwargs
) -> Txt2ImgResult:
    payload = {
        "prompt": f"a cartoon of {prompt} <hypernet:superjail:0.85> <hypernet:as:0.25>",
        "steps": 20,
        "width": resolution[0],
        "height": resolution[1],
        "sampler_index": kwargs.get("sampler_index", "Euler a"),
        "seed": kwargs.get("seed", random.randint(0, 999999)),
        "subseed_strength": kwargs.get("subseed_strength", 0.001),
        "batch_size": kwargs.get("batch_size", 4),
    }
    response = requests.post(f"http://{ip}:{port}/sdapi/v1/txt2img", json=payload)

    assert response.status_code == 200, f"{response.status_code} {response.reason}"

    return Txt2ImgResult(
        imgs=sdui_response_to_pil(response),
        prompt=payload["prompt"],
        seed=payload["seed"],
        subseed_strength=payload["subseed_strength"],
        sampler_index=payload["sampler_index"],
    )


def generate_frames(
    prompts: list[str],
    resolution: Tuple[int, int] = (480, 264),
    ip: str = "localhost",
    port: int = 7860,
    **kwargs,
) -> list[Txt2ImgResult]:
    return [sdui_txt2img(prompt, resolution, ip, port, **kwargs) for prompt in prompts]


def sdui_upscale(
    imgs: List[PIL.Image.Image], scale: int, ip: str, port: int
) -> PIL.Image.Image:
    image_list = [{"data": pil_to_base64(img), "name": i} for i, img in enumerate(imgs)]
    payload = {
        "resize_mode": 0,
        "upscaler_1": "R-ESRGAN 4x+ Anime6B",
        "upscaling_resize": scale,
        "imageList": image_list,
    }
    response = requests.post(
        f"http://{ip}:{port}/sdapi/v1/extra-batch-images", json=payload
    )
    return sdui_response_to_pil(response)


def upscale(
    imgs: List[PIL.Image.Image],
    scale: int = 4,
    hostname: str = "localhost",
    port: int = 7860,
) -> List[PIL.Image.Image]:
    return sdui_upscale(imgs, scale, hostname, port)


def gen_alpha_mask(
    imgs: List[PIL.Image.Image], ip: str = "localhost", port: int = 7860, **kwargs
) -> np.ndarray:
    """
    kwargs:
        model, List[str]: models to use. results will be averaged (default: [isnet-general-use, isnet-anime, u2net-p])
    """
    results = []
    for model in kwargs.get("model", ["isnet-general-use", "isnet-anime", "u2net-p"]):
        for img in imgs:
            response = requests.post(
                f"http://{ip}:{port}/rembg",
                json={
                    "input_image": pil_to_base64(img),
                    "model": model,
                    "return_mask": True,
                },
            )

            mask = base64_to_pil(response.json()["image"])
            results.append(mask)

    all_alpha = np.zeros_like(results[0]).astype(float)
    for img in results:
        all_alpha += np.asarray(img).copy().astype(float) / 255.0
    all_alpha /= len(results)
    all_alpha = np.sqrt(all_alpha)
    return (all_alpha * 255.0).astype(np.uint8)


def postproc_char(
    frames: List[PIL.Image.Image],
    scale: int | None = None,
    hostname: str = "localhost",
    port: int = 7860,
) -> List[PIL.Image.Image]:
    mask = PIL.Image.fromarray(gen_alpha_mask(frames))
    if scale is not None and scale > 1:
        frames = upscale(frames, scale, hostname, port)
    mask = mask.resize(frames[0].size, resample=PIL.Image.Resampling.BICUBIC)
    return [
        PIL.Image.fromarray(
            np.concatenate([np.asarray(u), np.asarray(mask)[..., np.newaxis]], axis=-1)
        )
        for u in frames
    ]
