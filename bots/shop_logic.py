from aiogram import Router, types, F
from aiogram.filters import Command
from services.db_service import get_user_products, get_stock_count
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.strings import Buttons

router = Router()

async def show_products_for_shop(message: types.Message, owner_id: int):
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

        builder = InlineKeyboardBuilder()
        if stock_count > 0:
            builder.row(types.InlineKeyboardButton(
                text=f"🛒 Kaufen ({product['price']}€)",
                callback_data=f"buy_{product['id']}_{owner_id}"
            ))
        else:
            builder.row(types.InlineKeyboardButton(
                text="📧 Verkäufer kontaktieren",
                url=f"tg://user?id={owner_id}"
            ))

        await message.answer(
            caption, 
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )

@router.message(Command("start"))
async def handle_shop_start(message: types.Message, is_owner: bool = False, shop_owner_id: int = None):
    if is_owner:
        return

    if shop_owner_id:
        await message.answer(f"🏪 **Willkommen im Shop!**\nHier sind die aktuellen Angebote:")
        await show_products_for_shop(message, shop_owner_id)

@router.callback_query(F.data == "refresh_shop")
async def refresh_shop_view(callback: types.CallbackQuery):
    await callback.answer("Ansicht wurde aktualisiert.")
