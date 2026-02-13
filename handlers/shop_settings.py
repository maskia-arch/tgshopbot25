from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.db_service import get_user_by_id, update_user_token, update_payment_methods
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

class ShopSettingsForm(StatesGroup):
    waiting_for_token = State()
    waiting_for_wallet = State()

@router.message(F.text == "⚙️ Shop-Einstellungen / Zahlungsarten")
@router.message(F.text == "⚙️ Shop-Bot konfigurieren")
async def show_settings_menu(message: types.Message):
    user = await get_user_by_id(message.from_user.id)
    if not user: return

    is_pro = user.get("is_pro", False)
    
    text = (
        "⚙️ **Shop-Einstellungen**\n\n"
        "Hier kannst du deine Zahlungsdaten hinterlegen, damit Kunden direkt an dich bezahlen.\n\n"
        "**Verfügbare Methoden:**\n"
        f"• BTC: `{user.get('wallet_btc') or 'Nicht hinterlegt'}`\n"
        f"• LTC: `{user.get('wallet_ltc') or 'Nicht hinterlegt'}`\n"
    )

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Bitcoin (BTC) ändern", callback_data="set_pay_wallet_btc"))
    builder.row(types.InlineKeyboardButton(text="Litecoin (LTC) ändern", callback_data="set_pay_wallet_ltc"))

    if is_pro:
        text += (
            f"• ETH: `{user.get('wallet_eth') or 'Nicht hinterlegt'}`\n"
            f"• SOL: `{user.get('wallet_sol') or 'Nicht hinterlegt'}`\n"
            f"• PayPal: `{user.get('paypal_email') or 'Nicht hinterlegt'}`\n"
        )
        builder.row(types.InlineKeyboardButton(text="Ethereum (ETH) ändern", callback_data="set_pay_wallet_eth"))
        builder.row(types.InlineKeyboardButton(text="Solana (SOL) ändern", callback_data="set_pay_wallet_sol"))
        builder.row(types.InlineKeyboardButton(text="PayPal (F&F) ändern", callback_data="set_pay_paypal_email"))
        builder.row(types.InlineKeyboardButton(text="🤖 Eigener Bot-Token", callback_data="start_token_config"))
    else:
        text += "\n💎 _Upgrade auf PRO für ETH, SOL, PayPal & eigenen Bot-Token._"

    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("set_pay_"))
async def start_wallet_update(callback: types.CallbackQuery, state: FSMContext):
    field = callback.data.replace("set_pay_", "")
    names = {"wallet_btc": "Bitcoin (BTC)", "wallet_ltc": "Litecoin (LTC)", "wallet_eth": "Ethereum (ETH)", "wallet_sol": "Solana (SOL)", "paypal_email": "PayPal (F&F) Email"}
    
    await state.update_data(current_field=field)
    await state.set_state(ShopSettingsForm.waiting_for_wallet)
    
    await callback.message.answer(f"Bitte sende mir jetzt deine Adresse/Email für **{names.get(field)}**:")
    await callback.answer()

@router.message(ShopSettingsForm.waiting_for_wallet)
async def process_wallet_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("current_field")
    value = message.text.strip()

    if message.text == "🏠 Hauptmenü":
        await state.clear()
        return

    try:
        await update_payment_methods(message.from_user.id, {field: value})
        await state.clear()
        await message.answer(f"✅ **Gespeichert!** Deine Zahlungsdaten wurden aktualisiert.")
    except Exception as e:
        await message.answer(f"❌ Fehler: {e}")

@router.callback_query(F.data == "start_token_config")
async def start_token_config(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ShopSettingsForm.waiting_for_token)
    await callback.message.answer("Bitte sende mir jetzt den **API-Token** deines Bots (vom @BotFather):")
    await callback.answer()

@router.message(ShopSettingsForm.waiting_for_token)
async def process_token(message: types.Message, state: FSMContext):
    if message.text == "🏠 Hauptmenü":
        await state.clear()
        return

    token = message.text.strip()
    if ":" not in token or len(token) < 30:
        await message.answer("❌ Ungültiger Token-Format.")
        return

    try:
        await update_user_token(message.from_user.id, token)
        await state.clear()
        await message.answer("✅ **Token erfolgreich gespeichert!**")
    except Exception as e:
        await message.answer(f"❌ Fehler: {e}")
