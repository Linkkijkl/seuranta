from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import asyncio
import uvicorn


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


def create_app() -> FastAPI:
    app = SeurantaApp()
    return app


async def main():
    config = uvicorn.Config("main:create_app", port=8000, factory=True)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())