from tronpy import Tron
from tronpy.exceptions import AddressNotFound

from app.models.bossWallet import BossWallet
from app.db.database import db

def create_trc20_wallet() -> str:
    tron = Tron(provider=[
        "d53ecc63-e84a-4cca-937c-3ab3b3996b27", 
        "ca96c310-ee04-4c4b-acca-1d3441f446f6", 
        "b12fb644-2ac3-4173-bf2c-9f4afac022a1"])
    account = tron.generate_address()
    return {
        "public_key": account['base58check_address'],
        "private_key": account['private_key']
    }

async def get_wallet_balance(wallet: str) -> float:
    tron = Tron()
    try:
        balance = await tron.get_account_balance(wallet)
        return balance / 1_000_000
    except AddressNotFound:
        balance = 0.0

    return balance

async def get_boss_wallet() -> BossWallet:
    boss_wallet = await db["boss_wallets"].find_one()
    return BossWallet(**boss_wallet) if boss_wallet else None