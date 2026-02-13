import asyncio
import logging
import os
import threading
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from config import Config

# Router Imports
from bots.master_bot import router as master_router
from bots.shop_logic import router as shop_router
from handlers import admin_router, customer_router, payment_router
from services.db_service import get_active_pro_users

# 1. Webserver für Render (Health Check & Port Binding)
app = Flask(__name__)

@app.route('/')
def health():
    return "Own1Shop Multi-Bot System is running", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 2. Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 3. Multi-Bot Management
async def start_customer_bots(main_dispatcher: Dispatcher):
    """Startet die individuellen Shop-Bots der Pro-User."""
    active_shops = await get_active_pro_users()
    
    for shop in active_shops:
        token = shop.get("custom_bot_token")
        if token:
            try:
                # Erstelle eine neue Bot-Instanz für den User-Token
                customer_bot = Bot(
                    token=token,
                    default=DefaultBotProperties(parse_mode="HTML")
                )
                # Wir registrieren den Bot im Dispatcher, damit er auf dieselbe Logik hört
                # Das ermöglicht es, dass ein Admin-Panel viele Bots steuert
                asyncio.create_task(main_dispatcher.start_polling(customer_bot))
                logger.info(f"✅ Shop-Bot für User {shop['id']} erfolgreich gestartet.")
            except Exception as e:
                logger.error(f"❌ Fehler beim Starten des Bots für Token {token[:10]}...: {e}")

async def main():
    if not Config.MASTER_BOT_TOKEN:
        logger.error("MASTER_BOT_TOKEN nicht gefunden! Abbruch.")
        return

    # FSM Speicher initialisieren
    storage = MemoryStorage()

    # Master-Bot Instanz (Das Admin-Panel)
    master_bot = Bot(
        token=Config.MASTER_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    
    # Zentraler Dispatcher
    dp = Dispatcher(storage=storage)

    # Router registrieren (Priorität beachten)
    dp.include_router(admin_router)     # Produktverwaltung & Admin-Funktionen
    dp.include_router(payment_router)   # Upgrade & Zahlungslogik
    dp.include_router(customer_router)  # Kunden-Interaktion (Kaufen/Bestand)
    dp.include_router(master_router)    # Hauptmenü des Master-Bots
    dp.include_router(shop_router)      # Allgemeine Logik für User-Shops

    logger.info(f"Own1Shop Version {Config.VERSION} initialisiert.")

    # Bereinigung alter Nachrichten
    await master_bot.delete_webhook(drop_pending_updates=True)

    # --- PRO-LOGIK: Startet alle eigenen Bots der Verkäufer ---
    # Dies macht den Master-Bot zum Dashboard für viele Unter-Bots
    await start_customer_bots(dp)

    # Startet das Polling für den Master-Bot
    logger.info("Master-Bot Polling gestartet...")
    await dp.start_polling(master_bot)

if __name__ == "__main__":
    # Flask-Server in separatem Thread (für Render.com Status 'Live')
    threading.Thread(target=run_flask, daemon=True).start()
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Own1Shop wurde sicher beendet.")
