from fastapi import APIRouter, HTTPException, status

from .models import Ok, Bans, NewBan
from src.depends import DBDep
from core.fast_decorators import cache
from core.redis_client import RedisDep
from core.fast_depends import PaginationParams


bans_router_v1 = APIRouter(prefix='/v1/bans', tags=['bans'])


@bans_router_v1.post('', response_model=Ok)
async def add_ban(db: DBDep, data: NewBan, redis: RedisDep):
    """
    Добавить бан или белый список
    - ip - IP адрес пользователя
    - reason - причина бана
    - duration_days - длительность бана в днях
    - permanent - является ли бан вечным
    - white - добавить IP адрес в белый список
    """
    # Проверка на валидность IP адреса
    if len(data.ip.split('.')) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid IP address'
        )
    # Проверка на существование IP адреса в базе данных
    if await db.bans.exists(data.ip):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='IP address already in ban'
        )
    db_ans = await db.bans.new(
        ip=data.ip,
        reason=data.reason,
        duration_days=data.duration_days,
        permanent=data.permanent,
        white=data.white,
        commit=False
    )
    if db_ans:
        # Если IP адрес добавлен в базу данных, удалить его из кэша
        await redis.delete(f'in_ban:ip_address:{data.ip}')
    return {'ok': db_ans}


@bans_router_v1.get('', response_model=Bans)
async def bans(db: DBDep, pagination: PaginationParams):
    """Список всех банов и белых списков. Для пагинации параметров требуется чтобы и skip и limit были указаны"""
    if pagination.skip is not None and pagination.limit is not None:
        return {'bans': await db.bans.pagination(skip=pagination.skip, limit=pagination.limit)}
    return {'bans': await db.bans.all()}


@bans_router_v1.get('/{ip_address}', response_model=Ok)
@cache(key='in_ban', expire=21600)
async def in_ban(ip_address: str, db: DBDep, redis: RedisDep):
    """Проверка наличия IP адреса в банах. Эндпойнт кэшируется на 6 часов"""
    # Проверка на валидность IP адреса
    if len(ip_address.split('.')) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid IP address'
        )
    return {'ok': await db.bans.exists(ip_address)}


@bans_router_v1.delete('/{ip_address}', response_model=Ok)
async def del_ban(ip_address: str, db: DBDep, redis: RedisDep):
    """Удаление IP адреса из банов или белых списков"""
    await redis.delete(f'in_ban:ip_address:{ip_address}')
    return {'ok': await db.bans.delete_by_ip(ip_address)}
