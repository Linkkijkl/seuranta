FROM python:3.13
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /

COPY ./requirements.txt /requirements.txt

RUN uv pip install --system --no-cache-dir --upgrade -r /requirements.txt

COPY ./src /src
COPY ./static /static
COPY ./templates /templates
COPY ./seuranta.db /seuranta.db

CMD ["fastapi", "run", "src/main.py", "--proxy-headers", "--port", "8000", "--host", "0.0.0.0"]