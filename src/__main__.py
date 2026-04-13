try:
    import src
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

from core.redis_client import RedisClient
from src.database import init_db
from src.database.session import new_session
from src.database.repo import DataBase
from src.routers.v1 import bans_router_v1, utils_router_v1

from src.settings import settings


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
    title='Blocklist Service',
    description='Is ip banned?',
    version='0.0.2',
    lifespan=lifespan,
)

app.include_router(bans_router_v1)
app.include_router(utils_router_v1)


@app.middleware('http')
async def check_access_code(request: Request, call_next):
    """
    Проверка кода доступа для приложения.
    Если DEBUG=False и X-Access-Code не совпадает с ACCESS_CODE, возвращает 401.
    """
    if not settings.DEBUG and request.headers.get('X-Access-Code') != settings.ACCESS_CODE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return await call_next(request)


if __name__ == "__main__":
    try:
        uvicorn.run(app, host=settings.HOST, port=settings.PORT)
    except Exception as e:
        logging.exception(e)
