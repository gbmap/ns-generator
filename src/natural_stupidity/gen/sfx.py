import base64
import io
from typing import Any
import requests
import soundfile as sf


def generate(
    prompts: list[str], durations: list[float], hostname: str, port: int
) -> dict[str, dict[str, Any]]:
    url = f"http://{hostname}:{port}/sfx"
    response = requests.post(url, json={"prompts": prompts, "durations": durations})
    data = response.json()
    print(data)

    for k, v in data.items():
        print(k)
        print(v)
        sound_data = base64.b64decode(v)
        array, sr = sf.read(io.BytesIO(sound_data))
        data[k] = {"data": array, "sample_rate": sr}
    return data
