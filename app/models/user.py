from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import secrets

class User(BaseModel):
    username: str
    email: str
    password: str
    friend_ids: list[int] = []
    referral_id: Optional[int] = None
    id: int = secrets.SystemRandom().randint(1000, 9999)
    auto_withdraw: bool = True
    wallet_address: Optional[str] = None
