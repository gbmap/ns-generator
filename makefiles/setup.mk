-include .$(PWD)/.env


POETRY_GROUPS_SERVER := --with server
POETRY_GROUPS_CLIENT := 

poetry/setup:
	pip install setuptools poetry

setup/server: poetry/setup
	poetry install $(POETRY_GROUPS_SERVER)

setup/client: poetry/setup
	poetry install $(POETRY_GROUPS_CLIENT)

