from core.supabase_client import db
from config import Config

async def can_add_product(telegram_id: int) -> bool:
    user_response = db.table("profiles").select("is_pro").eq("id", telegram_id).execute()
    
    if not user_response.data:
        return False
    
    user = user_response.data[0]
    
    if user.get("is_pro"):
        return True
    
    products_response = db.table("products").select("id", count="exact").eq("owner_id", telegram_id).execute()
    product_count = products_response.count if products_response.count is not None else 0
    
    return product_count < Config.FREE_PRODUCT_LIMIT
