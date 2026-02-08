
from contextlib import asynccontextmanager
from fastapi import HTTPException, status, Request, FastAPI
import redis.asyncio as redis

from core.requests_makers import HttpMakerAsync
from core.redis_client import RedisClient

from app.settings import settings
# Файл настроек с url сервиса, ключа приложения к redis и ключа приложения

# Сервис связи с API блокировки
class BlocklistService(HttpMakerAsync):
    def __init__(self):
        super().__init__(
            base_url=settings.BLOCKER_URL,
            base_headers={
                'X-Access-Code': settings.BLOCKER_ACCESS_CODE
            }
        )

    async def in_ban(self, ip: str, redis: RedisClient) -> bool:
        data = await redis.get_json(
            key=f'in_ban:ip_address:{ip}',
            spec_app_prefix=settings.BLOCKER_REDIS_PREFIX
        )
        if data is not None and type(data.get('ok')) == bool:
            return data['ok']
        return (await self._make(f'/v1/bans/{ip}', method='GET')).json.get('ok', False)

    async def ban(
        self, ip: str,
        reason: str = 'no reason',
        duration_days: int = 3,
        permanent: bool = False,
        white: bool = False
    ) -> bool:
        return (await self._make(f'/v1/bans', method='POST', json={
            'ip': ip,
            'reason': reason,
            'duration_days': duration_days,
            'permanent': permanent,
            'white': white
        })).json.get('ok', False)


blocklist_service = BlocklistService()



# Добавляем redis и настраиваем приложение
redis_c = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # код до устновки redis
    app.state.redis = RedisClient(
        redis_pool=redis_c,
        prefix=settings.REDIS_PREFIX,
        expire=settings.REDIS_EXPIRE
    )
    # код после
    yield


app = FastAPI(
    # настройки приложения
    lifespan=lifespan
)

# И middleware для блокировки
@app.middleware('http')
async def blocker(request: Request, call_next):
    # Проверяем в бане ли пользователь
    if await blocklist_service.in_ban(request.client.host, RedisClient(
        redis_pool=redis_c,
        prefix=settings.REDIS_PREFIX,
        expire=settings.REDIS_EXPIRE
    )):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        )
    # Проверяем не ведет ли эндпойнт в никуда
    exceptions_routes = [ # список эндпоинтов, которые сразу получают бан
        '/.env',
    ]
    if not settings.DEBUG:
        exceptions_routes.extend([
            '/openapi.json',
            '/docs',
            '/redoc',
            '/swagger',
        ])
    routes = tuple([i.path.split('{')[0] for i in app.routes if i not in exceptions_routes])
    if not request.url.path.startswith(routes):
        await blocklist_service.ban(
            ip=request.client.host,
            reason='app_name > Endpoint not found', # Вместо app_name укажите название приложения
            duration_days=3,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        )
    response = await call_next(request)
    return response
