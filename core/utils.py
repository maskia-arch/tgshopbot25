import httpx
from services.db_service import db

async def get_user_id_by_shop_id(shop_id: str):
    try:
        response = db.table("profiles").select("id").eq("shop_id", shop_id.upper()).single().execute()
        return response.data["id"] if response.data else None
    except:
        return None

async def get_ltc_price(eur_amount: float):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.coinbase.com/v2/prices/LTC-EUR/spot")
            data = response.json()
            price = float(data["data"]["amount"])
            return round(eur_amount / price, 8)
    except:
        return None

def validate_crypto_address(address: str, method: str):
    address = address.strip()
    if method == "paypal_email":
        return "@" in address and "." in address
    if method == "wallet_btc":
        return address.startswith(("1", "3", "bc1")) and len(address) >= 26
    if method == "wallet_ltc":
        return address.startswith(("L", "M", "ltc1")) and len(address) >= 26
    if method == "wallet_eth":
        return address.startswith("0x") and len(address) == 42
    if method == "wallet_sol":
        return len(address) >= 32 and len(address) <= 44
    return True

def format_stock_display(content: str):
    if not content:
        return 0
    items = [i for i in content.split("\n") if i.strip()]
    return len(items)
