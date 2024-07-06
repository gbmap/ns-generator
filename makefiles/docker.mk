-include .$(PWD)/.env

docker/cache:
	docker volume create ns-generator-cache

docker/network:
	-docker network create ns

docker/build: docker/cache
	docker build --build-arg GH_USER=$(GH_USER) --build-arg GH_TOKEN=$(GH_TOKEN) -t ns-generator .

docker/run: docker/cache docker/network
	docker run -it -d -p 9001:9001 --network ns -v ns-generator-cache:/home/generator/.cache/ --name ns-generator ns-generator

docker/stop:
	docker stop ns-generator
	docker rm ns-generator

docker/rebuild: docker/stop docker/build docker/run
