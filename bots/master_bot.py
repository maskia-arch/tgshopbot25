from aiogram import Router, types, F
from aiogram.filters import CommandStart, CommandObject
from config import Config
from services.db_service import create_new_user, get_user_by_id, get_user_by_shop_id

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    """
    Haupt-Einstiegspunkt des Bots. Unterstützt Deep-Linking (z.B. /start 5ULG63).
    """
    args = command.args  # Holt den Code nach dem /start (z.B. 5ULG63)

    # 1. FALL: Nutzer nutzt einen Shop-Link eines Verkäufers
    if args:
        shop_owner = await get_user_by_shop_id(args)
        if shop_owner:
            # Hier leiten wir den User in die Shop-Ansicht des Verkäufers
            # Wir nutzen den Benutzernamen des Shop-Besitzers für die Begrüßung
            owner_name = shop_owner.get("username", "Unbekannt")
            
            kb = [[types.KeyboardButton(text="🏠 Hauptmenü")]]
            keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
            
            await message.answer(
                f"🏪 **Willkommen im Shop von {owner_name}**\n\n"
                "Hier kannst du die verfügbaren Produkte durchstöbern und sicher einkaufen.",
                reply_markup=keyboard
            )
            
            # TRIGGERE HIER DEN SHOP-FLOW (customer_handlers)
            # Wir "faken" hier quasi den Klick auf "🛍 Shop durchsuchen" für diesen speziellen Shop
            from handlers.customer_handlers import show_products_for_shop
            await show_products_for_shop(message, shop_owner['id'])
            return
        else:
            await message.answer("❌ Dieser Shop-Code ist leider ungültig oder existiert nicht mehr.")
            # Danach normaler Start fortsetzen

    # 2. FALL: Normaler Start des Bots (Dashboard für Verkäufer)
    await create_new_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "User"
    )
    
    user = await get_user_by_id(message.from_user.id)
    is_pro = user.get("is_pro") if user else False
    shop_id = user.get("shop_id", "N/A") if user else "N/A"

    welcome_text = (
        f"Willkommen bei **{Config.BRAND_NAME}**! 🚀\n\n"
        "Hier kannst du deinen eigenen Shop-Bot erstellen und digitale Güter verkaufen.\n\n"
        f"🔗 **Dein persönlicher Shop-Link:**\n"
        f"`t.me/{(await message.bot.get_me()).username}?start={shop_id}`\n\n"
        "**Deine Möglichkeiten:**\n"
        "• Kostenlos: Bis zu 2 Produkte & Test-Shop\n"
        "• Pro: Unbegrenzt Produkte & eigener Bot-Token\n\n"
        f"Status: {'💎 PRO' if is_pro else '🆓 Kostenlos'}\n"
        f"Shop-ID: `{shop_id}`"
    )
    
    kb = [
        [types.KeyboardButton(text="🛒 Meinen Test-Shop verwalten")],
        [types.KeyboardButton(text="🛍 Eigenen Shop ansehen")]
    ]
    
    if is_pro:
        kb.insert(1, [types.KeyboardButton(text="⚙️ Shop-Bot konfigurieren")])
    else:
        kb.insert(1, [types.KeyboardButton(text="💎 Upgrade auf Pro (10€/Monat)")])
        
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@router.message(F.text == "🛍 Eigenen Shop ansehen")
async def view_own_shop(message: types.Message):
    """Zeigt dem User seinen eigenen Shop aus Kundensicht."""
    user = await get_user_by_id(message.from_user.id)
    if user and user.get("shop_id"):
        # Wir simulieren den Start mit der eigenen Shop-ID
        from aiogram.filters import CommandObject
        await cmd_start(message, CommandObject(args=user.get("shop_id")))

@router.message(F.text == "🏠 Hauptmenü")
async def main_menu(message: types.Message):
    """Einfacher Handler um zum Startmenü zurückzukehren."""
    # Wir erstellen ein leeres CommandObject für den normalen Start
    from aiogram.filters import CommandObject
    await cmd_start(message, CommandObject(args=None))
