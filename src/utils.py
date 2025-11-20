import re
import httpx
from jinja2 import Environment, FileSystemLoader
from fastapi.templating import Jinja2Templates
from get_docker_secret import get_docker_secret

NAME_MAXLENGTH = 20
KATTILA_API_URL = "https://kattila-api.linkkijkl.fi"

JINJA_ENV = Environment(
    loader = FileSystemLoader("templates"),
    trim_blocks = True,
)
JINJA_TEMPLATES = Jinja2Templates(env=JINJA_ENV)

#with open("apikey.txt", "r") as keyfile:
#    self.KATTILA_API_KEY = keyfile.read().strip()
_KATTILA_API_KEY = get_docker_secret("apikey")

def sanitise_name(name: str, max_length: int = NAME_MAXLENGTH) -> str:
    return re.sub(r'[^a-zA-Z0-9]', '', name)[:max_length]


async def export_names(name_data):
    headers = {"X-API-Key": _KATTILA_API_KEY}
    #json={"users": [{"username": username} for username in await self.present_names]}
    #httpx.put(f"{KATTILA_API_URL}/seuranta/users", headers=headers, json=json)