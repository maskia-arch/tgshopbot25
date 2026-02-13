from core.supabase_client import db

async def get_active_pro_users():
    """Holt alle User, die ein aktives PRO-Abo haben."""
    response = db.table("profiles").select("*").eq("is_pro", True).execute()
    return response.data

async def get_user_by_id(telegram_id: int):
    """Sucht einen User anhand seiner Telegram-ID."""
    response = db.table("profiles").select("*").eq("id", telegram_id).execute()
    return response.data[0] if response.data else None

async def create_new_user(telegram_id: int, username: str):
    """Erstellt ein neues Profil, falls es noch nicht existiert."""
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
    """Speichert den individuellen Bot-Token eines PRO-Users."""
    db.table("profiles").update({"custom_bot_token": token}).eq("id", telegram_id).execute()

async def get_user_products(owner_id: int):
    """Listet alle Produkte eines bestimmten Besitzers auf."""
    response = db.table("products").select("*").eq("owner_id", owner_id).execute()
    return response.data

async def add_product(owner_id: int, name: str, price: float, content: str, description: str = ""):
    """Erstellt ein Produkt. Content (Lagerbestand) ist nun optional."""
    clean_content = ""
    if content:
        # Bereinigt den Content: Entfernt Leerzeichen und teilt bei Komma oder Zeilenumbruch
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
    """Fügt neuen Lagerbestand zu einem bestehenden Produkt hinzu."""
    product = db.table("products").select("content").eq("id", product_id).eq("owner_id", owner_id).single().execute()
    if product.data:
        old_content = product.data.get("content", "")
        new_items = [i.strip() for i in new_content.replace(",", "\n").split("\n") if i.strip()]
        
        # Bestehenden Inhalt und neuen Inhalt zusammenführen
        updated_content = old_content + ("\n" if old_content else "") + "\n".join(new_items)
        updated_content = updated_content.strip()
        
        db.table("products").update({"content": updated_content}).eq("id", product_id).execute()
        return len(new_items)
    return 0

async def get_stock_count(product_id: int):
    """Gibt die Anzahl der aktuell verfügbaren Items zurück."""
    product = db.table("products").select("content").eq("id", product_id).single().execute()
    if not product.data or not product.data.get("content"):
        return 0
    # Filtert leere Zeilen, um die korrekte Anzahl zu erhalten
    return len([i for i in product.data["content"].split("\n") if i.strip()])

async def confirm_order(order_id: str):
    """Schließt eine Bestellung ab und entnimmt das erste Item aus dem Lager."""
    # 1. Order laden
    order_res = db.table("orders").select("*").eq("id", order_id).single().execute()
    if not order_res.data:
        return None
    
    order = order_res.data
    product_id = order["product_id"]
    
    # 2. Produkt laden
    product_res = db.table("products").select("content").eq("id", product_id).single().execute()
    if not product_res.data:
        return None
        
    content = product_res.data.get("content", "")
    items = [i for i in content.split("\n") if i.strip()]
    
    if not items:
        return "sold_out"

    # 3. Erstes Item nehmen und Rest zurückspeichern
    item_to_send = items[0]
    remaining_content = "\n".join(items[1:])
    
    db.table("products").update({"content": remaining_content}).eq("id", product_id).execute()
    db.table("orders").update({"status": "completed"}).eq("id", order_id).execute()
    
    return item_to_send

async def delete_product(product_id: str, owner_id: int):
    """Löscht ein Produkt permanent."""
    db.table("products").delete().eq("id", product_id).eq("owner_id", owner_id).execute()

async def create_order(buyer_id: int, product_id: str, seller_id: int):
    """Erstellt eine neue Bestellung mit Status 'pending'."""
    data = {
        "buyer_id": buyer_id,
        "product_id": product_id,
        "seller_id": seller_id,
        "status": "pending"
    }
    response = db.table("orders").insert(data).execute()
    return response.data[0] if response.data else None
