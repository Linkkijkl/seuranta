from typing import Any, Annotated
from pathlib import Path
from fastapi import Depends, FastAPI, Request, Response, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Session, select, col
import logging
import datetime
import aiofiles
import re
from .db import *
from .lease_monitor import Lease, LeaseMonitor


_NAME_MAXLENGTH = 20


class SeurantaApp(FastAPI):
    def __init__(self, **kwargs: dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.__dict__.update(kwargs)
        self.engine = get_db_engine()
        super().__init__(lifespan=SeurantaApp.lifespan)
        self.templates = Jinja2Templates(directory="templates")
        self.mount("/static", StaticFiles(directory="static"), name="static")
        self.EXPORT_DIR = Path("exports")
        self.NAMES_TXT = Path("names.txt")
        self.EXPORT_FILENAMES = {self.NAMES_TXT}


    @asynccontextmanager
    async def lifespan(self):
        SQLModel.metadata.create_all(self.engine)
        await self.init_export_paths()
        self._lease_monitor: LeaseMonitor = LeaseMonitor('http://192.168.1.1/moi', self.export_names)
        await self.init_routes()
        yield


    @property
    def leases(self) -> list[Lease]:
        return self._lease_monitor.leases


    @property
    async def online_ips(self) -> list[str]:
        return [lease.ipv4_addr for lease in self.leases]


    @property
    async def online_macs(self) -> list[str]:
        return [lease.mac_addr for lease in self.leases]


    @property
    async def online_entity_ids(self) -> list[int]:
        session = next(get_session())
        select_entity_id_by_mac = select(Device.trackedentity_id).where(col(Device.mac).in_(await self.online_macs))
        return list(session.exec(select_entity_id_by_mac).all())


    @property
    async def present_names(self) -> list[str]:
        session = next(get_session())
        select_name_by_online_ids = select(TrackedEntity.name).where(col(TrackedEntity.id).in_(await self.online_entity_ids))
        return list(session.exec(select_name_by_online_ids).all())


    async def export_names(self):
        names_path = self.EXPORT_DIR/self.NAMES_TXT
        self.logger.debug(f"Exporting names to {names_path}")
        async with aiofiles.open(names_path, "w") as export:
            await export.writelines("\n".join(await self.present_names))
            await export.flush()


    async def init_export_paths(self):
        if not self.EXPORT_DIR.is_dir():
            self.logger.info(f"Creating {self.EXPORT_DIR} directory")
            self.EXPORT_DIR.mkdir()
        for filename in self.EXPORT_FILENAMES:
            if (filepath := self.EXPORT_DIR/filename).exists():
                continue
            self.logger.info(f"Creating {filepath}")
            filepath.touch()


    async def init_routes(self):
        self.add_api_route("/", endpoint=self.index)
        self.add_api_route("/name-form", methods=["get"], endpoint=self.name_form_page) # type: ignore
        self.add_api_route("/name-form", methods=["post"], endpoint=self.handle_name_form, response_model=TrackedEntityPublicWithDevices) # type: ignore
        self.add_api_route("/trackeds", methods=["get"], endpoint=self.get_trackeds, response_model=list[TrackedEntityPublic]) # type: ignore
        self.add_api_route("/tracked", methods=["post"], endpoint=self.create_tracked, response_model=TrackedEntityPublicWithDevices) # type: ignore
        self.add_api_route("/tracked/{tracked_id}", methods=["get"], endpoint=self.get_tracked, response_model=TrackedEntityPublicWithDevices) # type: ignore


    async def index(self, req: Request) -> Response:
        return self.templates.TemplateResponse(request=req, name="index.html", context={"present_names": await self.present_names})


    async def name_form_page(self, req: Request) -> Response:
        return self.templates.TemplateResponse(request=req, name="name-form.html", context={"name_maxlength": _NAME_MAXLENGTH})

    @staticmethod
    async def sanitise_name(name: str) -> str:
        return re.sub(r'[^a-zA-Z0-9]', '', name)[:_NAME_MAXLENGTH]


    async def handle_name_form(self, req: Request, name: Annotated[str, Form()], session: Session = Depends(get_session)):
        assert req.client
        ip = req.client.host
        name = await self.sanitise_name(name)
        self.logger.info(f"Received name-form from {name}@{ip}")
        if lease := await self._lease_monitor.get_lease_by_ip(ip):
            if device := get_db_device(lease, session):
                self.logger.info(f"Request is associated with an existing device in the database, {device.mac}")
        response = await self.create_tracked(req, TrackedEntityCreate(name=name), session=session)
        return response


    async def get_trackeds(self, session: Session = Depends(get_session)) -> list[TrackedEntity]:
        trackeds: list[TrackedEntity] = list(session.exec(select(TrackedEntity)).all())
        return trackeds


    async def get_tracked(self, tracked_id: int, session: Session = Depends(get_session)):
        tracked = session.get(TrackedEntity, tracked_id)
        if not tracked:
            raise HTTPException(status_code=404, detail="TrackedEntity not found")
        return tracked


    async def create_tracked(self, req: Request, tracked: TrackedEntityCreate, session: Session = Depends(get_session)):
        assert req.client
        self.logger.info(f"Creating tracked entity {tracked.name}")
        self.logger.info(f"Creation request is coming from {req.client.host}")
        request_ip = req.client.host
        request_lease: Lease | None = None
        if request_leases := [lease for lease in self.leases if lease.ipv4_addr == request_ip]:
            request_lease = request_leases.pop()
            self.logger.info(f"Creation request is associated with mac: {request_lease.mac_addr}")
        else:
            self.logger.info(f"Creating tracked entity {tracked.name} with no association to any devices")
        name_exists = session.exec(select(TrackedEntity).where(TrackedEntity.name == tracked.name)).first()
        if not name_exists:
            timestamp = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0).isoformat()
            extra_data = {"created_date": timestamp}
            db_tracked = TrackedEntity.model_validate(tracked, update=extra_data)
            session.add(db_tracked)
            session.commit()
            session.refresh(db_tracked)
        else:
            db_tracked = name_exists
        if request_lease:
            device_exists = session.exec(select(Device).where(Device.mac == request_lease.mac_addr)).first()
            assert db_tracked.id
            if device_exists:
                device_exists.trackedentity_id = db_tracked.id
                session.add(device_exists)
                session.commit()
                session.refresh(device_exists)
            else:
                db_device = DeviceCreate(name=request_lease.hostname, mac=request_lease.mac_addr, trackedentity_id=db_tracked.id)
                db_device = Device.model_validate(db_device)
                session.add(db_device)
                session.commit()
                session.refresh(db_device)
        return db_tracked
