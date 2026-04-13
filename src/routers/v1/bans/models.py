from typing import Tuple, List
from datetime import datetime
from pydantic import BaseModel


class Ok(BaseModel):
    ok: bool = False


class Ban(BaseModel):
    ip: str
    reason: str
    date_unban: datetime
    permanent: bool
    white: bool


class Bans(BaseModel):
    bans: Tuple[Ban] | List[Ban]


class NewBan(BaseModel):
    ip: str
    reason: str = 'no reason'
    duration_days: int = 3
    permanent: bool = False
    white: bool = False
