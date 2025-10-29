import pytest
from sqlalchemy.orm import sessionmaker
from src.main import app, lease_monitor, get_session
import src.models as models
from src.lease_monitor import Lease

# async dependencies
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# sync dependencies
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture
def mock_leases():
    mock_leases = [Lease("192.168.1.100","test-hostname-1","1a:2b:3c:4d:5e:6f"),
                    Lease("192.168.1.101","test-hostname-2","6f:5e:4d:3c:2b:1a"),
                    Lease("127.0.0.1","test-hostname-3","11:aa:22:bb:33:cc")] # This IP is from where AsyncClient makes requests
    return mock_leases

@pytest_asyncio.fixture()
async def async_session():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestSessionLocal = sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with test_engine.begin() as connection:
        await connection.run_sync(models.Base.metadata.create_all)

    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()

@pytest_asyncio.fixture
async def async_client(monkeypatch, async_session, mock_leases):
    def get_session_override():
        return async_session

    monkeypatch.setattr(lease_monitor, "_leases", mock_leases)
    monkeypatch.setattr(lease_monitor, "fetch_leases", 200)
    app.dependency_overrides[get_session] = get_session_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def client():
    def get_session_override():
        raise Exception("If the test needs a database connection, use asyc_client fixture")
    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)