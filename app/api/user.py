from datetime import datetime
import hashlib
import hmac
import cv2
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from fastapi.responses import FileResponse

from fastapi.security import OAuth2PasswordRequestForm
import requests
from tronpy import Tron
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.crud.boss_wallet import get_boss_wallet, save_boss_wallet
from app.crud.user import get_user, create_user, get_users
from app.models.charge import Charge
from app.models.user import User
from app.utils.payment import generate_payment_link
from app.utils.qrcode_generator import generate_qr_code
from app.utils.reward import get_reward_amount
from app.utils.transaction import get_transaction_info
from app.utils.transfer import transfer_to_boss
from app.utils.wallet import get_wallet_balance
from app.db.database import db
from app.utils.withdraw import withdraw_from_boss
from pathlib import Path

router = APIRouter()

@router.get("/users", response_model=List[User])
async def read_users():
    users = await get_users()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users

@router.get("/users/{username}", response_model=User)
async def read_user(username: str, current_user : User = Depends(get_current_user)):
    user = await get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users/{username}/charge_history")
async def get_charge_history(username: str):
    user = await get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    charge_history = await db['charge_history'].find({"from": user.wallet_address}).to_list(length=100)

    for record in charge_history:
        record['_id'] = str(record['_id'])

    return {"charge_history": charge_history}

@router.get("/users/{username}/withdraw_history")
async def get_withdraw_history(username: str):
    user = await get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    withdraw_history = await db["withdraw_history"].find({"to": user.wallet_address}).to_list(length=100)
    for record in withdraw_history:
        record['_id'] = str(record['_id'])
    
    return {"withdraw_history": withdraw_history}

@router.get("/users/{username}/revenue_history")
async def get_revenue_history(username: str):
    user = await get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    revenue_history = await db['charge_history'].find({"from": user.wallet_address, "type": "revenue"}).to_list(length=100)

    for record in revenue_history:
        record['_id'] = str(record['_id'])

    return {"revenue_history": revenue_history}


@router.post("/users", response_model=User)
async def create_new_user(user: User):
    user.password = hash_password(user.password)
    return await create_user(user)

@router.post("/token")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user = await get_user(form.username)
    if not user or not verify_password(form.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    user.password = ""
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}

@router.post("/generate_payment_link")
async def generate_payment():
    
    payment_link = generate_payment_link()
    qr_code_image = generate_qr_code()

    return {
        "payment_link": payment_link,
        "qr_code": qr_code_image
    }

@router.get("/invite/{username}")
async def get_invite_code(username: str):
    user = await get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    invite_code = user.id
    return {"code": invite_code}

@router.get('/users/{username}/balance')
async def check_balance(username: str):
    user = await get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    balance = await get_wallet_balance(user.wallet_address)
    return {"username": username, "balance": balance}

@router.post("/transfer_to_boss/{boss_wallet}")
async def transfer_all_to_boss(boss_wallet: str):
    try:
        result = await transfer_to_boss(boss_wallet, db)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/withdraw/{username}")
async def withdraw(username: str, amount: float):
    try:
        user = await get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.auto_withdraw:
            raise HTTPException(status_code=403, detail="Please wait a moment, your transaction is currently under review.")

        balance = await get_wallet_balance(user.wallet)
        if amount > balance:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        result = await withdraw_from_boss('USDT', user.wallet_address, amount, 'TRX')
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.patch("/user/{username}/auto_withdraw")
async def set_auto_withdraw(username: str, auto_withdraw: bool):
    user = await get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    
    user.auto_withdraw = auto_withdraw
    await db['users'].update_one({'username': username}, {"$set": {"auto_withdraw": auto_withdraw}})
    
    return {"message": "Auto withdraw setting updated successfully", "auto_withdraw": user.auto_withdraw}
    
@router.post("/boss_wallet")
async def set_boss_wallet(wallet_address: str, private_key: str):
    await save_boss_wallet(wallet_address, private_key)
    return {"message": "Boss wallet address and private key saved successfully."}

@router.get('/users/{username}/wallet')
async def get_wallet_amount(username: str):
    user = await get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    balance = await get_wallet_balance(user.wallet)
    if balance <= 0:
        return {"balance": 0}
    
    boss_wallet = await get_boss_wallet()
    tron = Tron()
    txn = (
        tron.trx.transfer(user.wallet, boss_wallet.wallet_address, balance * 1_000_000)
        .build()
        .sign(user.private_key)
    )
    txn.broadcast()
    await db['users'].update_one(
        {"username": username},
        {"$set": {"transferred_amount": balance, "transaction_time": datetime.utcnow()}}
    )
    
    return {"balance": balance}

@router.get('/users/{username}/earning_info')
async def get_earnings_info(username: str):
    user = await get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return await get_reward_amount(user.wallet_address)

@router.post("/charge")
async def charge_user(charge: Charge):

    charge_data = charge.dict()
    charge_data['timestamp'] = datetime.utcnow()
    await db['charge_history'].insert_one(charge_data)

    return {"message": "Charge recorded successfully", "charge": charge_data}

api_key = 'rmXbSc9prPNN0zvdqmdqZgPlTUNXRkWhKOmuKBmoUVjkz27YbOucEucLJHJXsz3B'
api_secret = 'lX6OFrDJsqX4or62kvg1R6ZK6EVmbXlARpsof4LGg6jIJWaOl1jnHbyno6D7l0gN'

@router.get('/get_charge_history')
async def get_charge_history(coin: str = 'USDT', status: int = 1):
    try:
        server_time_url = 'https://api.binance.com/api/v3/time'
        server_time_response = requests.get(server_time_url)
        server_time = server_time_response.json()['serverTime']

        url = 'https://api.binance.com/sapi/v1/capital/deposit/hisrec'

        params = {
            'coin': coin,
            'status': status,
            'timestamp': server_time,
            'recvWindow': 5000
        }

        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        params['signature'] = signature
        headers = {'X-MBX-APIKEY': api_key}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json())
        
        items = response.json()
        res = []
        for item in items:
            txId = item['txId']
            txInfo = get_transaction_info(txId)
            temp = {
                "timestamp": txInfo["timestamp"] / 1000,
                "from": txInfo["trc20TransferInfo"][0]["from_address"],
                "to": txInfo["trc20TransferInfo"][0]["to_address"],
                "amount": txInfo["trc20TransferInfo"][0]["amount_str"]
            }
            res.append(temp)

        for record in res:
            record['timestamp'] = datetime.fromtimestamp(record['timestamp'])
            await db['charge_history'].update_one(
                {"timestamp": record['timestamp'], "from": record['from']},
                {"$set": record},
                upsert=True
            )

        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get('/get_withdraw_history')
async def get_withdraw_history(coin: str = 'USDT', status: int = 1):
    try:
        server_time_url = 'https://api.binance.com/api/v3/time'
        server_time_response = requests.get(server_time_url)
        server_time = server_time_response.json()['serverTime']

        url = 'https://api.binance.com/sapi/v1/capital/withdraw/history'
        params = {
            'coin': coin,
            'status': status,
            'timestamp': server_time,
            'recvWindow': 5000
        }

        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        params['signature'] = signature
        headers = {'X-MBX-APIKEY': api_key}

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json())
        
        items = response.json()
        res = []
        for item in items:
            txId = item['txId']
            txInfo = get_transaction_info(txId)
            temp = {
                "timestamp": txInfo["timestamp"] / 1000,
                "from": txInfo["trc20TransferInfo"][0]["from_address"],
                "to": txInfo["trc20TransferInfo"][0]["to_address"],
                "amount": txInfo["trc20TransferInfo"][0]["amount_str"]
            }
            res.append(temp)

        for record in res:
            record['timestamp'] = datetime.fromtimestamp(record['timestamp'])
            await db['withdraw_history'].update_one(
                {"timestamp": record['timestamp'], "to": record['to']},
                {"$set": record},
                upsert=True
            )

        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get('/get_reward/{username}')
async def get_reward(username: str):
    user = await get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    charge_history = await db['charge_history'].find({"from": user.wallet_address}).to_list(None)
    withdraw_history = await db["withdraw_history"].find({"to": user.wallet_address}).to_list(None)
    current_timestamp = datetime.utcnow()
    last_timestamp = datetime(1900, 1, 1, 0, 0)
    for charge in charge_history:
        last_timestamp = max(charge['timestamp'], last_timestamp)
    for withdraw in withdraw_history:
        last_timestamp = max(withdraw['timestamp'], last_timestamp)

    is_later_than_24hrs = (current_timestamp - last_timestamp).total_seconds() > 86400

    if is_later_than_24hrs:
        await db['charge_history'].update_one(
            {"timestamp": current_timestamp, "from": user.wallet_address},
            {"$set": {
                "timestamp": current_timestamp,
                "from": user.wallet_address,
                "to": generate_payment_link(),
                "amount": await get_reward_amount(user.wallet_address),
                "type": "revenue"
            }},
            upsert=True
        )
        return {"message": "Successfully received daily reward."}
    else:
        return {"message": "Not available yet. You can do this action in every 24hrs."}
    
