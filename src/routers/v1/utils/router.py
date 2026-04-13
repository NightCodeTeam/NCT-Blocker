import os
from typing import Any

import psutil
from fastapi import APIRouter
from pydantic import BaseModel

from src.depends import DBDep


class StatusResponse(BaseModel):
    ok: bool
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    adt_data: dict[str, Any]


utils_router_v1 = APIRouter(prefix="/v1/utils", tags=["utils"])
process = psutil.Process(os.getpid())


@utils_router_v1.get("/status", response_model=StatusResponse)
async def status(db: DBDep):
    """
    Возвращает статус загруженности приложения.
    - ok - загрузка успешна
    - cpu_usage - использование CPU в процентах (может быть более 100% если используется несколько ядер)
    - memory_usage - использование памяти в мегабайтах
    - disk_usage - использование диска в процентах
    - adt_data - дополнительные данные
    """
    return {
        "ok": True,
        "cpu_usage": round(process.cpu_percent(), 1),
        "memory_usage": round(process.memory_info().rss / 1024 / 1024, 1),
        "disk_usage": round(psutil.disk_usage('/').percent, 1),
        "adt_data": {
            'blocked': await db.bans.count(white=False),
            'white': await db.bans.count(white=True)
        }
    }
