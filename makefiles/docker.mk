-include .$(PWD)/.env

ifeq ($(DOCKER_IMAGE_TAG),)
	DOCKER_IMAGE_TAG := latest
endif

DOCKER_IMAGE_NAME := ns-generator

docker/cache:
	docker volume create ns-generator-cache

docker/network:
	-docker network create ns

docker/build:
	docker build --build-arg GH_USER=$(GH_USER) --build-arg GH_TOKEN=$(GH_TOKEN) -t $(DOCKER_IMAGE_NAME) .
	docker image tag $(DOCKER_IMAGE_NAME):latest ghcr.io/gbmap/$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)

docker/run: docker/cache docker/network
	docker run -it -d -p 9001:9001 --network ns -v ns-generator-cache:/home/generator/.cache/ --name $(DOCKER_IMAGE_NAME) $(DOCKER_IMAGE_NAME)

docker/stop:
	docker stop $(DOCKER_IMAGE_NAME)
	docker rm $(DOCKER_IMAGE_NAME)

docker/rebuild: docker/stop docker/build docker/run


docker/push:
	docker image tag $(DOCKER_IMAGE_NAME):latest ghcr.io/gbmap/$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)
	docker login ghcr.io -u $(GH_USER) -p $(GH_TOKEN)
	docker push ghcr.io/gbmap/$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)
