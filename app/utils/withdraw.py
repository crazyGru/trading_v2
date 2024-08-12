from datetime import datetime, timedelta
import hashlib
import hmac
import time
import json
import requests
from tronpy import Tron

from app.crud.boss_wallet import get_boss_wallet
from app.models.Withdrwal import Withdrawal

def gen_sign(method, url, query_string=None, payload_string=None):
    key = 'f8502bc0e9a04a1e9a3f0a9ecd5b03cf'        # api_key
    secret = 'adf2ba6f64a7b063600a51a548b0d16605745668b809cf4d51ce34a8767157c5'     # api_secret

    t = time.time()
    m = hashlib.sha512()
    m.update((payload_string or "").encode('utf-8'))
    hashed_payload = m.hexdigest()
    s = '%s\n%s\n%s\n%s\n%s' % (method, url, query_string or "", hashed_payload, t)
    sign = hmac.new(secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
    return {'KEY': key, 'Timestamp': str(t), 'SIGN': sign}

host = "http://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url = '/withdrawals'
query_param = ''

async def withdraw_from_boss(username: str, db, wallet_address: str, amount_to_withdraw: float) -> str:
    user = await db['users'].find_one({"username": username})
    if not user:
        return "User not found."
    
    if user['transaction_time'] and datetime.utcnow() < user['transaction_time'] + timedelta(hours=24):
        return "Withdrawal not allowed within 24 hours of the last transaction."
    
    if amount_to_withdraw <= 0:
        return "Invalid withdrawal amount."
    
    if amount_to_withdraw > user["transferred_amount"]:
        return "Insufficient funds for withdrawal."
    
    withdrawal_record = Withdrawal(
        user_id=user['id'],
        wallet_address=wallet_address,
        amount=amount_to_withdraw,
        status=user['auto_withdraw'],
        timestamp=datetime.utcnow()
    )

    await db['withdrawal_history'].insert_one(withdrawal_record.dict())
    
    body = {
        "withdraw_order_id":"order_123456",
        "currency":"USDT",
        "address":wallet_address,
        "amount":amount_to_withdraw,
        "memo":"",
        "chain":"TRX"
    }
    body_str = json.dumps(body)
    sign_headers = gen_sign('POST', prefix + url, query_param, body_str)
    headers.update(sign_headers)
    r = requests.request('POST', host+prefix+url, headers=headers, data = body_str)
    return r.json()