from datetime import datetime
from pydantic import BaseModel

class Charge(BaseModel):
    user_id: int
    amount: float
    timestamp: datetime