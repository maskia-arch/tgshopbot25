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
from bots.shop_logic import router as shop_logic_router
from handlers import (
    admin_router, 
    customer_router, 
    payment_router, 
    settings_router  # Neuer Router für Shop-Konfiguration
)
from services.db_service import get_active_pro_users

# 1. Webserver für Render (Health Check & Port Binding)
app = Flask(__name__)

@app.route('/')
def health():
    return "Own1Shop Multi-Tenant System is running", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 2. Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 3. Multi-Bot Management (Pro-Features)
async def start_customer_bots(main_dispatcher: Dispatcher):
    """Startet die individuellen Shop-Bots der Pro-User via eigenem Token."""
    active_shops = await get_active_pro_users()
    
    for shop in active_shops:
        token = shop.get("custom_bot_token")
        if token:
            try:
                customer_bot = Bot(
                    token=token,
                    default=DefaultBotProperties(parse_mode="HTML")
                )
                # Die externen Bots nutzen dieselbe Logik wie das Hauptsystem
                asyncio.create_task(main_dispatcher.start_polling(customer_bot))
                logger.info(f"✅ Externer Shop-Bot für User {shop['id']} gestartet.")
            except Exception as e:
                logger.error(f"❌ Fehler bei Bot-Token {token[:10]}...: {e}")

async def main():
    if not Config.MASTER_BOT_TOKEN:
        logger.error("MASTER_BOT_TOKEN nicht gefunden! Abbruch.")
        return

    # FSM Speicher für Zustände (Wichtig für Formulare/Admin)
    storage = MemoryStorage()

    # Master-Bot Instanz
    master_bot = Bot(
        token=Config.MASTER_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    
    # Zentraler Dispatcher für alle Nachrichten & Bots
    dp = Dispatcher(storage=storage)

    # --- Router Registrierung (Reihenfolge bestimmt Priorität) ---
    dp.include_router(admin_router)      # Admin-Menü, Produkte anlegen/löschen
    dp.include_router(settings_router)   # Token-Konfiguration & Shop-ID
    dp.include_router(payment_router)    # Upgrade-Logik
    dp.include_router(customer_router)   # Kaufprozess & Bestellungen
    dp.include_router(master_router)     # /start mit Deep-Linking Support
    dp.include_router(shop_logic_router) # Produktpräsentation für Kunden

    logger.info(f"Own1Shop Version {Config.VERSION} wird gestartet...")

    # Alte Webhooks löschen & wartende Updates ignorieren
    await master_bot.delete_webhook(drop_pending_updates=True)

    # Startet das Hosting für Pro-User (Eigene Bots)
    await start_customer_bots(dp)

    # Startet das Polling für den Haupt-Bot
    logger.info("Master-Bot Polling aktiv.")
    await dp.start_polling(master_bot)

if __name__ == "__main__":
    # Flask-Server für Render 'Live' Status
    threading.Thread(target=run_flask, daemon=True).start()
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("System wurde manuell beendet.")
