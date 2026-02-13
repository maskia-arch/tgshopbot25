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

async def get_user_products(owner_id: int):
    response = db.table("products").select("*").eq("owner_id", owner_id).execute()
    return response.data

async def add_product(owner_id: int, name: str, price: float, content: str, description: str = ""):
    # Bereinigt den Content: Entfernt Leerzeichen und teilt bei Komma oder Zeilenumbruch
    # Speichert alles sauber untereinander
    items = [i.strip() for i in content.replace(",", "\n").split("\n") if i.strip()]
    clean_content = "\n".join(items)
    
    data = {
        "owner_id": owner_id,
        "name": name,
        "price": price,
        "content": clean_content,
        "description": description
    }
    db.table("products").insert(data).execute()

async def refill_stock(product_id: int, owner_id: int, new_content: str):
    # Holt alten Bestand
    product = db.table("products").select("content").eq("id", product_id).eq("owner_id", owner_id).single().execute()
    if product.data:
        old_content = product.data.get("content", "")
        items = [i.strip() for i in new_content.replace(",", "\n").split("\n") if i.strip()]
        updated_content = (old_content + "\n" + "\n".join(items)).strip()
        
        db.table("products").update({"content": updated_content}).eq("id", product_id).execute()
        return len(items)
    return 0

async def get_stock_count(product_id: int):
    product = db.table("products").select("content").eq("id", product_id).single().execute()
    if not product.data or not product.data.get("content"):
        return 0
    return len(product.data["content"].split("\n"))

async def confirm_order(order_id: str):
    # 1. Order laden
    order_res = db.table("orders").select("*").eq("id", order_id).single().execute()
    if not order_res.data:
        return None
    
    order = order_res.data
    product_id = order["product_id"]
    
    # 2. Produkt laden und ein Item entnehmen
    product_res = db.table("products").select("content").eq("id", product_id).single().execute()
    content = product_res.data.get("content", "")
    
    if not content:
        return "sold_out"

    items = content.split("\n")
    item_to_send = items[0] # Das erste Item nehmen
    remaining_content = "\n".join(items[1:]) # Rest zurückspeichern
    
    # 3. DB Update: Bestand reduzieren & Order abschließen
    db.table("products").update({"content": remaining_content}).eq("id", product_id).execute()
    db.table("orders").update({"status": "completed"}).eq("id", order_id).execute()
    
    return item_to_send

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
