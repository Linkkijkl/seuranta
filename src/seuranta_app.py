from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler # type: ignore
from apscheduler.triggers.cron import CronTrigger # type: ignore
from contextlib import asynccontextmanager
import logging


class SeurantaApp(FastAPI):
    def __init__(self):
        super().__init__(lifespan=SeurantaApp.lifespan)
        self.logger = logging.getLogger(__name__)
        self.templates = Jinja2Templates(directory="templates")
        self.mount("/static", StaticFiles(directory="static"), name="static")


    @asynccontextmanager
    async def lifespan(self):
        await self.init_routes()
        yield


    async def init_routes(self):
        self.add_route("/", route=self.index)


    async def index(self, req: Request) -> Response:
        return self.templates.TemplateResponse(request=req, name="index.html")