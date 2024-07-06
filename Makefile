-include .$(PWD)/.env
include ./makefiles/docker.mk
include ./makefiles/setup.mk

server:
	uvicorn src.natural_stupidity.gen.server:app --host 0.0.0.0 --port 9001

