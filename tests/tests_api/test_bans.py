import pytest
from httpx import AsyncClient
from app.database.repo import DataBase


async def test_correct(test_client: AsyncClient, test_db: DataBase):
    await test_db.bans.clear_table()
    await test_db.bans.new('123.4.5.6')
    await test_db.bans.new('123.4.5.7')
    await test_db.bans.new('123.4.5.8')
    await test_db.bans.new('123.4.5.9')
    await test_db.bans.new('123.4.5.0')
    await test_db.commit()

    res = await test_client.get('v1/bans')
    assert res.status_code == 200
    assert len(res.json()['bans']) == 5


async def test_pagination_small(test_client: AsyncClient, test_db: DataBase):
    res = await test_client.get('v1/bans', params={'skip': 0, 'limit': 2})
    assert res.status_code == 200
    assert len(res.json()['bans']) == 2


async def test_pagination_big(test_client: AsyncClient, test_db: DataBase):
    res = await test_client.get('v1/bans', params={'skip': 1, 'limit': 5})
    assert res.status_code == 200
    assert len(res.json()['bans']) == 4
