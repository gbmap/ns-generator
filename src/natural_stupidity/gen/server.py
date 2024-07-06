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
