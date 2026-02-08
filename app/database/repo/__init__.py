from sqlalchemy.ext.asyncio import AsyncSession
from core.sql_repository import DataBaseRepo
from .bans import BanRepo


class DataBase(DataBaseRepo):
    def __init__(self, session: AsyncSession) -> None:
        self.bans = BanRepo(session=session)
        super().__init__(session=session)
