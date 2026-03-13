from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, Product
from handlers.admin.panel import is_admin

router = Router()


# ─── FSM States ──────────────────────────────────────────────────────────────

class AddProductFSM(StatesGroup):
    waiting_name  = State()
    waiting_price = State()

class EditPriceFSM(StatesGroup):
    waiting_product = State()   # callback triggers this
    waiting_price   = State()


# ─── Helper: inline keyboard of all products ─────────────────────────────────

def products_inline_kb(products: list[Product], action: str) -> InlineKeyboardMarkup:
    """action = 'edit_price'"""
    buttons = [
        [InlineKeyboardButton(
            text=f"{p.name} — {p.price:,.0f} ₸",
            callback_data=f"{action}:{p.id}"
        )]
        for p in products
    ]
    buttons.append([InlineKeyboardButton(text="❌ Болдырмау", callback_data="product_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ══════════════════════════════════════════════════════════════════════════════
# ADD PRODUCT
# ══════════════════════════════════════════════════════════════════════════════

@router.message(F.text == "➕ Тауар қосу")
async def add_product_start(message: Message, db_user: User, state: FSMContext):
    if not is_admin(db_user.tg_id):
        return
    await state.set_state(AddProductFSM.waiting_name)
    await message.answer(
        "📦 <b>Жаңа тауар қосу</b>\n\n"
        "Тауардың атын жазыңыз:\n"
        "<i>(мысалы: 1 КҮН)</i>",
        parse_mode="HTML"
    )


@router.message(AddProductFSM.waiting_name)
async def add_product_name(message: Message, db_user: User, state: FSMContext):
    if not is_admin(db_user.tg_id):
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AddProductFSM.waiting_price)
    await message.answer(
        f"✅ Атауы: <b>{message.text.strip()}</b>\n\n"
        "Бағасын теңгемен енгізіңіз:\n"
        "<i>(мысалы: 366)</i>",
        parse_mode="HTML"
    )


@router.message(AddProductFSM.waiting_price)
async def add_product_price(message: Message, db_user: User, db_session: AsyncSession, state: FSMContext):
    if not is_admin(db_user.tg_id):
        return

    try:
        price = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Дұрыс сан енгізіңіз, мысалы: <b>366</b>", parse_mode="HTML")
        return

    data = await state.get_data()
    name = data["name"]

    # Check duplicate
    existing = await db_session.scalar(select(Product).where(Product.name == name))
    if existing:
        await state.clear()
        await message.answer(
            f"⚠️ <b>{name}</b> атты тауар бұрыннан бар!\n"
            "Бағасын өзгерту үшін «✏️ Баға өзгерту» батырмасын қолданыңыз.",
            parse_mode="HTML"
        )
        return

    product = Product(name=name, price=price, description=f"{name} лицензиясы")
    db_session.add(product)
    await db_session.commit()
    await state.clear()

    await message.answer(
        f"✅ <b>Тауар сәтті қосылды!</b>\n\n"
        f"📦 Атауы: <b>{name}</b>\n"
        f"💰 Бағасы: <b>{price:,.0f} ₸</b>",
        parse_mode="HTML"
    )


# ══════════════════════════════════════════════════════════════════════════════
# EDIT PRODUCT PRICE
# ══════════════════════════════════════════════════════════════════════════════

@router.message(F.text == "✏️ Баға өзгерту")
async def edit_price_start(message: Message, db_user: User, db_session: AsyncSession, state: FSMContext):
    if not is_admin(db_user.tg_id):
        return

    result = await db_session.execute(select(Product).order_by(Product.id))
    products = result.scalars().all()

    if not products:
        await message.answer("⚠️ Тауарлар жоқ.")
        return

    await state.set_state(EditPriceFSM.waiting_product)
    await message.answer(
        "✏️ <b>Бағасын өзгерту</b>\n\n"
        "Тауарды таңдаңыз:",
        reply_markup=products_inline_kb(products, "edit_price"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("edit_price:"), EditPriceFSM.waiting_product)
async def edit_price_chosen(callback: CallbackQuery, db_user: User, db_session: AsyncSession, state: FSMContext):
    if not is_admin(db_user.tg_id):
        return

    product_id = int(callback.data.split(":")[1])
    product = await db_session.get(Product, product_id)
    if not product:
        await callback.answer("Тауар табылмады.", show_alert=True)
        return

    await state.update_data(product_id=product_id, product_name=product.name, old_price=product.price)
    await state.set_state(EditPriceFSM.waiting_price)
    await callback.message.edit_text(
        f"✏️ <b>{product.name}</b>\n"
        f"Қазіргі баға: <b>{product.price:,.0f} ₸</b>\n\n"
        "Жаңа бағаны теңгемен енгізіңіз:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(EditPriceFSM.waiting_price)
async def edit_price_confirm(message: Message, db_user: User, db_session: AsyncSession, state: FSMContext):
    if not is_admin(db_user.tg_id):
        return

    try:
        new_price = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Дұрыс сан енгізіңіз, мысалы: <b>2555</b>", parse_mode="HTML")
        return

    data = await state.get_data()
    product = await db_session.get(Product, data["product_id"])
    old_price = data["old_price"]

    product.price = new_price
    await db_session.commit()
    await state.clear()

    await message.answer(
        f"✅ <b>Баға сәтті өзгертілді!</b>\n\n"
        f"📦 Тауар: <b>{product.name}</b>\n"
        f"💰 Бұрынғы баға: <s>{old_price:,.0f} ₸</s>\n"
        f"💰 Жаңа баға:    <b>{new_price:,.0f} ₸</b>",
        parse_mode="HTML"
    )


# ─── Cancel ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "product_cancel")
async def product_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Болдырылмады.")
    await callback.answer()
