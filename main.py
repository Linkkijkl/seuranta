from src.seuranta_app import SeurantaApp
import asyncio
import uvicorn


def create_app() -> SeurantaApp:
    app = SeurantaApp()
    return app


async def main():
    config = uvicorn.Config("main:create_app", port=8000, factory=True)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())