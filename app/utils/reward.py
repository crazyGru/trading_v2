from app.utils.wallet import get_wallet_balance


async def get_reward_amount(wallet_address: str):
    available_amount = await get_wallet_balance(wallet_address)
    available_amount /= 1000000

    # Determine reward based on available amount
    if 12 <= available_amount < 100:
        return available_amount * 0.108  # 10.8%
    elif 100 <= available_amount < 500:
        return available_amount * 0.123  # 12.3%
    elif 500 <= available_amount < 2000:
        return available_amount * 0.138  # 13.8%
    elif 2000 <= available_amount < 5000:
        return available_amount * 0.158  # 15.8%
    elif 5000 <= available_amount < 10000:
        return available_amount * 0.178  # 17.8%
    elif 10000 <= available_amount < 20000:
        return available_amount * 0.198  # 19.8%
    elif 20000 <= available_amount < 50000:
        return available_amount * 0.228  # 22.8%
    elif 50000 <= available_amount < 100000:
        return available_amount * 0.258  # 25.8%
    elif available_amount >= 100000:
        return available_amount * 0.308  # 30.8%
    else:
        return 0  # No reward for amounts less than 12
