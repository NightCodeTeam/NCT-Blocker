try:
    import app
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))


from contextlib import asynccontextmanager
import logging

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
import redis.asyncio as redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.redis_client import RedisClient
from app.core.fast_routers import utils_router_v1
from app.database import init_db
from app.database.session import new_session
from app.database.repo import DataBase
from app.routers.v1 import bans_router_v1
from app.depends import DBDep

from app.settings import settings


redis_c = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)


async def auto_update():
    logging.info('> Daily auto update')
    async with new_session() as session:
        await DataBase(session).bans.del_old_bans()


# ? Планеровщик
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запускаем бд
    await init_db()

    # Подключаю Redis
    app.state.redis = RedisClient(
        redis_pool=redis_c,
        prefix=settings.REDIS_PREFIX,
        expire=settings.REDIS_EXPIRE
    )

    # Автообновление
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        auto_update,
        trigger=CronTrigger(hour=12, minute=00),  # Каждый день в 12:00 мск
        timezone="UTC"
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    name='WhiteList Service',
    description='Is ip address in whitelist?',
    version='0.0.1',
    lifespan=lifespan,
)

app.include_router(bans_router_v1)
app.include_router(utils_router_v1)


@app.middleware('http')
async def check_access_code(request: Request, call_next):
    if not settings.DEBUG and request.headers.get('X-Access-Code') != settings.ACCESS_CODE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Goodbye!'
        )
    response = await call_next(request)
    return response


if __name__ == "__main__":
    try:
        uvicorn.run(app, host=settings.HOST, port=settings.PORT)
    except Exception as e:
        logging.exception(e)
