from aiogram import Router, types, F
from aiogram.filters import Command  # <--- DIESE ZEILE HAT GEFEHLT!
from services.db_service import get_user_by_id
from services.subscription import activate_pro_subscription
from config import Config

router = Router()

@router.message(F.text == "💎 Upgrade auf Pro (10€/Monat)")
async def show_upgrade_options(message: types.Message):
    user = await get_user_by_id(message.from_user.id)
    
    if user and user.get("is_pro"):
        await message.answer(f"Du nutzt bereits die Pro-Version von {Config.BRAND_NAME}! ✨")
        return

    text = (
        f"🚀 **Upgrade auf {Config.BRAND_NAME} Pro**\n\n"
        "Deine Vorteile:\n"
        "✅ Unbegrenzt viele Produkte anlegen\n"
        "✅ Eigenes Branding (Kein 'Powered by')\n"
        "✅ Statistiken und Prioritäts-Support\n\n"
        f"Preis: **{Config.PRO_SUBSCRIPTION_PRICE}€ / Monat**\n\n"
        "Bitte wähle eine Zahlungsmethode:"
    )
    
    kb = [
        [types.InlineKeyboardButton(text="Litecoin (LTC)", callback_data="pay_ltc")],
        [types.InlineKeyboardButton(text="PayPal / Kreditkarte", callback_data="pay_fiat")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "pay_ltc")
async def pay_ltc_info(callback: types.CallbackQuery):
    wallet_address = "DEINE_LTC_WALLET_ADRESSE"
    
    await callback.message.answer(
        f"Sende LTC im Wert von **{Config.PRO_SUBSCRIPTION_PRICE}€** an folgende Adresse:\n\n"
        f"`{wallet_address}`\n\n"
        "Sende nach der Transaktion bitte einen Screenshot des Belegs an den Support.",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(Command("grantpro"))
async def admin_grant_pro(message: types.Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Nutze: /grantpro [Telegram_ID]")
        return

    try:
        target_id = int(args[1])
        await activate_pro_subscription(target_id)
        await message.answer(f"✅ User {target_id} wurde für 30 Tage auf PRO gesetzt.")
        
        try:
            await message.bot.send_message(
                target_id, 
                f"🎉 Dein Upgrade auf **{Config.BRAND_NAME} Pro** wurde aktiviert!"
            )
        except Exception:
            await message.answer("User wurde geupgradet, konnte aber nicht benachrichtigt werden.")
            
    except ValueError:
        await message.answer("Fehler: Die Telegram_ID muss eine Zahl sein.")
    except Exception as e:
        await message.answer(f"Fehler: {e}")
