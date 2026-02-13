from core.supabase_client import db

async def get_active_pro_users():
    response = db.table("profiles").select("*").eq("is_pro", True).execute()
    return response.data

async def get_user_by_id(telegram_id: int):
    response = db.table("profiles").select("*").eq("id", telegram_id).execute()
    return response.data[0] if response.data else None

async def create_new_user(telegram_id: int, username: str):
    user = await get_user_by_id(telegram_id)
    if not user:
        data = {
            "id": telegram_id,
            "username": username,
            "is_pro": False
        }
        db.table("profiles").insert(data).execute()
        return True
    return False

async def update_user_token(telegram_id: int, token: str):
    db.table("profiles").update({"custom_bot_token": token}).eq("id", telegram_id).execute()

async def get_user_products(owner_id: int):
    response = db.table("products").select("*").eq("owner_id", owner_id).execute()
    return response.data

async def add_product(owner_id: int, name: str, price: float, content: str, description: str = ""):
    data = {
        "owner_id": owner_id,
        "name": name,
        "price": price,
        "content": content,
        "description": description
    }
    db.table("products").insert(data).execute()

async def delete_product(product_id: str, owner_id: int):
    db.table("products").delete().eq("id", product_id).eq("owner_id", owner_id).execute()

async def create_order(buyer_id: int, product_id: str, seller_id: int):
    data = {
        "buyer_id": buyer_id,
        "product_id": product_id,
        "seller_id": seller_id,
        "status": "pending"
    }
    response = db.table("orders").insert(data).execute()
    return response.data[0] if response.data else None

async def confirm_order(order_id: str):
    db.table("orders").update({"status": "completed"}).eq("id", order_id).execute()
