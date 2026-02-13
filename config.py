import os
from dotenv import load_dotenv

load_dotenv()

def get_version():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        version_path = os.path.join(base_dir, "version.txt")
        with open(version_path, "r") as f:
            return f.read().strip()
    except Exception:
        return "1.0.0"

class Config:
    BRAND_NAME = "Own1Shop"
    VERSION = get_version()
    
    MASTER_BOT_TOKEN = os.getenv("MASTER_BOT_TOKEN")
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    FREE_PRODUCT_LIMIT = 2
    PRO_SUBSCRIPTION_PRICE = 10.00
    
    ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
