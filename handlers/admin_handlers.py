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

router = Router()

class ProductForm(StatesGroup):
    name = State()
    description = State()
    price = State()
    content = State()

class RefillForm(StatesGroup):
    product_id = State()
    content = State()

@router.message(F.text == "🛒 Meinen Test-Shop verwalten")
@router.message(Command("admin"))
async def admin_menu(message: types.Message):
    user = await get_user_by_id(message.from_user.id)
    shop_id = user.get("shop_id", "Wird generiert...")
    bot_info = await message.bot.get_me()
    
    shop_link = f"https://t.me/{bot_info.username}?start={shop_id}"

    kb = [
        [types.KeyboardButton(text="➕ Produkt hinzufügen")],
        [types.KeyboardButton(text="📋 Meine Produkte")],
        [types.KeyboardButton(text="⚙️ Shop-Einstellungen / Zahlungsarten")],
        [types.KeyboardButton(text="🏠 Hauptmenü")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    text = (
        "🛠 **Admin-Bereich**\n\n"
        f"🆔 Deine Shop-ID: `{shop_id}`\n"
        f"🔗 Kunden-Link: [Hier klicken]({shop_link})\n\n"
        "Verwalte hier deine Produkte, Zahlungsarten und Bestände."
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)

@router.message(F.text == "➕ Produkt hinzufügen")
async def start_add_product(message: types.Message, state: FSMContext):
    if not await can_add_product(message.from_user.id):
        await message.answer("⚠️ Limit erreicht! Im Free-Modus max. 2 Produkte. Upgrade auf Pro für unbegrenzt.")
        return
    
    await state.set_state(ProductForm.name)
    await message.answer("Wie soll das Produkt heißen?")

@router.message(ProductForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ProductForm.description)
    await message.answer("Gib eine kurze Beschreibung ein:")

@router.message(ProductForm.description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(ProductForm.price)
    await message.answer("Was soll es kosten? (z.B. 12.50)")

@router.message(ProductForm.price)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
        await state.update_data(price=price)
        await state.set_state(ProductForm.content)
        
        kb = [[types.InlineKeyboardButton(text="⏭ Später auffüllen (Überspringen)", callback_data="skip_stock")]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
        
        await message.answer(
            "📦 **Lagerbestand hinzufügen (Optional)**\n\n"
            "Sende jetzt die Daten (Format: `mail:pass, mail:pass`)\n"
            "oder überspringe diesen Schritt.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer("Bitte eine gültige Zahl eingeben.")

@router.callback_query(F.data == "skip_stock")
async def skip_stock_process(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("name"):
        await callback.answer("Fehler: Sitzung abgelaufen.", show_alert=True)
        return

    await add_product(
        owner_id=callback.from_user.id,
        name=data['name'],
        price=data['price'],
        content="", 
        description=data['description']
    )
    await state.clear()
    await callback.message.edit_text(f"✅ Produkt **{data['name']}** ohne Bestand erstellt.")
    await callback.answer()

@router.message(ProductForm.content)
async def process_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("name"): 
        await state.clear()
        return

    await add_product(
        owner_id=message.from_user.id,
        name=data['name'],
        price=data['price'],
        content=message.text,
        description=data['description']
    )
    await state.clear()
    await message.answer(f"✅ Produkt **{data['name']}** wurde erstellt!")

@router.message(F.text == "📋 Meine Produkte")
async def list_admin_products(message: types.Message):
    products = await get_user_products(message.from_user.id)
    if not products:
        await message.answer("Du hast noch keine Produkte angelegt.")
        return

    for p in products:
        p_id = p['id']
        stock = await get_stock_count(p_id)
        text = (
            f"📦 **{p['name']}**\n"
            f"💰 Preis: {p['price']}€\n"
            f"🔢 Lagerbestand: `{stock}`"
        )
        kb = [
            [types.InlineKeyboardButton(text="➕ Lager auffüllen", callback_data=f"refill_{p_id}")],
            [types.InlineKeyboardButton(text="🗑 Löschen", callback_data=f"delete_{p_id}")]
        ]
        await message.answer(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@router.callback_query(F.data.startswith("refill_"))
async def start_refill(callback: types.CallbackQuery, state: FSMContext):
    try:
        product_id = callback.data.split("_")[1]
        await state.update_data(refill_id=product_id)
        await state.set_state(RefillForm.content)
        await callback.message.answer("📥 Sende nun die neuen Daten (`mail:pass` oder eine pro Zeile):")
        await callback.answer()
    except Exception:
        await callback.answer("Fehler beim Identifizieren des Produkts.", show_alert=True)

@router.message(RefillForm.content)
async def process_refill_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pid = data.get('refill_id')
    
    if pid:
        added_count = await refill_stock(pid, message.from_user.id, message.text)
        await message.answer(f"✅ Erfolgreich `{added_count}` Einheiten nachgefüllt!")
    
    await state.clear()

@router.callback_query(F.data.startswith("delete_"))
async def process_delete_product(callback: types.CallbackQuery):
    try:
        product_id = callback.data.split("_")[1]
        await delete_product(product_id, callback.from_user.id)
        await callback.message.delete()
        await callback.answer("✅ Produkt gelöscht.")
    except Exception:
        await callback.answer("Fehler beim Löschen des Produkts.", show_alert=True)

@router.callback_query(F.data.startswith("confirm_"))
async def process_confirm_sale(callback: types.CallbackQuery):
    try:
        order_id = callback.data.split("_")[1]
        order_res = db.table("orders").select("*").eq("id", order_id).single().execute()
        
        if not order_res.data:
            await callback.answer("Bestellung nicht gefunden.")
            return
        
        buyer_id = order_res.data['buyer_id']
        item_content = await confirm_order(order_id)
        
        if item_content == "sold_out":
            await callback.message.answer("❌ Produkt ist ausverkauft!")
        elif item_content:
            try:
                await callback.bot.send_message(
                    buyer_id, 
                    f"🎉 **Zahlung bestätigt!**\n\nHier ist deine Ware:\n<code>{item_content}</code>", 
                    parse_mode="HTML"
                )
                await callback.message.edit_text(
                    f"✅ **Verkauf bestätigt!**\nDie Ware wurde automatisch gesendet:\n<code>{item_content}</code>", 
                    parse_mode="HTML"
                )
            except Exception:
                await callback.message.answer(f"⚠️ Kunde konnte nicht benachrichtigt werden. Ware: {item_content}")
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Fehler: {str(e)}", show_alert=True)
