import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repo import DataBase


async def test_correct(test_client: AsyncClient, test_db: DataBase):
    await test_db.bans.new(ip='321.4.5.6', reason='test')
    await test_db.commit()
    res = await test_client.get('/v1/bans/321.4.5.6')
    assert res.status_code == 200
    assert res.json()['ok'] == True
    await test_db.bans.delete_by_ip('321.4.5.6')
    await test_db.commit()


async def test_not_exists(test_client: AsyncClient, test_db: DataBase):
    res = await test_client.get('/v1/bans/123.5.5.5')
    assert res.status_code == 200
    assert res.json()['ok'] == False


async def test_in_wrong(test_client: AsyncClient):
    res = await test_client.get('/v1/bans/123')
    assert res.status_code == 400
    assert res.json()['detail'] == 'Invalid IP address'
