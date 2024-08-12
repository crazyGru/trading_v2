from datetime import datetime
from pydantic import BaseModel

class Withdrawal(BaseModel):
    user_id: int
    wallet_address: str
    amount: float
    status: bool
    timestamp: datetime