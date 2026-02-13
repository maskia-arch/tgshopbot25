import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import Config
from bots.master_bot import router as master_router
from bots.shop_logic import router as shop_router
from services.db_service import get_active_pro_users

# Logging für Render.com Logs konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def start_customer_bots(dp: Dispatcher):
    """Lädt alle aktiven Pro-Bots aus Supabase und startet sie."""
    active_shops = await get_active_pro_users()
    
    for shop in active_shops:
        token = shop.get("custom_bot_token")
        if token:
            try:
                customer_bot = Bot(token=token)
                # Wir nutzen denselben Router für alle Kunden-Bots
                # Die Unterscheidung erfolgt im Handler über die bot_id
                logger.info(f"Starte Kunden-Bot für User {shop['id']}...")
                # Hinweis: Bei vielen Bots empfiehlt sich hier ein Bot-Manager/Polling-Task
            except Exception as e:
                logger.error(f"Fehler beim Starten von Bot {token[:10]}...: {e}")

async def main():
    # 1. Master-Bot initialisieren
    if not Config.MASTER_BOT_TOKEN:
        logger.error("MASTER_BOT_TOKEN nicht gefunden! Abbruch.")
        return

    master_bot = Bot(token=Config.MASTER_BOT_TOKEN)
    dp = Dispatcher()

    # 2. Router registrieren
    dp.include_router(master_router) # Logik für deinen Own1Shop Bot
    dp.include_router(shop_router)   # Logik für die Shops der User

    logger.info(f"Own1Shop Version {Config.VERSION} wird gestartet...")

    # 3. Optionale Pro-Bots laden (für die Zukunft/Skalierung)
    # await start_customer_bots(dp)

    # 4. Polling starten
    # Der Master-Bot hört auf Nachrichten
    await dp.start_polling(master_bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Own1Shop wurde sicher beendet.")
