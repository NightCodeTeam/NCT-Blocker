from typing import Tuple, List
from datetime import datetime
from pydantic import BaseModel


class Ban(BaseModel):
    """
    Модель бана или белого адреса:
        - ip
        - reason - причина бана или записи в белый список
        - date_unban - дата снятия бана
        - permanent - является ли бан вечным
        - white - является ли запись в белый список
    """
    ip: str
    reason: str
    date_unban: datetime
    permanent: bool
    white: bool


class Bans(BaseModel):
    bans: Tuple[Ban] | List[Ban]


class NewBan(BaseModel):
    """
    Модель для создания нового бана или белого адреса:
        - ip
        - reason - причина бана или записи в белый список
        - duration_days - количество дней до снятия бана (по умолчанию 3)
        - permanent - является ли бан вечным (по умолчанию False)
        - white - является ли запись в белый список (по умолчанию False)
    """
    ip: str
    reason: str = 'no reason'
    duration_days: int = 3
    permanent: bool = False
    white: bool = False
