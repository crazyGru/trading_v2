

from app.models.bossWallet import BossWallet
from app.db.database import db


async def get_boss_wallet(wallet_address: str, private_key: str) -> None:
    boss_wallet = BossWallet(wallet_address=wallet_address, private_key = private_key)
    await db["boss_wallets"].insert_one(boss_wallet.dict())

async def save_boss_wallet() -> BossWallet:
    boss_wallet = await db["boss_wallets"].find_one()
    return BossWallet(**boss_wallet) if boss_wallet else None