from typing import Annotated

from fastapi import (
    FastAPI,
    Depends,
    Request,
    Response,
    Form,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils import NAME_MAXLENGTH, JINJA_TEMPLATES
import src.models as models
import src.schemas as schemas
import src.crud as crud
from src.database import SessionLocal, engine
from src.lease_monitor import Lease, LeaseMonitor


lease_monitor = LeaseMonitor()

lease_monitor_scheduler = AsyncIOScheduler()
lease_monitor_scheduler.add_job(lease_monitor.update_leases, CronTrigger(second="*/15"))


async def get_session():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

SessionDep = Annotated[AsyncSession, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(models.Base.metadata.create_all)
    lease_monitor_scheduler.start()
    await lease_monitor.update_leases()
    yield
    lease_monitor_scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

async def associate_tracked_entity(req: Request, session: AsyncSession, lm: LeaseMonitor) -> None | models.TrackedEntity:
    if (lease := await lm.get_lease_by_ip(req.client.host)) \
    and (device := await crud.get_device_by_mac_addr(session, lease.mac_addr)):
        return await session.get_one(models.TrackedEntity, device.tracked_entity_id)

@app.get("/")
async def root(req: Request, session: SessionDep) -> Response:
    context: dict[str, Any] = {}
    context["present_names"] = await crud.get_tracked_entity_names_by_mac_addrs(session, lease_monitor.mac_addrs)
    if (tracked_entity := await associate_tracked_entity(req, session, lease_monitor)):
        context["tracked_entity"] = tracked_entity
        await tracked_entity.awaitable_attrs.devices
    return JINJA_TEMPLATES.TemplateResponse(request=req, name="index.html", context=context)

@app.get("/name-form")
async def serve_name_form(req: Request):
    return JINJA_TEMPLATES.TemplateResponse(request=req, name="name-form.html", context={"name_maxlength": NAME_MAXLENGTH})

@app.post("/name-form")
async def handle_name_form(req: Request, username: Annotated[str, Form()], session: SessionDep):
    if not (associated_lease := await lease_monitor.get_lease_by_ip(req.client.host)):
        return Response(content="Could not find associated DHCP lease", status_code=500)
    
    if associated_device := await crud.get_device_by_mac_addr(session, associated_lease.mac_addr):
        associated_tracked_entity = await session.get_one(models.TrackedEntity, associated_device.tracked_entity_id)
        await crud.update_tracked_entity_name(session, associated_tracked_entity, username)
        return RedirectResponse("/", status_code=302)
    
    new_tracked_entity = schemas.TrackedEntityCreate(name=username)
    new_device = schemas.DeviceCreate(mac_addr=associated_lease.mac_addr)
    await crud.create_tracked_entity_with_device(session, new_tracked_entity, new_device)
    return RedirectResponse("/", status_code=302)