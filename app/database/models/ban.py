from datetime import datetime

from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.spec_time import get_current_time
from app.database import Base


class Ban(Base):
    __tablename__ = 'bans'
    ip: Mapped[str] = mapped_column(primary_key=True)
    reason: Mapped[str] = mapped_column(default="no reason")
    date_unban: Mapped[datetime] = mapped_column(DateTime, default=get_current_time())
    permanent: Mapped[bool] = mapped_column(default=False)
    white: Mapped[bool] = mapped_column(default=False)
