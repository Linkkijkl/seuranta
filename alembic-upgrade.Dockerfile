FROM python:3.13
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /

RUN --mount=type=bind,source=requirements.txt,target=/tmp/requirements.txt \
    uv pip install --system --no-cache-dir --upgrade -r /tmp/requirements.txt

COPY ./alembic.ini /alembic.ini
COPY ./src /src
COPY ./migration /migration

CMD alembic upgrade head