FROM python:3.13
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN uv pip install --system --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./src /code/src
COPY ./static /code/static
COPY ./templates /code/templates
COPY ./tests /code/tests

RUN python -m pytest