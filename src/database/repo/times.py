from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from core.sql_repository import RepositoryObj
from core.spec_time import get_current_time
from src.database.models import BanTime

from src.settings import settings


class BanTimeRepo(RepositoryObj):
    """
    Репозиторий для работы с моделью BanTime.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(BanTime, session=session)

    async def by_ip(self, ip_address: str) -> BanTime | None:
        """
        Возвращает модель BanTime по IP или None если не найдено.
        """
        return await self.get(filter_=BanTime.ip == ip_address)

    async def increase(self, ip_address: str) -> int:
        """
        Увеличивает счетчик блокировок для IP.
        """
        data = await self.by_ip(ip_address)
        if data:
            data.count += 1
            data.last_date = get_current_time().date()
            return data.count
        await self._add(BanTime(ip=ip_address))
        return 1

    async def del_old_bans(self):
        """
        Удаляет старые отчеты.
        """
        await self._delete(
            filter_=BanTime.last_date < (get_current_time() - timedelta(
                days=settings.BAN_TIMES_EXPIRE
            )).date()
        )
