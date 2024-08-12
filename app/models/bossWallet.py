from pydantic import BaseModel

class BossWallet(BaseModel):
    wallet_address: str
    private_key: str