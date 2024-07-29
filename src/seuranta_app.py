from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


class SeurantaApp(FastAPI):
    def __init__(self):
        super().__init__()
        self.templates = Jinja2Templates(directory="templates")
        self.mount("/static", StaticFiles(directory="static"), name="static")
        self.init_routes()


    def init_routes(self):
        self.add_route("/", route=self.index)


    async def index(self, req: Request) -> Response:
        return self.templates.TemplateResponse(request=req, name="index.html")