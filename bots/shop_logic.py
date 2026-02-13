from aiogram import Router, types
from services.db_service import get_user_by_id
from config import Config

router = Router()

async def get_branding_text(owner_id: int):
    user = await get_user_by_id(owner_id)
    if user and user.get("is_pro"):
        return ""
    return f"\n\n—\n🤖 Powered by {Config.BRAND_NAME}"

@router.message()
async def universal_shop_handler(message: types.Message):
    # Diese Logik greift, wenn Nachrichten in den Kunden-Bots eingehen
    # Hier wird geprüft, ob der Shop-Besitzer Pro-Status hat
    
    # Beispiel für eine automatische Antwort mit Branding-Check:
    branding = await get_branding_text(message.from_user.id)
    
    if message.text == "/start":
        text = (
            "Willkommen in diesem Shop! 🛒\n"
            "Nutze die Buttons, um Produkte zu sehen."
            f"{branding}"
        )
        await message.answer(text)
