from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from get_docker_secret import get_docker_secret
import os


PG_USERNAME = os.getenv("POSTGRES_USER")
PG_DBNAME = os.getenv("POSTGRES_DB")
PG_PASSWD = get_docker_secret("postgres-passwd")
DB_URL = f"postgresql+asyncpg://{PG_USERNAME}:{PG_PASSWD}@seuranta-db/{PG_DBNAME}"

engine = create_async_engine(DB_URL)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
