import asyncio
import logging
import os
import threading
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from config import Config

from bots.master_bot import router as master_router
from bots.shop_logic import router as shop_logic_router
from handlers import (
    admin_router, 
    customer_router, 
    payment_router, 
    settings_router,
    master_admin_router
)
from services.db_service import get_active_pro_users
from core.middlewares import ShopMiddleware

app = Flask(__name__)

@app.route('/')
def health():
    return "Own1Shop Multi-Tenant System is running", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def start_customer_bots(main_dispatcher: Dispatcher):
    active_shops = await get_active_pro_users()
    
    for shop in active_shops:
        token = shop.get("custom_bot_token")
        if token:
            try:
                customer_bot = Bot(
                    token=token,
                    default=DefaultBotProperties(parse_mode="HTML")
                )
                await customer_bot.delete_webhook(drop_pending_updates=True)
                await asyncio.sleep(0.5)
                asyncio.create_task(main_dispatcher.start_polling(customer_bot))
                logger.info(f"✅ Externer Shop-Bot für User {shop['id']} gestartet.")
            except Exception as e:
                logger.error(f"❌ Fehler bei Bot-Token {token[:10]}...: {e}")

async def main():
    if not Config.MASTER_BOT_TOKEN:
        logger.error("MASTER_BOT_TOKEN nicht gefunden! Abbruch.")
        return

    storage = MemoryStorage()

    master_bot = Bot(
        token=Config.MASTER_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    
    dp = Dispatcher(storage=storage)

    dp.message.middleware(ShopMiddleware())
    dp.callback_query.middleware(ShopMiddleware())

    dp.include_router(master_admin_router)
    dp.include_router(admin_router)
    dp.include_router(settings_router)
    dp.include_router(payment_router)
    dp.include_router(customer_router)
    dp.include_router(master_router)
    dp.include_router(shop_logic_router)

    logger.info(f"Own1Shop Version {Config.VERSION} wird gestartet...")

    await master_bot.delete_webhook(drop_pending_updates=True)
    await asyncio.sleep(2)

    await start_customer_bots(dp)

    logger.info("Master-Bot Polling aktiv.")
    await dp.start_polling(master_bot, skip_updates=True)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("System wurde manuell beendet.")
