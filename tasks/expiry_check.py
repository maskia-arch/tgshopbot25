import asyncio
import logging
from datetime import datetime, timezone
from core.supabase_client import db

logger = logging.getLogger(__name__)

async def check_subscriptions():
    now = datetime.now(timezone.utc).isoformat()
    
    response = db.table("profiles") \
        .select("id, username, custom_bot_token") \
        .eq("is_pro", True) \
        .lt("expiry_date", now) \
        .execute()
    
    expired_users = response.data
    
    for user in expired_users:
        user_id = user["id"]
        
        db.table("profiles") \
            .update({"is_pro": False}) \
            .eq("id", user_id) \
            .execute()
            
        logger.info(f"Abo abgelaufen für User: {user_id} (@{user.get('username')})")

if __name__ == "__main__":
    asyncio.run(check_subscriptions())
