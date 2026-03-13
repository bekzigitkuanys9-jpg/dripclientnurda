from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Payment
from config import config
from keyboards.admin_kb import approve_reject_keyboard
from keyboards.user_kb import main_menu_keyboard

router = Router()


class PaymentState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_receipt = State()


@router.message(F.text == "💳 Top-up Balance")
async def topup_handler(message: Message, state: FSMContext):
    await state.set_state(PaymentState.waiting_for_amount)
    await message.answer(
        "💳 <b>БАЛАНС ТОЛТЫРУ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Толтырғыңыз келетін соманы теңгемен жазыңыз:",
        parse_mode="HTML"
    )


@router.message(PaymentState.waiting_for_amount)
async def payment_amount_handler(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("⚠️ Жарамды сома енгізіңіз (тек сандар).")
        return

    amount = float(message.text.strip())
    if amount <= 0:
        await message.answer("⚠️ Сома 0-ден үлкен болуы тиіс.")
        return

    await state.update_data(amount=amount)
    await state.set_state(PaymentState.waiting_for_receipt)

    text = (
        f"💳 <b>KASPI АРҚЫЛЫ ТӨЛЕУ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Төлем сомасы: <b>{amount:,.0f} ₸</b>\n\n"
        f"📱 Kaspi деректемелері:\n"
        f"   Телефон: <code>{config.kaspi_phone}</code>\n"
        f"   Алушы: <b>{config.kaspi_receiver}</b>\n\n"
        f"✅ Төлемді жасаңыз, содан кейін:\n"
        f"📸 Скриншотты немесе чек файлын (jpg/png/pdf) жіберіңіз."
    )
    await message.answer(text, parse_mode="HTML")


@router.message(PaymentState.waiting_for_receipt, F.photo | F.document)
async def payment_receipt_handler(
    message: Message, state: FSMContext, bot: Bot,
    db_user: User, db_session: AsyncSession
):
    data = await state.get_data()
    amount = data.get("amount")

    file_id = None
    is_photo = False
    if message.photo:
        file_id = message.photo[-1].file_id
        is_photo = True
    elif message.document:
        file_id = message.document.file_id

    if not file_id:
        await message.answer("⚠️ Сурет немесе файл жіберіңіз.")
        return

    payment = Payment(
        user_tg_id=db_user.tg_id,
        amount=amount,
        receipt_file_id=file_id,
        status="pending"
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)

    await state.clear()
    await message.answer(
        "✅ <b>Төлем сұранысы жіберілді!</b>\n\n"
        "Админ тексеріп, балансыңызды толтырады.\n"
        "Шыдамдылықпен күтіңіз. 🙏",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )

    if not config.admin_ids:
        return

    admin_text = (
        f"📥 <b>ЖАҢА ТӨЛЕМ СҰРАНЫСЫ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 User: @{message.from_user.username or 'no_username'}\n"
        f"🆔 Telegram ID: <code>{db_user.tg_id}</code>\n"
        f"💰 Сома: <b>{amount:,.0f} ₸</b>\n"
        f"🔢 Төлем ID: #{payment.id}"
    )

    kb = approve_reject_keyboard(payment.id, db_user.tg_id)

    for admin_id in config.admin_ids:
        try:
            if is_photo:
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=file_id,
                    caption=admin_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                await bot.send_document(
                    chat_id=admin_id,
                    document=file_id,
                    caption=admin_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"Admin {admin_id} хабар жіберілмеді: {e}")
