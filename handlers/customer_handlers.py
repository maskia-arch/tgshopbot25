from aiogram import Router, types, F
from services.db_service import get_user_products, create_order, get_stock_count
from config import Config
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

async def show_shop_catalog(message: types.Message, owner_id: int):
    """
    Zentrale Funktion zur Produktpräsentation. 
    Wird aufgerufen durch Deep-Links oder die Shop-Vorschau.
    """
    products = await get_user_products(owner_id)
    
    if not products:
        await message.answer("📭 Dieser Shop hat aktuell keine Produkte im Angebot.")
        return

    for product in products:
        # Frischen Lagerbestand direkt aus der DB laden
        stock_count = await get_stock_count(product['id'])
        
        stock_text = f"✅ Auf Lager: `{stock_count}`" if stock_count > 0 else "❌ Aktuell ausverkauft"
        
        caption = (
            f"📦 **{product['name']}**\n\n"
            f"📝 {product['description']}\n\n"
            f"💰 Preis: {product['price']}€\n"
            f"🔢 Status: {stock_text}"
        )
        
        builder = InlineKeyboardBuilder()
        
        if stock_count > 0:
            # Kauf-Button mit Produkt-ID und Besitzer-ID verknüpfen
            builder.row(types.InlineKeyboardButton(
                text=f"🛒 Jetzt kaufen ({product['price']}€)", 
                callback_data=f"buy_{product['id']}_{product['owner_id']}"
            ))
        else:
            # Kontakt-Button falls ausverkauft
            builder.row(types.InlineKeyboardButton(
                text="Nachricht an Verkäufer", 
                url=f"tg://user?id={product['owner_id']}"
            ))
            
        await message.answer(caption, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.message(F.text == "🛍 Shop durchsuchen")
async def browse_own_shop(message: types.Message):
    """Handler für den Button im Master-Bot (eigene Produkte sehen)."""
    await message.answer("👀 **Vorschau deines Shops:**")
    await show_shop_catalog(message, message.from_user.id)

@router.callback_query(F.data.startswith("buy_"))
async def start_purchase(callback: types.CallbackQuery):
    """Verarbeitet den Kaufwunsch eines Kunden."""
    data = callback.data.split("_")
    product_id = data[1]
    seller_id = int(data[2])
    
    # Echtzeit-Check: Ist das Item noch da?
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
            "Sobald der Händler den Zahlungseingang bestätigt, wird dir die Ware **automatisch hier im Chat** zugestellt.",
            parse_mode="Markdown"
        )
        
        # Benachrichtigung an den Verkäufer (Admin) mit Bestätigungs-Button
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
                f"Kunde: @{callback.from_user.username or 'Unbekannt'} (`{callback.from_user.id}`)\n"
                f"Produkt-ID: `{product_id}`\n"
                f"Bestell-ID: `{order['id']}`\n\n"
                f"Bitte bestätige den Zahlungseingang unten, um die Ware auszuliefern."
            ),
            reply_markup=confirm_keyboard,
            parse_mode="Markdown"
        )
        
        await callback.answer("Bestellung aufgenommen!")
    else:
        await callback.answer("Fehler beim Erstellen der Bestellung.", show_alert=True)
