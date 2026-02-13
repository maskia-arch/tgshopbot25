from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.db_service import (
    add_product, get_user_products, delete_product, 
    confirm_order, refill_stock, get_stock_count, get_user_by_id
)
from core.validator import can_add_product
from core.supabase_client import db
from core.strings import Buttons, Messages

router = Router()

class ProductForm(StatesGroup):
    name = State()
    description = State()
    price = State()
    content = State()

class RefillForm(StatesGroup):
    product_id = State()
    content = State()

@router.message(Command("start"))
async def cmd_start_handler(message: types.Message, is_owner: bool = False, shop_owner_id: int = None):
    if is_owner:
        await admin_menu(message, is_owner=True)
    elif shop_owner_id:
        from bots.shop_logic import show_products_for_shop
        await message.answer(f"🏪 **Willkommen im Shop!**\nHier sind die aktuellen Angebote:")
        await show_products_for_shop(message, shop_owner_id)
    else:
        await message.answer(Messages.WELCOME_BACK.format(status="FREE", shop_id="Keine"))

@router.message(F.text == Buttons.ADMIN_MANAGE)
@router.message(Command("admin"))
async def admin_menu(message: types.Message, is_owner: bool = False):
    user = await get_user_by_id(message.from_user.id)
    if not user:
        return

    shop_id = user.get("shop_id", "Wird generiert...")
    bot_info = await message.bot.get_me()
    
    shop_link = f"https://t.me/{bot_info.username}"
    if "?start=" not in shop_link and "Own1Shop_Bot" in bot_info.username:
        shop_link += f"?start={shop_id}"

    kb = [
        [types.KeyboardButton(text=Buttons.ADD_PRODUCT)],
        [types.KeyboardButton(text=Buttons.LIST_PRODUCTS)],
        [types.KeyboardButton(text=Buttons.SETTINGS)],
        [types.KeyboardButton(text=Buttons.MAIN_MENU)]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    text = Messages.ADMIN_WELCOME.format(shop_id=shop_id, shop_link=shop_link)
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)

@router.message(F.text == Buttons.ADD_PRODUCT)
async def start_add_product(message: types.Message, state: FSMContext):
    if not await can_add_product(message.from_user.id):
        await message.answer(Messages.LIMIT_REACHED)
        return
    
    await state.set_state(ProductForm.name)
    await message.answer(Messages.ASK_PRODUCT_NAME)

@router.message(ProductForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ProductForm.description)
    await message.answer(Messages.ASK_PRODUCT_DESC)

@router.message(ProductForm.description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(ProductForm.price)
    await message.answer(Messages.ASK_PRODUCT_PRICE)

@router.message(ProductForm.price)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
        await state.update_data(price=price)
        await state.set_state(ProductForm.content)
        kb = [[types.InlineKeyboardButton(text=Buttons.SKIP_STOCK, callback_data="skip_stock")]]
        await message.answer(
            "📦 **Lagerbestand hinzufügen (Optional)**\n\nSende jetzt die Daten oder überspringe.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer("Bitte eine gültige Zahl eingeben.")

@router.callback_query(F.data == "skip_stock")
async def skip_stock_process(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await add_product(callback.from_user.id, data['name'], data['price'], "", data['description'])
    await state.clear()
    await callback.message.edit_text(f"✅ Produkt **{data['name']}** erstellt.")
    await callback.answer()

@router.message(ProductForm.content)
async def process_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await add_product(message.from_user.id, data['name'], data['price'], message.text, data['description'])
    await state.clear()
    await message.answer(Messages.PRODUCT_ADDED.format(name=data['name']))

@router.message(F.text == Buttons.LIST_PRODUCTS)
async def list_admin_products(message: types.Message):
    products = await get_user_products(message.from_user.id)
    if not products:
        await message.answer("Du hast noch keine Produkte angelegt.")
        return

    for p in products:
        stock = await get_stock_count(p['id'])
        text = f"📦 **{p['name']}**\n💰 Preis: {p['price']}€\n🔢 Lager: `{stock}`"
        kb = [
            [types.InlineKeyboardButton(text=Buttons.REFILL_STOCK, callback_data=f"refill_{p['id']}")],
            [types.InlineKeyboardButton(text=Buttons.DELETE_PRODUCT, callback_data=f"delete_{p['id']}")]
        ]
        await message.answer(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@router.callback_query(F.data.startswith("refill_"))
async def start_refill(callback: types.CallbackQuery, state: FSMContext):
    pid = callback.data.split("_")[1]
    await state.update_data(refill_id=pid)
    await state.set_state(RefillForm.content)
    await callback.message.answer(Messages.STOCK_REFILL_PROMPT)
    await callback.answer()

@router.message(RefillForm.content)
async def process_refill_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pid = data.get('refill_id')
    if pid:
        added = await refill_stock(pid, message.from_user.id, message.text)
        await message.answer(f"✅ `{added}` Einheiten nachgefüllt!")
    await state.clear()

@router.callback_query(F.data.startswith("delete_"))
async def process_delete_product(callback: types.CallbackQuery):
    pid = callback.data.split("_")[1]
    await delete_product(pid, callback.from_user.id)
    await callback.message.delete()
    await callback.answer("✅ Produkt gelöscht.")

@router.callback_query(F.data.startswith("confirm_"))
async def process_confirm_sale(callback: types.CallbackQuery):
    order_id = callback.data.split("_")[1]
    order = db.table("orders").select("*").eq("id", order_id).single().execute().data
    if order:
        item = await confirm_order(order_id)
        if item == "sold_out":
            await callback.message.answer("❌ Ausverkauft!")
        elif item:
            await callback.bot.send_message(order['buyer_id'], f"🎉 Ware erhalten:\n<code>{item}</code>", parse_mode="HTML")
            await callback.message.edit_text(f"✅ Ware gesendet:\n<code>{item}</code>", parse_mode="HTML")
    await callback.answer()
