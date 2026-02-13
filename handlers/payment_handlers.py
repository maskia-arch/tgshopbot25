from aiogram import Router, types, F
from services.db_service import get_user_by_id
from services.subscription import activate_pro_subscription
from config import Config
from core.strings import Buttons, Messages

router = Router()

@router.message(F.text == Buttons.UPGRADE_PRO)
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
    wallet = "ltc1q73t84vd9mj4yt2pkgmtx8cfmductgf8ds87dm5"
    
    confirm_kb = [
        [types.InlineKeyboardButton(
            text=f"✅ Zahlung bestätigen (ID: {callback.from_user.id})", 
            callback_data=f"admin_confirm_pro_{callback.from_user.id}"
        )]
    ]
    
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
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=confirm_kb),
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

@router.callback_query(F.data.startswith("admin_confirm_pro_"))
async def process_admin_confirm_pro(callback: types.CallbackQuery):
    if callback.from_user.id not in Config.ADMIN_IDS:
        await callback.answer("Keine Berechtigung.", show_alert=True)
        return

    target_id = int(callback.data.split("_")[-1])
    
    try:
        await activate_pro_subscription(target_id)
        
        await callback.message.edit_text(
            f"{callback.message.text}\n\n✅ **Bestätigt! User {target_id} ist jetzt PRO.**",
            parse_mode="Markdown"
        )
        
        await callback.bot.send_message(
            target_id, 
            f"🎉 Dein Upgrade auf **{Config.BRAND_NAME} Pro** wurde soeben aktiviert!\n"
            "Du kannst jetzt unbegrenzt Produkte anlegen und deinen eigenen Bot-Token nutzen."
        )
        await callback.answer("User erfolgreich freigeschaltet!")
        
    except Exception as e:
        await callback.answer(f"Fehler: {e}", show_alert=True)

@router.callback_query(F.data == "pay_fiat")
async def pay_fiat_info(callback: types.CallbackQuery):
    await callback.message.answer(
        "Für alternative Zahlungsmethoden (PayPal, Kreditkarte) kontaktiere bitte unseren Support direkt.\n\n"
        "Schreibe dazu einfach an den Admin."
    )
    await callback.answer()
