FROM python:3.12-slim AS system

RUN apt-get update && \
  apt-get install -y make git vim

RUN useradd -d /home/generator generator

WORKDIR /home/generator
ENV PATH="/home/generator/.local/bin:${PATH}"

FROM system AS dependencies
COPY makefiles/ makefiles/
COPY Makefile ./
COPY pyproject.toml ./
RUN make poetry/setup && \
  poetry config virtualenvs.create false

RUN make setup/server
RUN poetry shell

FROM dependencies as natural_stupidity
ARG GH_USER
ARG GH_TOKEN

RUN git clone https://${GH_USER}:${GH_TOKEN}@github.com/gbmap/ns-parser.git && \
  cd ns-parser && \
  git checkout 5e1ceff && \
  pip install . && \
  cd -

FROM natural_stupidity AS source
COPY src/ ./src/
COPY config.yaml config.yaml
RUN chown -R generator:generator ../ 
ENTRYPOINT ["uvicorn", "src.natural_stupidity.gen.server:app", "--host", "0.0.0.0", "--port", "9001"]
