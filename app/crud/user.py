from datetime import datetime
from typing import List
from app.models.user import User
from app.db.database import db
from app.utils.wallet import create_trc20_wallet

async def get_user(username: str) -> User:
    user = await db["users"].find_one({"username": username})
    if user:
        user['transaction_time'] = user.get('transaction_time') or datetime.utcnow()  # Set default datetime
        return User(**user)
    return None

async def get_user_by_id(referral_id: int) -> User:
    return await db['users'].find_one({'id': referral_id})

async def create_user(user: User) -> User:
    if user.referral_id:
        referral_user = await get_user_by_id(user.referral_id)
        if not referral_user:
            raise ValueError("Referral ID does not exist.")
        
        await db["users"].update_one(
            {"id": user.referral_id},
            {"$addToSet": {"friend_ids": user.id}}
        )

    user.auto_withdraw = user.auto_withdraw if user.auto_withdraw is not None else True
    await db["users"].insert_one(user.dict())
    return user

async def get_users() -> List[User]:
    users_data = await db["users"].find().to_list(1000)  # Fetch user data
    return [User(username=user['username'], email=user['email'], password=user['password'],  # Explicitly map fields
                  friend_ids=user.get('friend_ids', []), 
                  referral_id=user.get('referral_id'), 
                  id=user['id'], 
                  auto_withdraw=user.get('auto_withdraw', True), 
                  wallet_address=user.get('wallet_address')) for user in users_data]
