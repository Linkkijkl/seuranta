from typing import Annotated, Any

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
from src.lease_monitor import LeaseMonitor


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

async def associate_tracked_entity_data(req: Request, session: SessionDep):
    req.state.lease = await lease_monitor.get_lease_by_ip(req.client.host)
    req.state.device = None
    req.state.tracked_entity = None

    if req.state.lease:
        req.state.device = await crud.get_device_by_mac_addr(session, req.state.lease.mac_addr)
        if req.state.device:
            req.state.tracked_entity = await session.get_one(models.TrackedEntity, req.state.device.tracked_entity_id)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(models.Base.metadata.create_all)
    lease_monitor_scheduler.start()
    await lease_monitor.update_leases()
    yield
    lease_monitor_scheduler.shutdown()

app = FastAPI(lifespan=lifespan, dependencies=[Depends(associate_tracked_entity_data)])

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root(req: Request, session: SessionDep) -> Response:
    context: dict[str, Any] = {}
    context["present_names"] = await crud.get_tracked_entity_names_by_mac_addrs(session, lease_monitor.mac_addrs)
    if te := req.state.tracked_entity:
        context["tracked_entity"] = te
        await te.awaitable_attrs.devices
        return JINJA_TEMPLATES.TemplateResponse(request=req, name="informative.html", context=context)
    return JINJA_TEMPLATES.TemplateResponse(request=req, name="index.html", context=context)

@app.get("/name-form")
async def serve_name_form(req: Request, session: SessionDep):
    context: dict[str, Any] = {"name_maxlength": NAME_MAXLENGTH}
    context["tracked_entity"] = req.state.tracked_entity
    return JINJA_TEMPLATES.TemplateResponse(request=req, name="name-form.html", context=context)

@app.post("/name-form")
async def handle_name_form(req: Request, username: Annotated[str, Form()], session: SessionDep):
    if not req.state.lease:
        return Response(content="Could not find associated DHCP lease", status_code=500)

    # Device is associated with an existing tracked entity, so 
    if te := req.state.tracked_entity:
        await crud.update_tracked_entity_name(session, te, username)
        return RedirectResponse("/", status_code=302)
    
    new_device = schemas.DeviceCreate(mac_addr=req.state.lease.mac_addr, hostname=req.state.lease.hostname)
    
    if te := crud.get_tracked_entity_by_name(username):
        await crud.add_device_to_tracked_entity(session, te, new_device)
        return RedirectResponse("/", status_code=302)
    
    new_tracked_entity = schemas.TrackedEntityCreate(name=username)

    await crud.create_tracked_entity_with_device(session, new_tracked_entity, new_device)
    return RedirectResponse("/", status_code=302)

@app.post("/memberships")
async def add_membership(req: Request, membership: schemas.MembershipCreate, session: SessionDep):
    if te := req.state.tracked_entity \
    and te.tracked_entity_id == membership.tracked_entity_id:
        await crud.add_membership(session, membership)

@app.delete("/memberships")
async def delete_membership(req: Request, membership: schemas.MembershipDelete, session: SessionDep):
    if te := req.state.tracked_entity \
    and te.tracked_entity_id == membership.tracked_entity_id:
        await crud.delete_membership(session, membership)
