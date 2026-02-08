import os

import psutil
from fastapi import APIRouter
from pydantic import BaseModel


class StatusResponse(BaseModel):
    ok: bool
    cpu_usage: float
    memory_usage: float
    disk_usage: float


utils_router_v1 = APIRouter(prefix="/v1/utils", tags=["utils"])
process = psutil.Process(os.getpid())


@utils_router_v1.get("/status", response_model=StatusResponse)
async def status():
    return {
        "ok": True,
        "cpu_usage": process.cpu_percent(),
        "memory_usage": process.memory_info().rss / 1024 / 1024,
        "disk_usage": psutil.disk_usage('/').percent
    }
