from aiogram import Router, types, F
from aiogram.filters import Command
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
        "✅ Eigenes Branding (Eigener Bot-Token)\n"
        "✅ Prioritäts-Support & mehr\n\n"
        f"Preis: **{Config.PRO_SUBSCRIPTION_PRICE}€ / Monat**\n\n"
        "Bitte wähle eine Zahlungsmethode:"
    )
    
    kb = [
        [types.InlineKeyboardButton(text="Litecoin (LTC)", callback_data="pay_ltc")],
        [types.InlineKeyboardButton(text="Andere Methoden (Support)", callback_data="pay_fiat")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "pay_ltc")
async def pay_ltc_info(callback: types.CallbackQuery):
    # Deine hinterlegte Adresse
    wallet = "ltc1q73t84vd9mj4yt2pkgmtx8cfmductgf8ds87dm5"
    
    # Benachrichtigung an den Admin (Dich) über das Interesse
    for admin_id in Config.ADMIN_IDS:
        try:
            await callback.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"🔔 **Kaufinteresse Pro-Version**\n\n"
                    f"User: @{callback.from_user.username or 'Kein Username'}\n"
                    f"ID: `{callback.from_user.id}`\n"
                    f"Hat soeben die LTC-Zahlungsdaten angefordert."
                ),
                parse_mode="Markdown"
            )
        except Exception:
            continue

    await callback.message.answer(
        f"📥 **Zahlung via Litecoin (LTC)**\n\n"
        f"Sende LTC im Wert von **{Config.PRO_SUBSCRIPTION_PRICE}€** an folgende Adresse:\n\n"
        f"`{wallet}`\n\n"
        "⚠️ **Wichtig:** Sende nach der Transaktion bitte einen Screenshot des Belegs an den Support.\n"
        "Sobald die Zahlung bestätigt ist, schalten wir deinen Account manuell frei.",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "pay_fiat")
async def pay_fiat_info(callback: types.CallbackQuery):
    await callback.message.answer(
        "Für alternative Zahlungsmethoden (PayPal, Kreditkarte) kontaktiere bitte unseren Support direkt.\n\n"
        "Schreibe dazu einfach an den Admin."
    )
    await callback.answer()

@router.message(Command("grantpro"))
async def admin_grant_pro(message: types.Message):
    """Admin-Befehl um User manuell freizuschalten."""
    if message.from_user.id not in Config.ADMIN_IDS:
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Nutze: `/grantpro [Telegram_ID]`", parse_mode="Markdown")
        return

    try:
        target_id = int(args[1])
        # Funktion aus subscription.py
        await activate_pro_subscription(target_id)
        
        await message.answer(f"✅ User `{target_id}` wurde erfolgreich auf PRO gesetzt.", parse_mode="Markdown")
        
        # Benachrichtigung an den Kunden
        try:
            await message.bot.send_message(
                target_id, 
                f"🎉 Dein Upgrade auf **{Config.BRAND_NAME} Pro** wurde soeben aktiviert!\n"
                "Du kannst jetzt unbegrenzt Produkte anlegen und deinen eigenen Bot-Token nutzen."
            )
        except Exception:
            await message.answer("User wurde geupgradet, konnte aber nicht benachrichtigt werden (Bot geblockt?).")
            
    except ValueError:
        await message.answer("Fehler: Die Telegram_ID muss eine Zahl sein.")
    except Exception as e:
        await message.answer(f"Fehler: {e}")
