from aiogram import Router, types, F
from aiogram.filters import CommandStart, CommandObject
from config import Config
from services.db_service import create_new_user, get_user_by_id, get_user_by_shop_id
from handlers.customer_handlers import show_shop_catalog

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    args = command.args

    if args:
        shop_owner = await get_user_by_shop_id(args)
        if shop_owner:
            owner_name = shop_owner.get("username", "Unbekannt")
            
            kb = [[types.KeyboardButton(text="🏠 Hauptmenü")]]
            keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
            
            await message.answer(
                f"🏪 **Willkommen im Shop von {owner_name}**\n\n"
                "Hier kannst du die verfügbaren Produkte durchstöbern und sicher einkaufen.",
                reply_markup=keyboard
            )
            
            await show_shop_catalog(message, shop_owner['id'])
            return
        else:
            await message.answer("❌ Dieser Shop-Code ist leider ungültig oder existiert nicht mehr.")

    await create_new_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "User"
    )
    
    user = await get_user_by_id(message.from_user.id)
    is_pro = user.get("is_pro") if user else False
    shop_id = user.get("shop_id", "N/A") if user else "N/A"

    bot_info = await message.bot.get_me()
    shop_link = f"t.me/{bot_info.username}?start={shop_id}"

    welcome_text = (
        f"Willkommen bei **{Config.BRAND_NAME}**! 🚀\n\n"
        "Hier kannst du deinen eigenen Shop-Bot erstellen und digitale Güter verkaufen.\n\n"
        f"🔗 **Dein persönlicher Shop-Link:**\n"
        f"`{shop_link}`\n\n"
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
    user = await get_user_by_id(message.from_user.id)
    if user:
        await message.answer("👀 **Vorschau deines Shops aus Kundensicht:**")
        await show_shop_catalog(message, user['id'])

@router.message(F.text == "🏠 Hauptmenü")
async def main_menu(message: types.Message):
    from aiogram.filters import CommandObject
    await cmd_start(message, CommandObject(args=None))
