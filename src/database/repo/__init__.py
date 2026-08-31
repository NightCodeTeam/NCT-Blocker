from sqlalchemy.ext.asyncio import AsyncSession
from core.sql_repository import DataBaseRepo
from .bans import BanRepo
from .times import BanTimeRepo


class DataBase(DataBaseRepo):
    bans: BanRepo
    times: BanTimeRepo

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session)

        self.bans = BanRepo(session=session)
        self.times = BanTimeRepo(session=session)
