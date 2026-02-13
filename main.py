import asyncio
import logging
import os
import threading
from flask import Flask
from aiogram import Bot, Dispatcher
from config import Config
from bots.master_bot import router as master_router
from bots.shop_logic import router as shop_router
from handlers import admin_router, customer_router, payment_router

# 1. Webserver für Render (Health Check)
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 2. Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    if not Config.MASTER_BOT_TOKEN:
        logger.error("MASTER_BOT_TOKEN nicht gefunden! Abbruch.")
        return

    bot = Bot(token=Config.MASTER_BOT_TOKEN)
    dp = Dispatcher()

    # Router registrieren
    dp.include_router(master_router)
    dp.include_router(shop_router)
    dp.include_router(admin_router)
    dp.include_router(customer_router)
    dp.include_router(payment_router)

    logger.info(f"Own1Shop Version {Config.VERSION} wird gestartet...")
    
    # Startet das Polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Flask-Server in einem separaten Thread starten
    threading.Thread(target=run_flask, daemon=True).start()
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Own1Shop wurde sicher beendet.")
