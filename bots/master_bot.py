from aiogram import Router, types, F
from aiogram.filters import CommandStart
from config import Config
from services.db_service import create_new_user, get_user_by_id

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await create_new_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "User"
    )
    
    welcome_text = (
        f"Willkommen bei **{Config.BRAND_NAME}**! 🚀\n\n"
        "Hier kannst du deinen eigenen Shop-Bot erstellen und digitale Güter verkaufen.\n\n"
        "**Deine Möglichkeiten:**\n"
        "• Kostenlos: Bis zu 2 Produkte listen\n"
        "• Pro: Unbegrenzt Produkte & eigenes Branding\n\n"
        f"Version: {Config.VERSION}"
    )
    
    kb = [
        [types.KeyboardButton(text="🛒 Meinen Test-Shop verwalten")],
        [types.KeyboardButton(text="💎 Upgrade auf Pro (10€/Monat)")],
        [types.KeyboardButton(text="🛍 Shop durchsuchen")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@router.message(F.text == "🏠 Hauptmenü")
async def main_menu(message: types.Message):
    await cmd_start(message)
