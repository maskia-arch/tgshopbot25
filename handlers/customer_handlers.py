from aiogram import Router, types, F
from services.db_service import get_user_products, create_order, get_stock_count, get_user_by_id
from config import Config
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.strings import Buttons, Messages

router = Router()

async def show_shop_catalog(message: types.Message, owner_id: int):
    products = await get_user_products(owner_id)
    
    if not products:
        await message.answer("📭 Dieser Shop hat aktuell keine Produkte im Angebot.")
        return

    for product in products:
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
            builder.row(types.InlineKeyboardButton(
                text=Buttons.BUY_NOW.format(price=product['price']), 
                callback_data=f"buy_{product['id']}_{product['owner_id']}"
            ))
        else:
            builder.row(types.InlineKeyboardButton(
                text=Buttons.CONTACT_SELLER, 
                url=f"tg://user?id={product['owner_id']}"
            ))
            
        await message.answer(caption, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.message(F.text == Buttons.VIEW_SHOP)
async def browse_own_shop(message: types.Message):
    await message.answer("👀 **Vorschau deines Shops:**")
    await show_shop_catalog(message, message.from_user.id)

@router.callback_query(F.data.startswith("buy_"))
async def start_purchase(callback: types.CallbackQuery):
    data = callback.data.split("_")
    product_id = data[1]
    seller_id = int(data[2])
    
    stock_count = await get_stock_count(product_id)
    if stock_count <= 0:
        await callback.answer("⚠️ Leider ist dieses Produkt gerade ausverkauft!", show_alert=True)
        return

    order = await create_order(
        buyer_id=callback.from_user.id,
        product_id=product_id,
        seller_id=seller_id
    )
    
    if order:
        # Verkäufer-Profil laden, um dessen Wallets anzuzeigen
        seller = await get_user_by_id(seller_id)
        
        payment_text = "✅ **Bestellung eingeleitet!**\n\nBitte sende den Betrag an eine der folgenden Adressen:\n\n"
        
        # Dynamische Anzeige der hinterlegten Wallets des Verkäufers
        if seller.get("wallet_btc"):
            payment_text += f"₿ **BTC:** `{seller['wallet_btc']}`\n"
        if seller.get("wallet_ltc"):
            payment_text += f"Ł **LTC:** `{seller['wallet_ltc']}`\n"
        if seller.get("wallet_eth"):
            payment_text += f"Ξ **ETH:** `{seller['wallet_eth']}`\n"
        if seller.get("wallet_sol"):
            payment_text += f"◎ **SOL:** `{seller['wallet_sol']}`\n"
        if seller.get("paypal_email"):
            payment_text += f"🅿️ **PayPal (F&F):** `{seller['paypal_email']}`\n"
            
        payment_text += "\nSobald der Händler den Zahlungseingang bestätigt, wird dir die Ware automatisch zugestellt."
        
        await callback.message.answer(payment_text, parse_mode="Markdown")
        
        # Benachrichtigung an den Verkäufer
        confirm_kb = [
            [types.InlineKeyboardButton(
                text=Buttons.CONFIRM_PAYMENT, 
                callback_data=f"confirm_{order['id']}"
            )]
        ]
        confirm_keyboard = types.InlineKeyboardMarkup(inline_keyboard=confirm_kb)
        
        await callback.bot.send_message(
            chat_id=seller_id,
            text=Messages.NEW_ORDER_SELLER.format(
                username=callback.from_user.username or 'Unbekannt',
                user_id=callback.from_user.id,
                product_name=product_id # Hier könnte man noch den echten Namen laden
            ),
            reply_markup=confirm_keyboard,
            parse_mode="Markdown"
        )
        
        await callback.answer("Bestellung aufgenommen!")
    else:
        await callback.answer("Fehler beim Erstellen der Bestellung.", show_alert=True)
