from fastapi import FastAPI, Depends, Request, Response, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from typing import Annotated
from jinja2 import Environment, FileSystemLoader
from .utils import sanitise_name, export_names
from .lease_monitor import Lease, LeaseMonitor

JINJA_ENV = Environment(
    loader = FileSystemLoader("templates"),
    trim_blocks = True,
)
JINJA_TEMPLATES = Jinja2Templates(env=_JINJA_ENV)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

lease_monitor = LeaseMonitor('http://192.168.1.1/moi', export_names)

@app.get("/")
async def root(req: Request) -> Response:
    context: dict[str, Any] = {"present_names": await self.present_names}
    if req.client and (lease := await self._lease_monitor.get_lease_by_ip(req.client.host)):
        if device := get_db_device(lease, next(get_session())):
            context["tracked"] = device.trackedentity
    return JINJA_TEMPLATES.TemplateResponse(request=req, name="index.html", context=context)


@app.get("/name-form")
async def serve_name_form():
    return {}


@app.post("/name-form")
async def handle_name_form(req: Request, name_form_data: Annotated[str, Form()]):
    assert req.client
    ip = req.client.host
    name = await utils.sanitise_name(name_form_data)
    if lease := await self._lease_monitor.get_lease_by_ip(ip):
        if device := get_db_device(lease, session):
            tracked = session.get(TrackedEntity, device.trackedentity_id)
            assert tracked
            tracked.name = name
            session.add(tracked)
            session.commit()
    await self.create_tracked(req, TrackedEntityCreate(name=name), session=session)
    return RedirectResponse("/", status_code=302)