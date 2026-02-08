import pytest
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from core.spec_time import time_with_shift
from app.database.repo import DataBase
from app.database.models import Ban


async def test_add(test_db: DataBase):
    await test_db.bans.clear_table()
    await test_db.bans.new(
        ip='123.4.5.6',
        reason='test',
        duration_days=7,
        permanent=True,
        white=False,
        commit=True
    )
    assert await test_db.bans.exists('123.4.5.6') == True
    res = await test_db.bans.by_ip('123.4.5.6')
    assert res is not None
    assert res.reason == 'test'
    res.date_unban.replace(tzinfo=timezone.utc)
    assert res.date_unban.replace(tzinfo=timezone.utc) >= time_with_shift(6)
    assert res.permanent == True
    assert res.white == False


async def test_add_wrong_ip(test_db: DataBase):
    await test_db.bans.new('123.4.5', 'test')
    await test_db.flush()
    assert await test_db.bans.exists('123.4.5') == False
    await test_db.rollback()


async def test_auto_reason(test_db: DataBase):
    await test_db.bans.clear_table()
    await test_db.bans.new('123.4.5.6', commit=False)
    await test_db.flush()
    assert await test_db.bans.exists('123.4.5.6') == True
    res = await test_db.bans.by_ip('123.4.5.6')
    assert res is not None
    assert res.reason == 'no reason'
    await test_db.rollback()


async def test_delete(test_db: DataBase):
    await test_db.bans.clear_table()
    await test_db.bans.new('123.4.5.6', 'test', False)
    await test_db.flush()
    assert await test_db.bans.exists('123.4.5.6') == True

    assert await test_db.bans.delete_by_ip('123.4.5.6', False) == True
    await test_db.flush()
    assert await test_db.bans.exists('123.4.5.6') == False


async def test_del_old_bans(test_db: DataBase):
    test_db.session.add_all([
        Ban(ip='123.4.5.10', reason='test', date_unban=datetime.now() - timedelta(days=30)),
        Ban(ip='123.4.5.11', reason='test', date_unban=datetime.now() - timedelta(days=30)),
        Ban(
            ip='123.4.5.12',
            reason='test',
            date_unban=datetime.now() - timedelta(days=1),
            permanent=True
        ),
        Ban(
            ip='123.4.5.13',
            reason='test',
            date_unban=datetime.now() - timedelta(days=1),
            white=True
        ),
    ])
    await test_db.commit()

    await test_db.bans.del_old_bans()
    await test_db.commit()
    assert await test_db.bans.exists('123.4.5.10') == False
    assert await test_db.bans.exists('123.4.5.11') == False
    assert await test_db.bans.exists('123.4.5.12') == True
    assert await test_db.bans.exists('123.4.5.13', white=True) == True
