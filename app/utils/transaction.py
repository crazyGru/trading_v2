from fastapi import HTTPException
from security import safe_requests


def get_transaction_info(txid: str) -> dict:
    url = f"https://apilist.tronscan.org/api/transaction-info?hash={txid}"
    response = safe_requests.get(url)

    if response.status_code == 200:
        transaction_data = response.json()
        return transaction_data
    else:
        raise HTTPException(status_code=response.status_code, detail = "Error retrieving transaction data")
