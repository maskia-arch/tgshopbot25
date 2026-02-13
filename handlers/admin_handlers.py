from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.db_service import add_product, get_user_products, delete_product, confirm_order
from core.validator import can_add_product

router = Router()

class ProductForm(StatesGroup):
    name = State()
    description = State()
    price = State()
    content = State()

@router.message(F.text == "🛒 Meinen Test-Shop verwalten")
@router.message(Command("admin"))
async def admin_menu(message: types.Message):
    kb = [
        [types.KeyboardButton(text="➕ Produkt hinzufügen")],
        [types.KeyboardButton(text="📋 Meine Produkte")],
        [types.KeyboardButton(text="🏠 Hauptmenü")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Willkommen im Admin-Bereich von Own1Shop.", reply_markup=keyboard)

@router.message(F.text == "➕ Produkt hinzufügen")
async def start_add_product(message: types.Message, state: FSMContext):
    if not await can_add_product(message.from_user.id):
        await message.answer("Limit erreicht! Im Free-Modus max. 2 Produkte. Upgrade auf Pro für unbegrenzt.")
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
    await message.answer("Was soll es kosten? (z.B. 5.99)")

@router.message(ProductForm.price)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
        await state.update_data(price=price)
        await state.set_state(ProductForm.content)
        await message.answer("Sende nun die Ware (Logins, Codes, etc.):")
    except ValueError:
        await message.answer("Bitte eine gültige Zahl eingeben.")

@router.message(ProductForm.content)
async def process_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await add_product(
        owner_id=message.from_user.id,
        name=data['name'],
        price=data['price'],
        content=message.text,
        description=data['description']
    )
    await state.clear()
    await message.answer(f"✅ Produkt '{data['name']}' wurde erfolgreich erstellt!")

@router.callback_query(F.data.startswith("confirm_"))
async def process_confirm_sale(callback: types.CallbackQuery):
    order_id = callback.data.split("_")[1]
    await confirm_order(order_id)
    await callback.message.edit_text("✅ Verkauf bestätigt. Die Ware wurde an den Kunden gesendet.")
