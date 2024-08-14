from datetime import datetime
import random
from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    password: str
    friend_ids: list[int] = []
    referral_id: Optional[int] = None
    id: int = random.randint(1000, 9999)
    auto_withdraw: bool = True
    wallet_address: Optional[str] = None