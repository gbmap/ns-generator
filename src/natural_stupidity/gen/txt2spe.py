import requests
import base64
import io

import soundfile as sf
from typing import List, Tuple

import numpy as np


def nstts_generate(
    lines: List[str], voices: List[str], url: str = "localhost", port: int = 8000
) -> Tuple[List[np.ndarray], int]:
    payload = {"character": {"lines": lines, "voice": voices}}

    response = requests.post(f"http://{url}:{port}/", json=payload)
    result = response.json()

    audios = [None] * len(lines)
    sr = 0
    for line in result["character"]:
        audio_bytes = base64.b64decode(result["character"][line])
        audio_bytes = io.BytesIO(audio_bytes)
        audio_numpy, sr = sf.read(audio_bytes)
        audios[lines.index(line)] = audio_numpy

    return audios, sr


def generate(
    lines: List[str], voices: List[str], url: str = "localhost", port: int = 8000
) -> Tuple[List[np.ndarray], int]:
    return nstts_generate(lines, voices, url, port)


def __main():
    audios, sr = generate(
        ["cartoons are drawings that move and say some stuff."], ["gilbert"]
    )
    sf.write("test.wav", audios[0], samplerate=sr)


if __name__ == "__main__":
    __main()
