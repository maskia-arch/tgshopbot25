from aiogram import Router, types, F
from aiogram.filters import CommandStart
from config import Config
from services.db_service import create_new_user, get_user_by_id

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """
    Haupt-Einstiegspunkt des Bots. Registriert den User und zeigt das 
    entsprechende Menü basierend auf dem PRO-Status an.
    """
    # User in DB anlegen falls nicht vorhanden
    await create_new_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "User"
    )
    
    # User-Daten abrufen um PRO-Status zu prüfen
    user = await get_user_by_id(message.from_user.id)
    is_pro = user.get("is_pro") if user else False

    welcome_text = (
        f"Willkommen bei **{Config.BRAND_NAME}**! 🚀\n\n"
        "Hier kannst du deinen eigenen Shop-Bot erstellen und digitale Güter verkaufen.\n\n"
        "**Deine Möglichkeiten:**\n"
        "• Kostenlos: Bis zu 2 Produkte listen (Test-Modus)\n"
        "• Pro: Unbegrenzt Produkte & eigener Bot-Token\n\n"
        f"Dein Status: {'💎 PRO' if is_pro else '🆓 Kostenlos'}\n"
        f"Version: {Config.VERSION}"
    )
    
    # Standard-Buttons (für alle sichtbar)
    kb = [
        [types.KeyboardButton(text="🛒 Meinen Test-Shop verwalten")],
        [types.KeyboardButton(text="🛍 Shop durchsuchen")]
    ]
    
    # Bedingte Buttons basierend auf PRO-Status
    if is_pro:
        # PRO-User können ihren Shop konfigurieren
        kb.insert(1, [types.KeyboardButton(text="⚙️ Shop-Bot konfigurieren")])
    else:
        # Kostenlose User sehen die Upgrade-Option
        kb.insert(1, [types.KeyboardButton(text="💎 Upgrade auf Pro (10€/Monat)")])
        
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@router.message(F.text == "🏠 Hauptmenü")
async def main_menu(message: types.Message):
    """Einfacher Handler um zum Startmenü zurückzukehren."""
    await cmd_start(message)
