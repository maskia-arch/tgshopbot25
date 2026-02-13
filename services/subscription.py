from datetime import datetime, timedelta, timezone
from core.supabase_client import db

async def check_subscription_status(telegram_id: int) -> bool:
    response = db.table("profiles").select("is_pro, expiry_date").eq("id", telegram_id).execute()
    if not response.data:
        return False
    
    user = response.data[0]
    if not user["is_pro"]:
        return False
        
    if user["expiry_date"]:
        expiry = datetime.fromisoformat(user["expiry_date"].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expiry:
            db.table("profiles").update({"is_pro": False}).eq("id", telegram_id).execute()
            return False
            
    return True

async def activate_pro_subscription(telegram_id: int, months: int = 1):
    now = datetime.now(timezone.utc)
    new_expiry = now + timedelta(days=30 * months)
    
    data = {
        "is_pro": True,
        "expiry_date": new_expiry.isoformat()
    }
    
    db.table("profiles").update(data).eq("id", telegram_id).execute()

async def cancel_subscription(telegram_id: int):
    db.table("profiles").update({"is_pro": False}).eq("id", telegram_id).execute()
