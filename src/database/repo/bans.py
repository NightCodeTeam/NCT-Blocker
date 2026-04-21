from typing import override

from sqlalchemy import and_, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, and_

from core.sql_repository import RepositoryObj, SessionNotFound
from core.spec_time import time_with_shift, get_current_time
from src.database.models.ban import Ban

from src.settings import settings


class BanRepo(RepositoryObj):
    """
    Репозиторий для работы с моделью Ban.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(Ban, session=session)

    async def exists(self, ip_address: str, white: bool = False) -> bool:
        """
        Проверяет наличие ip адреса в бане/белом списке.
        """
        return await self._exists(filter_=and_(Ban.ip == ip_address, Ban.white == white))

    @override
    async def count(self, white: bool = False) -> int:
        """
        Возвращает количество банов/белых адресов.
        """
        try:
            return (await self.session.execute(
                select(func.count()).select_from(self.model).where(Ban.white == white))
            ).scalar() or 0
        except AttributeError:
            raise SessionNotFound()

    async def by_ip(self, ip_address: str) -> Ban | None:
        """
        Возвращает модель Ban по IP или None если не найдено.
        """
        return await self.get(filter_=Ban.ip == ip_address)

    async def new(
        self,
        ip: str,
        reason: str = 'no reason',
        duration_days: int = 3,
        permanent: bool = False,
        white: bool = False,
        commit: bool = False
    ) -> bool:
        """
        Добавляет новую модель Ban в базу данных.
            - ip
            - reason - причина бана
            - duration_days - количество дней до разбана
            - permanent - является ли бан навсегда
            - white - является ли адрес белым
        """
        try:
            if len(ip.split('.')) != 4:
                return False
            return await self.add(Ban(
                ip=ip,
                reason=reason if reason else "no reason",
                date_unban=time_with_shift(duration_days),
                permanent=permanent,
                white=white,
            ), commit=commit)
        except IntegrityError:
            return False

    async def delete_by_ip(self, ip_address: str, commit: bool = False) -> bool:
        """
        Удаляет модель Ban по IP.
        """
        data = await self.by_ip(ip_address)
        if data:
            return await self.delete(obj=data, commit=commit)
        return False

    async def pagination(self, skip: int | None = None, limit: int | None = None) -> tuple[Ban, ...]:
        """
        Возвращает пагинацию моделей Ban.
        """
        return await super()._pagination(
            skip=skip,
            limit=limit,
            order_by_field=f"ip",
        )

    async def del_old_bans(self):
        """
        Удаляет старые баны (непостоянные, не белые, у которых истек срок разбана).
        """
        await self.session.execute(
            delete(Ban).where(
                and_(
                    Ban.date_unban < get_current_time(),
                    Ban.permanent == False,
                    Ban.white == False
                )
            )
        )
        await self.session.commit()
