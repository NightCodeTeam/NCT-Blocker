import pytest

from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fastapi import Request

from core.redis_client import get_redis
from app.database.database import Base
from app.database.repo import DataBase
from app.depends.db import get_db
from app.__main__ import app
from app.settings import settings


engine = create_async_engine(
    url="sqlite+aiosqlite:///:memory:",
    echo=True,
    pool_pre_ping=True,
)
test_session = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_test_db() -> AsyncGenerator[DataBase]:
    async with test_session() as session:
        yield DataBase(session)


@pytest.fixture(scope='function')
async def test_db() -> AsyncGenerator[DataBase]:
    async with test_session() as session:
        yield DataBase(session)


async def test_redis_client(request: Request):
    class RedisClientMock:
        def __init__(self, *args, **kwargs):
            pass

        async def get(self, *args, **kwargs):
            return None

        async def set(self, *args, **kwargs):
            pass

        async def get_dict(self, *args, **kwargs):
            return {}

        async def set_dict(self, *args, **kwargs):
            pass

        async def delete(self, *args, **kwargs):
            pass

        async def set_json(self, *args, **kwargs):
            pass

        async def get_json(self, *args, **kwargs):
            pass
    yield RedisClientMock()




@pytest.fixture(scope='module')
async def test_client() -> AsyncGenerator[AsyncClient]:
    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[get_redis] = test_redis_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
        app.dependency_overrides.clear()


@pytest.fixture(scope='session', autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
