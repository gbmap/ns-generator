"""
Mouth prediction bounding box.
"""

from typing import Tuple
from PIL.Image import Image

from gradio_client import Client, file


def _sbboxpred_predict(
    img: Image, ip: str, port: int
) -> Tuple[float, float, float, float] | None:
    url = f"http://{ip}:{port}/"
    client = Client(url)

    img.save(".tmp.png")
    f = file(".tmp.png")
    outputs = client.predict(f)[1]
    if len(outputs) == 0:
        return None

    box = outputs[0]["box"]
    return [box["x1"], box["y1"], box["x2"], box["y2"]]


def predict(img: Image, ip: str, port: int) -> Tuple[float, float, float, float]:
    return _sbboxpred_predict(img, ip, port)
