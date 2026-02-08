import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repo import DataBase


async def test_correct(test_client: AsyncClient, test_db: DataBase):
    res = await test_client.post('/v1/bans', json={'ip': '100.4.5.9', 'reason': 'test'})
    assert res.status_code == 200
    assert res.json()['ok'] == True


async def test_wrong(test_client: AsyncClient):
    res = await test_client.post('/v1/bans', json={'ip': '123'})
    assert res.status_code == 400


async def test_already_banned(test_client: AsyncClient):
    res = await test_client.post('/v1/bans', json={'ip': '123.4.5.6'})
    assert res.status_code == 400
