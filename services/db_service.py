import random
import string
from core.supabase_client import db

# --- HILFSFUNKTION FÜR SHOP-ID ---
def generate_unique_shop_id(length=6):
    """Generiert einen zufälligen Code wie 5ULG63."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# --- USER & SHOP MANAGEMENT ---

async def get_active_pro_users():
    """Holt alle User, die ein aktives PRO-Abo haben."""
    response = db.table("profiles").select("*").eq("is_pro", True).execute()
    return response.data

async def get_user_by_id(telegram_id: int):
    """
    Sucht einen User anhand seiner Telegram-ID.
    Generiert automatisch eine Shop-ID nach, falls diese fehlt.
    """
    response = db.table("profiles").select("*").eq("id", telegram_id).execute()
    if response.data:
        user = response.data[0]
        # Falls Altnutzer noch keine Shop-ID haben, hier nachgenerieren
        if not user.get("shop_id"):
            new_id = generate_unique_shop_id()
            db.table("profiles").update({"shop_id": new_id}).eq("id", telegram_id).execute()
            user["shop_id"] = new_id
        return user
    return None

async def get_user_by_shop_id(shop_id: str):
    """Sucht den Besitzer eines Shops anhand der Shop-ID."""
    response = db.table("profiles").select("*").eq("shop_id", shop_id.upper()).execute()
    return response.data[0] if response.data else None

async def create_new_user(telegram_id: int, username: str):
    """Erstellt ein neues Profil inklusive eindeutiger Shop-ID."""
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
    """Speichert den individuellen Bot-Token eines PRO-Users."""
    db.table("profiles").update({"custom_bot_token": token}).eq("id", telegram_id).execute()

# --- PRODUKT MANAGEMENT ---

async def get_user_products(owner_id: int):
    """Listet alle Produkte eines Besitzers auf."""
    try:
        # Explizites Casting zu int, um PGRST204 Fehler zu vermeiden
        response = db.table("products").select("*").eq("owner_id", int(owner_id)).execute()
        return response.data
    except Exception as e:
        print(f"Fehler beim Laden der Produkte: {e}")
        return []

async def add_product(owner_id: int, name: str, price: float, content: str, description: str = ""):
    """Erstellt ein Produkt mit optionalem Lagerbestand."""
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

async def refill_stock(product_id: int, owner_id: int, new_content: str):
    """Fügt neuen Lagerbestand hinzu. Wichtig für den 'Lager auffüllen' Button."""
    try:
        product = db.table("products").select("content").eq("id", int(product_id)).eq("owner_id", int(owner_id)).single().execute()
        if product.data:
            old_content = product.data.get("content", "")
            new_items = [i.strip() for i in new_content.replace(",", "\n").split("\n") if i.strip()]
            
            updated_content = old_content + ("\n" if old_content else "") + "\n".join(new_items)
            updated_content = updated_content.strip()
            
            db.table("products").update({"content": updated_content}).eq("id", int(product_id)).execute()
            return len(new_items)
    except Exception as e:
        print(f"Fehler beim Lager auffüllen: {e}")
    return 0

async def get_stock_count(product_id: int):
    """Gibt die Anzahl der verfügbaren Items zurück."""
    try:
        product = db.table("products").select("content").eq("id", int(product_id)).single().execute()
        if not product.data or not product.data.get("content"):
            return 0
        return len([i for i in product.data["content"].split("\n") if i.strip()])
    except:
        return 0

async def delete_product(product_id: int, owner_id: int):
    """Löscht ein Produkt permanent. Nutzt explizites Casting für Supabase."""
    db.table("products").delete().eq("id", int(product_id)).eq("owner_id", int(owner_id)).execute()

# --- BESTELLMANAGEMENT ---

async def confirm_order(order_id: str):
    """Schließt Bestellung ab und liefert Ware aus."""
    order_res = db.table("orders").select("*").eq("id", order_id).single().execute()
    if not order_res.data:
        return None
    
    order = order_res.data
    product_id = order["product_id"]
    
    product_res = db.table("products").select("content").eq("id", int(product_id)).single().execute()
    if not product_res.data:
        return None
        
    content = product_res.data.get("content", "")
    items = [i for i in content.split("\n") if i.strip()]
    
    if not items:
        return "sold_out"

    item_to_send = items[0]
    remaining_content = "\n".join(items[1:])
    
    db.table("products").update({"content": remaining_content}).eq("id", int(product_id)).execute()
    db.table("orders").update({"status": "completed"}).eq("id", order_id).execute()
    
    return item_to_send

async def create_order(buyer_id: int, product_id: int, seller_id: int):
    """Erstellt eine neue Bestellung."""
    data = {
        "buyer_id": buyer_id,
        "product_id": int(product_id),
        "seller_id": int(seller_id),
        "status": "pending"
    }
    response = db.table("orders").insert(data).execute()
    return response.data[0] if response.data else None
