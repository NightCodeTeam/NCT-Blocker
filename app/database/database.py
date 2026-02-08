from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.settings import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    url=settings.DB_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG
)
new_session = async_sessionmaker(bind=engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        #await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
