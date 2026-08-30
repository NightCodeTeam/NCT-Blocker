from datetime import date

from sqlalchemy import Date
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from core.spec_time import get_current_time


class BanTime(Base):
    """
    Модель сколько раз был забанен пользователь по IP-адресу.
    - ip: IP-адрес пользователя, который был забанен.
    - count: Количество раз, когда пользователь был забанен.
    - last_date: Дата последнего бана.

    Чем больше попыток было совершено, \
    тем больше шанс на постоянный ip и увелечение времени блокировки.
    """

    __tablename__ = 'ban_times'
    ip: Mapped[str] = mapped_column(primary_key=True)
    count: Mapped[int] = mapped_column(default=1)
    last_date: Mapped[date] = mapped_column(Date, default=get_current_time().date())

    def __repr__(self) -> str:
        return f"BanTime(ip={self.ip}, count={self.count}, last_date={self.last_date})"

    def __str__(self) -> str:
        return f"BanTime {self.ip}, count={self.count}, last_date={self.last_date}"
