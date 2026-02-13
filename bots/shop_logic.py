from aiogram import Router, types, F
from services.db_service import get_user_products, get_stock_count
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

async def show_products_for_shop(message: types.Message, owner_id: int):
    """
    Kern-Funktion, um alle Produkte eines spezifischen Shops anzuzeigen.
    Wird vom Master-Bot aufgerufen, wenn ein Deep-Link benutzt wird.
    """
    products = await get_user_products(owner_id)
    
    if not products:
        await message.answer(
            "📭 **Dieser Shop ist aktuell leer.**\n"
            "Der Verkäufer hat noch keine Produkte eingestellt.",
            parse_mode="Markdown"
        )
        return

    for product in products:
        stock_count = await get_stock_count(product['id'])
        
        # Status-Anzeige für den Kunden
        if stock_count > 0:
            stock_status = f"✅ Vorrätig: `{stock_count}`"
        else:
            stock_status = "❌ Aktuell ausverkauft"

        caption = (
            f"📦 **{product['name']}**\n\n"
            f"📝 {product['description']}\n\n"
            f"💰 Preis: **{product['price']}€**\n"
            f"🔢 Status: {stock_status}"
        )

        # Inline Keyboard für den Kaufprozess
        builder = InlineKeyboardBuilder()
        if stock_count > 0:
            # Wir übergeben Produkt-ID und Verkäufer-ID im Callback
            builder.row(types.InlineKeyboardButton(
                text=f"🛒 Kaufen ({product['price']}€)",
                callback_data=f"buy_{product['id']}_{owner_id}"
            ))
        else:
            # Optional: Kontakt zum Verkäufer, wenn ausverkauft
            builder.row(types.InlineKeyboardButton(
                text="📧 Verkäufer kontaktieren",
                url=f"tg://user?id={owner_id}"
            ))

        await message.answer(
            caption, 
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )

@router.callback_query(F.data == "refresh_shop")
async def refresh_shop_view(callback: types.CallbackQuery):
    """Ermöglicht es dem Kunden, die Ansicht zu aktualisieren."""
    # Logik zur Aktualisierung (optional)
    await callback.answer("Ansicht wurde aktualisiert.")
