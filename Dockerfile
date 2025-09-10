FROM python:3.13
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN uv pip install --system --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/src

CMD ["fastapi", "run", "src/main.py", "--proxy-headers", "--port", "8000", "--host", "0.0.0.0"]