from datetime import datetime
import random
from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    password: str
    wallet: str = None
    private_key: str = None
    transferred_amount: float = 0.0
    transaction_time: datetime = None
    friend_ids: list[int] = []
    referral_id: int = None
    id: int = random.randint(1000, 9999)
    auto_withdraw: bool = True