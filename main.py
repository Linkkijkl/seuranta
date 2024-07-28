from fastapi import FastAPI, Request, Response
import asyncio
import uvicorn


class SeurantaUserInterface(FastAPI):
    def __init__(self):
        super().__init__()
        self.init_routes()


    def init_routes(self):
        self.add_route("/", route=self.hello_kattila)


    async def hello_kattila(self, _: Request) -> Response:
        return Response("Hello, Kattila")


def create_app() -> FastAPI:
    app = SeurantaUserInterface()
    return app


async def main():
    config = uvicorn.Config("main:create_app", port=8000, factory=True)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())