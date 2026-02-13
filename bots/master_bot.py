from aiogram import Router, types, F
from aiogram.filters import CommandStart, CommandObject
from config import Config
from services.db_service import create_new_user, get_user_by_id, get_user_by_shop_id
from handlers.customer_handlers import show_shop_catalog
from core.strings import Buttons, Messages

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    args = command.args

    # 1. DEEP-LINK LOGIK: Prüft, ob ein Shop-Code in der URL übergeben wurde
    if args:
        shop_owner = await get_user_by_shop_id(args)
        if shop_owner:
            owner_name = shop_owner.get("username", "Unbekannt")
            
            kb = [[types.KeyboardButton(text=Buttons.MAIN_MENU)]]
            keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
            
            await message.answer(
                Messages.SHOP_WELCOME.format(owner_name=owner_name),
                reply_markup=keyboard
            )
            
            await show_shop_catalog(message, shop_owner['id'])
            return
        else:
            await message.answer("❌ Dieser Shop-Code ist leider ungültig oder existiert nicht mehr.")
            return

    # 2. NUTZER REGISTRIEREN / LADEN: Verhindert "Status: Keine" durch DB-Abfrage
    await create_new_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "User"
    )
    
    user = await get_user_by_id(message.from_user.id)
    is_pro = user.get("is_pro", False)
    shop_id = user.get("shop_id", "N/A")
    status_text = "💎 PRO" if is_pro else "🆓 Kostenlos"

    bot_info = await message.bot.get_me()
    # WICHTIG: https:// ist zwingend erforderlich, damit Telegram den Parameter erkennt
    shop_link = f"https://t.me/{bot_info.username}?start={shop_id}"

    # Dashboard-Text nutzt nun die echten Daten aus der Datenbank
    welcome_text = (
        f"{Messages.WELCOME_BACK.format(status=status_text, shop_id=shop_id)}\n\n"
        f"🔗 **Dein persönlicher Shop-Link:**\n"
        f"`{shop_link}`\n\n"
        "Verwalte hier deine Produkte oder schalte die Pro-Funktionen frei."
    )
    
    kb = [
        [types.KeyboardButton(text=Buttons.ADMIN_MANAGE)],
        [types.KeyboardButton(text=Buttons.VIEW_SHOP)]
    ]
    
    if is_pro:
        kb.insert(1, [types.KeyboardButton(text=Buttons.CONF_BOT)])
    else:
        kb.insert(1, [types.KeyboardButton(text=Buttons.UPGRADE_PRO)])
        
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@router.message(F.text == Buttons.VIEW_SHOP)
async def view_own_shop(message: types.Message):
    user = await get_user_by_id(message.from_user.id)
    if user:
        await message.answer("👀 **Vorschau deines Shops aus Kundensicht:**")
        await show_shop_catalog(message, user['id'])

@router.message(F.text == Buttons.MAIN_MENU)
async def main_menu(message: types.Message):
    # Simuliert einen Start ohne Argumente für die Dashboard-Anzeige
    await cmd_start(message, CommandObject(args=None))
