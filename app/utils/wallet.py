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
    try:
        
        charge_history = await db['charge_history'].find({"from": wallet}).to_list(None)
        withdraw_history = await db['withdraw_history'].find({"to": wallet}).to_list(None)

        total_charged = sum(float(charge['amount']) for charge in charge_history)
        total_withdrawn = sum(float(withdraw['amount']) for withdraw in withdraw_history)
        return total_charged - total_withdrawn
    except AddressNotFound:
        return 0.0

async def get_boss_wallet() -> BossWallet:
    boss_wallet = await db["boss_wallets"].find_one()
    return BossWallet(**boss_wallet) if boss_wallet else None