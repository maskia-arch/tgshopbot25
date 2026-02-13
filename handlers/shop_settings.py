from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.db_service import get_user_by_id, update_user_token

router = Router()

# Definition der Zustände für die Token-Eingabe
class TokenForm(StatesGroup):
    waiting_for_token = State()

@router.message(F.text == "⚙️ Shop-Bot konfigurieren")
async def start_token_config(message: types.Message, state: FSMContext):
    """Startet den Prozess der Token-Hinterlegung für Pro-User."""
    user = await get_user_by_id(message.from_user.id)
    
    # Sicherheitscheck: Nur Pro-User dürfen konfigurieren
    if not user or not user.get("is_pro"):
        await message.answer(
            "⚠️ **Feature gesperrt**\n\n"
            "Das Hinterlegen eines eigenen Bot-Tokens ist ein 💎 **PRO-Feature**.\n"
            "Bitte führe zuerst ein Upgrade durch.",
            parse_mode="Markdown"
        )
        return

    current_token = user.get("custom_bot_token")
    token_display = f"`{current_token[:10]}...`" if current_token else "`Keiner hinterlegt`"

    await state.set_state(TokenForm.waiting_for_token)
    
    kb = [[types.KeyboardButton(text="🏠 Hauptmenü")]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer(
        f"🛠 **Shop-Bot Konfiguration**\n\n"
        f"Aktueller Status: {token_display}\n\n"
        "Bitte sende mir jetzt den **API-Token** deines Bots.\n"
        "Diesen erhältst du beim @BotFather.\n\n"
        "💡 _Dein Shop wird nach dem Speichern automatisch über diesen Bot erreichbar sein._",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.message(TokenForm.waiting_for_token)
async def process_token(message: types.Message, state: FSMContext):
    """Verarbeitet den eingesendeten Token und speichert ihn in der DB."""
    # Falls der User das Hauptmenü wählt, brechen wir ab
    if message.text == "🏠 Hauptmenü":
        await state.clear()
        return

    token = message.text.strip()
    
    # Validierung: Ein Telegram Token hat immer ein ':' und eine gewisse Länge
    if ":" not in token or len(token) < 30:
        await message.answer(
            "❌ **Ungültiger Token**\n\n"
            "Das Format scheint nicht korrekt zu sein. Ein Bot-Token sieht etwa so aus:\n"
            "`123456789:ABCDefghIJKLmnop...`",
            parse_mode="Markdown"
        )
        return

    # In der Datenbank speichern
    try:
        await update_user_token(message.from_user.id, token)
        await state.clear()
        
        await message.answer(
            "✅ **Token erfolgreich gespeichert!**\n\n"
            "Dein eigener Shop-Bot wird nun vom System gestartet.\n"
            "Du kannst deine Produkte weiterhin hier im Admin-Panel verwalten.",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(f"❌ Fehler beim Speichern: {e}")

