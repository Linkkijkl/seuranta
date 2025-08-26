FROM python:3.13
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./ /

RUN uv pip install --system --no-cache-dir --upgrade -r requirements.txt

# See <https://fastapi.tiangolo.com/deployment/docker/#behind-a-tls-termination-proxy>
CMD ["python", "main.py"]