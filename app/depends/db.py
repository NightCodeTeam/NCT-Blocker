from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.database.repo import DataBase


async def get_db() -> AsyncGenerator[DataBase, None]:
    async with get_session() as d:
        yield DataBase(d)


DBDep = Annotated[DataBase, Depends(get_db)]

SessionDep = Annotated[AsyncSession, Depends(get_session)]
