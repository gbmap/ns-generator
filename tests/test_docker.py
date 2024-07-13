import requests
import pickle


def call_docker():
    try:
        with open("E:/UnrealProjects/UE_NS/Scenes/scene_trucker00.yml") as f:
            data = f.read()
    except:
        with open("/mnt/e/UnrealProjects/UE_NS/Scenes/scene_trucker00.yml") as f:
            data = f.read()

    response = requests.post("http://localhost:9001/", data=data)
    scene = pickle.loads(response.content)
    print(scene)


call_docker()
