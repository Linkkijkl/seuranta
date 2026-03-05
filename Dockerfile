FROM python:3.13-alpine
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /

RUN --mount=type=bind,source=requirements.txt,target=/tmp/requirements.txt \
    uv pip install --system --no-cache-dir --upgrade -r /tmp/requirements.txt

COPY ./src /src
COPY ./static /static
COPY ./templates /templates

ENTRYPOINT ["fastapi", "run", "--entrypoint", "src.main:app", "--proxy-headers", "--port", "8000", "--host", "0.0.0.0"]