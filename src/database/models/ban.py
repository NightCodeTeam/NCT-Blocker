from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from core.spec_time import get_current_time


class Ban(Base):
    """
    Модель бана. Хранит информацию о бане пользователя по IP-адресу.
    - ip: IP-адрес пользователя, который был забанен.
    - reason: Причина бана.
    - date_unban: Дата и время разбана.
    - permanent: Флаг перманентного бана.
    - white: Флаг белого списка (никогда не будет заблокирован).
    """

    __tablename__ = 'bans'
    ip: Mapped[str] = mapped_column(primary_key=True)
    reason: Mapped[str] = mapped_column(default="no reason")
    date_unban: Mapped[datetime] = mapped_column(DateTime, default=get_current_time())
    permanent: Mapped[bool] = mapped_column(default=False)
    white: Mapped[bool] = mapped_column(default=False)
