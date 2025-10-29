from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


SQLITE_FILE = "seuranta.db"
SQLITE_URL = f"sqlite+aiosqlite:///{SQLITE_FILE}"

engine = create_async_engine(SQLITE_URL)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
