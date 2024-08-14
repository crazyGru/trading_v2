from datetime import datetime, timedelta
import hashlib
import hmac
import time
import json
import requests

API_KEY = 'rmXbSc9prPNN0zvdqmdqZgPlTUNXRkWhKOmuKBmoUVjkz27YbOucEucLJHJXsz3B'
API_SECRET = 'lX6OFrDJsqX4or62kvg1R6ZK6EVmbXlARpsof4LGg6jIJWaOl1jnHbyno6D7l0gN'

async def withdraw_from_boss(coin, address, amount, network=None, address_tag=None):
    server_time_url = 'https://api.binance.com/api/v3/time'
    server_time_response = requests.get(server_time_url)
    server_time = server_time_response.json()['serverTime']

    endpoint = 'https://api.binance.com/sapi/v1/capital/withdraw/apply'
    timestamp = int(time.time() * 1000)

    params = {
        'coin': coin,              # e.g., 'USDT'
        'address': address,        # recipient's wallet address
        'amount': amount,          # amount to withdraw
        'timestamp': server_time     # current timestamp
    }

    if network:
        params['network'] = network
    if address_tag:
        params['addressTag'] = address_tag
    
    query_string = '&'.join([f'{key}={value}' for key, value in params.items()])
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params['signature'] = signature
    headers = {
        'X-MBX-APIKEY': API_KEY
    }
    response = requests.post(endpoint, headers=headers, params=params)

    return response.json()