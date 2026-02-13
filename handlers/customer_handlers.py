from aiogram import Router, types, F
from services.db_service import get_user_products, create_order
from config import Config

router = Router()

@router.message(F.text == "🛍 Shop durchsuchen")
async def browse_shop(message: types.Message):
    # In einem realen Szenario müssten wir hier die owner_id des Shop-Besitzers kennen
    # Für den Test-Modus im Master-Bot nutzen wir die ID des Users selbst
    products = await get_user_products(message.from_user.id)
    
    if not products:
        await message.answer("Dieser Shop hat aktuell keine Produkte im Angebot.")
        return

    for product in products:
        caption = (
            f"📦 **{product['name']}**\n\n"
            f"📝 {product['description']}\n\n"
            f"💰 Preis: {product['price']}€"
        )
        
        kb = [
            [types.InlineKeyboardButton(
                text=f"Kaufen für {product['price']}€", 
                callback_data=f"buy_{product['id']}_{product['owner_id']}"
            )]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
        
        await message.answer(caption, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("buy_"))
async def start_purchase(callback: types.CallbackQuery):
    data = callback.data.split("_")
    product_id = data[1]
    seller_id = int(data[2])
    
    # Bestellung in der Datenbank anlegen (Status: pending)
    order = await create_order(
        buyer_id=callback.from_user.id,
        product_id=product_id,
        seller_id=seller_id
    )
    
    if order:
        await callback.message.answer(
            "Vielen Dank für dein Interesse!\n\n"
            "Bitte sende den Betrag an die vom Händler hinterlegte Adresse.\n"
            "Sobald der Händler den Zahlungseingang bestätigt, erhältst du deine Ware automatisch hier im Chat."
        )
        
        # Benachrichtigung an den Verkäufer senden
        # Hier nutzen wir die Bot-Instanz, um dem Verkäufer den Bestätigungs-Button zu schicken
        confirm_kb = [
            [types.InlineKeyboardButton(
                text="Zahlung erhalten & Ware senden", 
                callback_data=f"confirm_{order['id']}"
            )]
        ]
        confirm_keyboard = types.InlineKeyboardMarkup(inline_keyboard=confirm_kb)
        
        await callback.bot.send_message(
            chat_id=seller_id,
            text=f"🔔 **Neue Bestellung!**\n\nEin Kunde möchte ein Produkt kaufen. Bitte bestätige den Erhalt der Zahlung, um die Ware freizugeben.",
            reply_markup=confirm_keyboard,
            parse_mode="Markdown"
        )
        
        await callback.answer("Bestellung wurde aufgenommen!")
    else:
        await callback.answer("Fehler beim Erstellen der Bestellung.", show_alert=True)
