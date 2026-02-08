import pytest
from httpx import AsyncClient
from app.database.repo import DataBase


async def test_correct(test_client: AsyncClient, test_db: DataBase):
    await test_db.bans.new(ip='123.4.5.6', reason='test', commit=True)
    res = await test_client.delete('v1/bans/123.4.5.6')
    assert res.json()['ok'] == True
