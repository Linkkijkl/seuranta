from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler # type: ignore
from apscheduler.triggers.cron import CronTrigger # type: ignore
from contextlib import asynccontextmanager
import logging
import aiohttp
import datetime
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select


class TrackedEntity(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_date: str
    devices: list["Device"] = Relationship(back_populates="trackedentity", cascade_delete=True)


class TrackedEntityCreate(SQLModel):
    name: str


class DeviceBase(SQLModel):
    name: str = Field(index=True)
    mac: str = Field(index=True, unique=True)


class Device(DeviceBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    trackedentity_id: int = Field(index=True, foreign_key="trackedentity.id", ondelete="CASCADE")
    trackedentity: TrackedEntity = Relationship(back_populates="devices")


def get_db_engine():
    SQLITE_FILE = "seuranta.db"
    SQLITE_URL = f"sqlite:///{SQLITE_FILE}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(SQLITE_URL, connect_args=connect_args)
    return engine


class SeurantaApp(FastAPI):
    def __init__(self, use_lease_monitor: bool=True):
        self.use_lease_monitor=use_lease_monitor
        self.clients = []
        self.engine = get_db_engine()
        super().__init__(lifespan=SeurantaApp.lifespan)
        self.logger = logging.getLogger(__name__)
        self.templates = Jinja2Templates(directory="templates")
        self.mount("/static", StaticFiles(directory="static"), name="static")
        self.LEASES_URL = 'http://192.168.1.1/moi'


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
                    self.clients = await self.parse_leases(response_text)
                return response.status


    @staticmethod
    async def parse_leases(lease_lines: str) -> list[tuple[str, str, str]]:
        clients = []
        filtered_lines: list[str] = [line for line in lease_lines.split("\n") if line]
        for line in filtered_lines:
            (_, mac, ip, hostname, _) = line.split()
            clients.append((mac,ip,hostname)) # type: ignore
        return clients # type: ignore


    async def init_routes(self):
        self.add_api_route("/", endpoint=self.index)
        self.add_api_route("/tracked", methods=["get"], endpoint=self.get_tracked, response_model=list[TrackedEntity])
        self.add_api_route("/tracked", methods=["post"], endpoint=self.create_tracked, response_model=TrackedEntity)


    async def index(self, req: Request) -> Response:
        return self.templates.TemplateResponse(request=req, name="index.html")


    async def get_tracked(self, req: Request):
        with Session(self.engine) as session:
            tracked = session.exec(select(TrackedEntity)).all()
            return tracked


    async def create_tracked(self, req: Request, tracked: TrackedEntityCreate):
        req_host = req.client.host
        req_mac = None
        for mac, ip, hostname in self.clients:
            if req_host == hostname:
                req_mac = mac

        with Session(self.engine) as session:
            timestamp = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0).isoformat()
            extra_data = {"created_date": timestamp}
            db_tracked = TrackedEntity.model_validate(tracked, update=extra_data)
            session.add(db_tracked)
            session.commit()
            session.refresh(db_tracked)
            if req_mac:
                db_device = Device(name=hostname, mac=req_mac, trackedentity_id=db_tracked.id)
                session.add(db_device)
                session.commit()
                session.refresh(db_device)
            return db_tracked
