from fastapi import APIRouter, HTTPException, status, Request

from .models import Bans, NewBan
from src.depends import DBDep, IPDep
from core.fast_decorators import cache_path
from core.fast_depends import PaginationParams
from core.pydantic_misc_models import Ok, Detail
from core.redis_client import RedisDep


bans_router_v1 = APIRouter(prefix='/v1/bans', tags=['bans'])


@bans_router_v1.get('', response_model=Bans)
async def bans(db: DBDep, pagination: PaginationParams):
    """Список всех банов и белых списков. Для пагинации параметров требуется чтобы и skip и limit были указаны"""
    if pagination.skip is not None and pagination.limit is not None:
        return {'bans': await db.bans.pagination(skip=pagination.skip, limit=pagination.limit)}
    return {'bans': await db.bans.all()}


@bans_router_v1.post('/{ip}',
    responses={
        200: {'model': Ok},
        400: {'description': 'Invalid IP address or IP address already in ban', 'model': Detail},
    },
)
async def add_ban(ip: IPDep, db: DBDep, data: NewBan, redis: RedisDep):
    """
    Добавить бан или белый список
    - reason - причина бана
    - duration_days - длительность бана в днях
    - permanent - является ли бан вечным
    - white - добавить IP адрес в белый список
    """
    # Проверка на существование IP адреса в базе данных
    if await db.bans.exists(ip):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='IP address already in ban'
        )
    count = await db.times.increase(ip)
    db_ans = True if await db.bans.new(
        ip=ip,
        reason=data.reason,
        duration_days=data.duration_days + (count // 10),
        permanent=data.permanent,
        white=data.white,
        commit=False
    ) is not None else False
    if db_ans:
        # Если IP адрес добавлен в базу данных, удалить его из кэша
        await redis.delete(f'/v1/bans/{ip}')
    return {'ok': db_ans}


@bans_router_v1.get('/{ip}', response_model=Ok | Detail, responses={
    200: {'model': Ok},
    400: {'description': 'Invalid IP address', 'model': Detail},
})
@cache_path(expire=21600)
async def in_ban(request: Request, ip: IPDep, db: DBDep):
    """Проверка наличия IP адреса в банах. Эндпойнт кэшируется на 6 часов"""
    return {'ok': await db.bans.exists(ip)}


@bans_router_v1.delete('/{ip}', response_model=Ok)
async def del_ban(ip: IPDep, db: DBDep, redis: RedisDep):
    """Удаление IP адреса из банов или белых списков"""
    await redis.delete(f'/v1/bans/{ip}')
    return {'ok': await db.bans.delete_by_ip(ip)}
