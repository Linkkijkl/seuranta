from fastapi import Depends, FastAPI, Request, Response, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler # type: ignore
from apscheduler.triggers.cron import CronTrigger # type: ignore
from contextlib import asynccontextmanager
import logging
import aiohttp
import datetime
import aiofiles
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select, col, Sequence # type: ignore


class TrackedEntityBase(SQLModel):
    name: str = Field(index=True, unique=True)


class TrackedEntity(TrackedEntityBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    devices: list["Device"] = Relationship(back_populates="trackedentity", cascade_delete=True)
    created_date: str


class TrackedEntityCreate(TrackedEntityBase):
    pass


class TrackedEntityPublic(TrackedEntityBase):
    id: int
    created_date: str


class DeviceBase(SQLModel):
    name: str = Field(index=True)
    mac: str = Field(index=True, unique=True)
    trackedentity_id: int = Field(index=True, foreign_key="trackedentity.id", ondelete="CASCADE")


class Device(DeviceBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    trackedentity: TrackedEntity | None = Relationship(back_populates="devices")


class DeviceCreate(DeviceBase):
    pass


class DevicePublic(DeviceBase):
    id: int


class TrackedEntityPublicWithDevices(TrackedEntityPublic):
    devices: list[DevicePublic]


class DevicePublicWithTrackedEntity(DevicePublic):
    trackedentity: TrackedEntityPublic | None = None


def get_db_engine():
    SQLITE_FILE = "seuranta.db"
    SQLITE_URL = f"sqlite:///{SQLITE_FILE}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(SQLITE_URL, connect_args=connect_args)
    return engine

def get_session():
    with Session(get_db_engine()) as session:
        yield session


class Lease():
    def __init__(self, ip: str, hostname: str, mac: str):
        self.ip: str = ip
        self.hostname: str = hostname
        self.mac: str = mac


    def __eq__(self, other: object) -> bool:
        return self.__dict__ == other.__dict__


class SeurantaApp(FastAPI):
    def __init__(self, use_lease_monitor: bool=True):
        self.use_lease_monitor=use_lease_monitor
        self.active_leases: list[Lease] = []
        self.present_names: list[str] = []
        self.engine = get_db_engine()
        super().__init__(lifespan=SeurantaApp.lifespan)
        self.logger = logging.getLogger(__name__)
        self.templates = Jinja2Templates(directory="templates")
        self.mount("/static", StaticFiles(directory="static"), name="static")
        self.LEASES_URL = 'http://192.168.1.1/moi'
        self.EXPORT_FILEPATH = "exports/names.txt"


    @asynccontextmanager
    async def lifespan(self):
        SQLModel.metadata.create_all(self.engine)

        if self.use_lease_monitor:
            await self.init_lease_monitor()
        await self.init_routes()
        yield


    async def init_lease_monitor(self):
        self.logger.info("Initialising lease monitor")
        lease_status = await self.fetch_leases()
        if lease_status < 400:
            lease_monitor = AsyncIOScheduler()
            lease_monitor.add_job(self.fetch_leases, CronTrigger(second="*/15")) # type: ignore
            lease_monitor.start()
            self.logger.info("Started DHCP lease monitor")
        else:
            self.logger.error("Didn't form connection with DHCP server, therefore not starting lease monitor")


    async def fetch_leases(self) -> int:
        timeout = aiohttp.ClientTimeout(total=10, connect=5)
        self.logger.info("Fetching DHCP leases")
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(self.LEASES_URL) as response:
                self.logger.info(f"DHCP lease response status: {response.status}")
                if response.status < 400:
                    response_text = await response.text()
                    self.active_leases = await self.parse_leases(response_text)
                    await self.update_present_names()
                    await self.export_present_names()
                return response.status


    @staticmethod
    async def parse_leases(leases_str: str) -> list[Lease]:
        leases: list[Lease] = []
        lease_lines: list[str] = [line for line in leases_str.split("\n") if line]
        for line in lease_lines:
            (_, mac, ip, hostname, _) = line.split()
            leases.append(Lease(ip=ip, hostname=hostname, mac=mac))
        return leases


    async def update_present_names(self):
        session = next(get_session())
        online_macs = [lease.mac for lease in self.active_leases]
        online_entity_ids = session.exec(select(Device.trackedentity_id).where(Device.mac.in_(online_macs))).all()
        self.present_names = session.exec(select(TrackedEntity.name).where(TrackedEntity.id.in_(online_entity_ids))).all()


    async def export_present_names(self):
        async with aiofiles.open(self.EXPORT_FILEPATH, "w") as export:
            await export.writelines(self.present_names)
            await export.flush()


    async def init_routes(self):
        self.add_api_route("/", endpoint=self.index)
        self.add_api_route("/trackeds", methods=["get"], endpoint=self.get_trackeds, response_model=list[TrackedEntityPublic])
        self.add_api_route("/tracked", methods=["post"], endpoint=self.create_tracked, response_model=TrackedEntityPublicWithDevices)
        self.add_api_route("/tracked/{tracked_id}", methods=["get"], endpoint=self.get_tracked, response_model=TrackedEntityPublicWithDevices)


    async def index(self, req: Request) -> Response:
        return self.templates.TemplateResponse(request=req, name="index.html", context={"present_names": self.present_names})


    async def get_trackeds(self, session: Session = Depends(get_session)):
        trackeds = session.exec(select(TrackedEntity)).all()
        return trackeds


    async def get_tracked(self, tracked_id: int, session: Session = Depends(get_session)):
        tracked = session.get(TrackedEntity, tracked_id)
        if not tracked:
            raise HTTPException(status_code=404, detail="TrackedEntity not found")
        return tracked


    async def create_tracked(self, req: Request, tracked: TrackedEntityCreate, session: Session = Depends(get_session)):
        self.logger.info(f"Creating tracked entity {tracked.name}")
        self.logger.info(f"Creation request is coming from {req.client.host}")
        request_ip = req.client.host
        request_lease = next(iter([lease for lease in self.active_leases if lease.ip == request_ip]))
        if request_lease:
            self.logger.debug(f"Creation request is associated with mac: {request_lease.mac}")
        else:
            self.logger.warn(f"Creating tracked entity {tracked.name} with no association to any devices")
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
            device_exists = session.exec(select(Device).where(Device.mac == request_lease.mac)).first()
            if device_exists:
                device_exists.trackedentity_id = db_tracked.id
                session.add(device_exists)
                session.commit()
                session.refresh(device_exists)
            else:
                db_device = DeviceCreate(name=request_lease.hostname, mac=request_lease.mac, trackedentity_id=db_tracked.id)
                db_device = Device.model_validate(db_device)
                session.add(db_device)
                session.commit()
                session.refresh(db_device)
        return db_tracked
