import re
import httpx
from jinja2 import Environment, FileSystemLoader
from fastapi.templating import Jinja2Templates
from get_docker_secret import get_docker_secret
import os

NAME_MAXLENGTH = 20

JINJA_ENV = Environment(
    loader = FileSystemLoader("templates"),
    trim_blocks = True,
)
JINJA_TEMPLATES = Jinja2Templates(env=JINJA_ENV)

KATTILA_API_URL = os.getenv("KATTILA_API_URL", None)
_KATTILA_API_KEY = get_docker_secret("apikey")

def sanitise_name(name: str, max_length: int = NAME_MAXLENGTH) -> str:
    return re.sub(r'[^a-zA-Z0-9]', '', name)[:max_length]


async def export_names(names: list[str]):
    if KATTILA_API_URL:
        headers = {"X-API-Key": _KATTILA_API_KEY}
        json={"users": [{"username": name} for name in names]}
        httpx.put(f"{KATTILA_API_URL}/seuranta/users", headers=headers, json=json)