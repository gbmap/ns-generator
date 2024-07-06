from typing import Any
import requests
import pickle


def generate(script: str, hostname: str, port: int) -> dict[str, Any]:
    response = requests.post(f"http://{hostname}:{port}/", data=script)
    return pickle.loads(response.content)
