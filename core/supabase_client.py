from supabase import create_client, Client
from config import Config

def get_supabase() -> Client:
    if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
        raise ValueError("Supabase URL oder Key fehlen in den Umgebungsvariablen!")
    
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

db = get_supabase()
