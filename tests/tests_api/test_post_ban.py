import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.repo import DataBase


async def test_correct(test_client: AsyncClient):
    res = await test_client.post(f'/v1/bans/100.4.5.9', json={'reason': 'test'})
    assert res.status_code == 200
    assert res.json()['ok'] == True


async def test_wrong(test_client: AsyncClient):
    res = await test_client.post('/v1/bans/123')
    assert res.status_code == 400
