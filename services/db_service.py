import random
import string
import uuid
from core.supabase_client import db

def generate_unique_shop_id(length=6):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

async def get_active_pro_users():
    response = db.table("profiles").select("*").eq("is_pro", True).execute()
    return response.data

async def get_user_by_id(telegram_id: int):
    response = db.table("profiles").select("*").eq("id", telegram_id).execute()
    if response.data:
        user = response.data[0]
        if not user.get("shop_id"):
            new_id = generate_unique_shop_id()
            db.table("profiles").update({"shop_id": new_id}).eq("id", telegram_id).execute()
            user["shop_id"] = new_id
        return user
    return None

async def get_user_by_shop_id(shop_id: str):
    response = db.table("profiles").select("*").eq("shop_id", shop_id.upper()).execute()
    return response.data[0] if response.data else None

async def get_shop_by_token(token: str):
    response = db.table("profiles").select("*").eq("custom_bot_token", token).execute()
    return response.data[0] if response.data else None

async def create_new_user(telegram_id: int, username: str):
    user = await get_user_by_id(telegram_id)
    if not user:
        shop_id = generate_unique_shop_id()
        data = {
            "id": telegram_id,
            "username": username,
            "is_pro": False,
            "shop_id": shop_id
        }
        db.table("profiles").insert(data).execute()
        return True
    return False

async def update_user_token(telegram_id: int, token: str):
    db.table("profiles").update({"custom_bot_token": token}).eq("id", telegram_id).execute()

async def update_payment_methods(telegram_id: int, payment_data: dict):
    db.table("profiles").update(payment_data).eq("id", telegram_id).execute()

async def get_user_products(owner_id: int):
    try:
        response = db.table("products").select("*").eq("owner_id", int(owner_id)).execute()
        return response.data
    except Exception as e:
        print(f"Error: {e}")
        return []

async def add_product(owner_id: int, name: str, price: float, content: str, description: str = ""):
    clean_content = ""
    if content:
        items = [i.strip() for i in content.replace(",", "\n").split("\n") if i.strip()]
        clean_content = "\n".join(items)
    
    data = {
        "owner_id": int(owner_id),
        "name": name,
        "price": price,
        "content": clean_content,
        "description": description
    }
    db.table("products").insert(data).execute()

async def refill_stock(product_id, owner_id: int, new_content: str):
    try:
        query_id = int(product_id) if str(product_id).isdigit() else product_id
        product = db.table("products").select("content").eq("id", query_id).eq("owner_id", int(owner_id)).single().execute()
        if product.data:
            old_content = product.data.get("content", "")
            items = [i.strip() for i in new_content.replace(",", "\n").split("\n") if i.strip()]
            updated_content = (old_content + ("\n" if old_content else "") + "\n".join(items)).strip()
            db.table("products").update({"content": updated_content}).eq("id", query_id).execute()
            return len(items)
    except Exception as e:
        print(f"Error: {e}")
    return 0

async def get_stock_count(product_id):
    try:
        query_id = int(product_id) if str(product_id).isdigit() else product_id
        product = db.table("products").select("content").eq("id", query_id).single().execute()
        if not product.data or not product.data.get("content"):
            return 0
        return len([i for i in product.data["content"].split("\n") if i.strip()])
    except:
        return 0

async def delete_product(product_id, owner_id: int):
    query_id = int(product_id) if str(product_id).isdigit() else product_id
    try:
        db.table("orders").delete().eq("product_id", query_id).execute()
        db.table("products").delete().eq("id", query_id).eq("owner_id", int(owner_id)).execute()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def confirm_order(order_id: str):
    order_res = db.table("orders").select("*").eq("id", order_id).single().execute()
    if not order_res.data:
        return None
    
    order = order_res.data
    p_id = order["product_id"]
    query_id = int(p_id) if str(p_id).isdigit() else p_id
    
    product_res = db.table("products").select("content").eq("id", query_id).single().execute()
    if not product_res.data:
        return None
        
    content = product_res.data.get("content", "")
    items = [i for i in content.split("\n") if i.strip()]
    
    if not items:
        return "sold_out"

    item_to_send = items[0]
    remaining_content = "\n".join(items[1:])
    
    db.table("products").update({"content": remaining_content}).eq("id", query_id).execute()
    db.table("orders").update({"status": "completed"}).eq("id", order_id).execute()
    
    return item_to_send

async def create_order(buyer_id: int, product_id, seller_id: int):
    query_id = int(product_id) if str(product_id).isdigit() else product_id
    data = {
        "buyer_id": buyer_id,
        "product_id": query_id,
        "seller_id": int(seller_id),
        "status": "pending"
    }
    response = db.table("orders").insert(data).execute()
    return response.data[0] if response.data else None

async def get_shop_customers(seller_id: int):
    response = db.table("orders").select("buyer_id").eq("seller_id", int(seller_id)).execute()
    if response.data:
        return list(set(item['buyer_id'] for item in response.data))
    return []
