from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler # type: ignore
from apscheduler.triggers.cron import CronTrigger # type: ignore
from contextlib import asynccontextmanager
import logging
import aiohttp


class SeurantaApp(FastAPI):
    def __init__(self, use_lease_monitor: bool=True):
        self.use_lease_monitor=use_lease_monitor
        super().__init__(lifespan=SeurantaApp.lifespan)
        self.logger = logging.getLogger(__name__)
        self.templates = Jinja2Templates(directory="templates")
        self.mount("/static", StaticFiles(directory="static"), name="static")
        self.LEASES_URL = 'http://192.168.1.1/moi'


    @asynccontextmanager
    async def lifespan(self):
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
                return response.status


    async def init_routes(self):
        self.add_route("/", route=self.index)


    async def index(self, req: Request) -> Response:
        return self.templates.TemplateResponse(request=req, name="index.html")
