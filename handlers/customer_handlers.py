from aiogram import Router, types, F
from services.db_service import get_user_products, create_order, get_stock_count
from config import Config

router = Router()

@router.message(F.text == "🛍 Shop durchsuchen")
async def browse_shop(message: types.Message):
    # Für den Test-Modus nutzen wir die ID des Users selbst als Shop-Besitzer
    products = await get_user_products(message.from_user.id)
    
    if not products:
        await message.answer("Dieser Shop hat aktuell keine Produkte im Angebot.")
        return

    for product in products:
        # Lagerbestand für dieses Produkt abrufen
        stock_count = await get_stock_count(product['id'])
        
        # Status-Text für den Bestand
        stock_text = f"✅ Auf Lager: `{stock_count}`" if stock_count > 0 else "❌ Aktuell ausverkauft"
        
        caption = (
            f"📦 **{product['name']}**\n\n"
            f"📝 {product['description']}\n\n"
            f"💰 Preis: {product['price']}€\n"
            f"🔢 Status: {stock_text}"
        )
        
        kb = []
        # Kaufen-Button nur anzeigen, wenn Bestand > 0 ist
        if stock_count > 0:
            kb.append([types.InlineKeyboardButton(
                text=f"🛒 Jetzt kaufen ({product['price']}€)", 
                callback_data=f"buy_{product['id']}_{product['owner_id']}"
            )])
        else:
            kb.append([types.InlineKeyboardButton(
                text="Nachricht an Verkäufer", 
                url=f"tg://user?id={product['owner_id']}"
            )])
            
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
        
        await message.answer(caption, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("buy_"))
async def start_purchase(callback: types.CallbackQuery):
    data = callback.data.split("_")
    product_id = data[1]
    seller_id = int(data[2])
    
    # Sicherheitshalber den Bestand vor der Bestellung nochmal prüfen
    stock_count = await get_stock_count(product_id)
    if stock_count <= 0:
        await callback.answer("⚠️ Leider ist dieses Produkt gerade ausverkauft!", show_alert=True)
        return

    # Bestellung in der Datenbank anlegen (Status: pending)
    order = await create_order(
        buyer_id=callback.from_user.id,
        product_id=product_id,
        seller_id=seller_id
    )
    
    if order:
        await callback.message.answer(
            "✅ **Bestellung eingeleitet!**\n\n"
            "Bitte sende den Betrag an die vom Händler hinterlegte Adresse.\n"
            "Sobald der Händler den Zahlungseingang bestätigt, wird dir die Ware (Logins/Codes) **automatisch hier im Chat** zugestellt.",
            parse_mode="Markdown"
        )
        
        # Benachrichtigung an den Verkäufer (Admin) senden
        confirm_kb = [
            [types.InlineKeyboardButton(
                text="✅ Zahlung erhalten (Ware senden)", 
                callback_data=f"confirm_{order['id']}"
            )]
        ]
        confirm_keyboard = types.InlineKeyboardMarkup(inline_keyboard=confirm_kb)
        
        await callback.bot.send_message(
            chat_id=seller_id,
            text=(
                f"🔔 **Neue Bestellung!**\n\n"
                f"Ein Kunde möchte ein Produkt kaufen.\n"
                f"Bestell-ID: `{order['id']}`\n"
                f"Kunde: @{callback.from_user.username or 'Unbekannt'} (`{callback.from_user.id}`)\n\n"
                f"Bitte bestätige den Zahlungseingang, um das Produkt aus dem Lager freizugeben."
            ),
            reply_markup=confirm_keyboard,
            parse_mode="Markdown"
        )
        
        await callback.answer("Bestellung aufgenommen!")
    else:
        await callback.answer("Fehler beim Erstellen der Bestellung.", show_alert=True)
