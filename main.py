from src.seuranta_app import SeurantaApp
import asyncio
import uvicorn


def create_app() -> SeurantaApp:
    app = SeurantaApp()
    return app


async def main():
    config = uvicorn.Config("main:create_app",
                            host="0.0.0.0",
                            port=8000,
                            factory=True,
                            log_level="info",
                            log_config="log_conf.yaml")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
