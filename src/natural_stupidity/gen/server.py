import base64
import os
import glob
import shutil
from fastapi import FastAPI, Request, Response
from natural_stupidity import parser, scene as sc

from .generator import generate_scene_resources

app = FastAPI()


@app.post("/")
async def main(request: Request):
    data = (await request.body()).decode()
    scene, commands = parser.parse(data)
    generate_scene_resources(scene, commands)
    response_data = sc.cache_scene(scene, commands)
    return Response(content=response_data)


@app.post("/ui/select_variant")
async def cache_character(name: str, prompt: str, option: int):
    cache_dir = os.environ.get("NS_CACHE_DIR", ".cache")

    target_fname = os.path.join(
        os.environ.get("NS_CACHE_DIR", ".cache"),
        f'{name}_{base64.b64encode(f"{name};{prompt}".encode()).decode()[:16]}.pickle',
    )

    src_fname = glob.glob(os.path.join(cache_dir, f"{name}_{option}*"))[0]
    shutil.copy(src_fname, target_fname)
