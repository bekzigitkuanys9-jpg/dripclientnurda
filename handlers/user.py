from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, Product, Key
from keyboards.user_kb import main_menu_keyboard, products_keyboard

router = Router()


# ─── PRODUCTS ────────────────────────────────────────────────────

@router.message(F.text == "🛒 Products")
async def products_handler(message: Message, db_user: User, db_session: AsyncSession):
    result = await db_session.execute(select(Product))
    products = result.scalars().all()

    if not products:
        await message.answer("❌ Қазір тауарлар жоқ.")
        return

    text = (
        f"🛍 <b>DRIP CLIENT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Лицензия мерзімін таңдаңыз:\n\n"
        f"💳 Балансыңыз: <b>{db_user.balance:,.0f} ₸</b>"
    )
    await message.answer(
        text,
        reply_markup=products_keyboard(products),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("buy_"))
async def buy_product_cb(callback: CallbackQuery, db_user: User, db_session: AsyncSession):
    product_id = int(callback.data.split("_")[1])

    from services.key_allocator import process_purchase
    success, msg = await process_purchase(db_session, db_user, product_id)

    if success:
        await callback.message.answer(
            f"✅ <b>Сатып алу сәтті!</b>\n\n{msg}\n\n"
            f"💳 Қалдық баланс: <b>{db_user.balance:,.0f} ₸</b>",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
    else:
        await callback.answer(f"❌ {msg}", show_alert=True)

    await callback.answer()


# ─── MY KEYS ─────────────────────────────────────────────────────

@router.message(F.text == "🔑 My Keys")
async def my_keys_handler(message: Message, db_user: User, db_session: AsyncSession):
    result = await db_session.execute(
        select(Key).join(Product)
        .where(Key.used_by == db_user.tg_id)
        .order_by(Key.created_at.desc())
    )
    keys = result.scalars().all()

    if not keys:
        await message.answer("🔑 Сізде әлі кілттер жоқ.\n\n🛒 Тауарлар бөліміне өтіп сатып алыңыз!")
        return

    text = "🔑 <b>MY KEYS</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for key in keys:
        text += f"📦 <b>{key.product.name}</b>\n<code>{key.key_value}</code>\n\n"

    await message.answer(text, parse_mode="HTML")
