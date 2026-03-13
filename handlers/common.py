from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart
from database.models import User
from keyboards.user_kb import main_menu_keyboard, share_contact_keyboard
from config import config

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User):
    """Shows phone verification or dashboard depending on user state."""
    if not db_user.phone_number:
        await message.answer(
            "👋 <b>Добро пожаловать!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Ботқа қатынасу үшін телефон нөміріңізді жіберіңіз 📲\n\n"
            "<i>(Бұл сізді адам екенін растайды)</i>",
            parse_mode="HTML",
            reply_markup=share_contact_keyboard()
        )
        return
    await _show_dashboard(message, db_user)


@router.message(F.contact)
async def handle_contact(message: Message, db_user: User, db_session, bot: Bot):
    """Receives shared contact, saves phone, notifies admins."""
    contact = message.contact

    if contact.user_id != message.from_user.id:
        await message.answer("⚠️ Тек өзіңіздің нөміріңізді жіберіңіз.")
        return

    is_new = db_user.phone_number is None
    db_user.phone_number = contact.phone_number
    await db_session.commit()

    await message.answer(
        f"✅ <b>Растама сәтті!</b>\n\n"
        f"📱 Нөмір: <code>{contact.phone_number}</code>\n\n"
        f"Енді ботты толық пайдалана аласыз!",
        parse_mode="HTML"
    )
    await _show_dashboard(message, db_user)

    # Notify all admins about this new verified user
    if is_new:
        admin_msg = (
            f"🆕 <b>ЖАҢА ПАЙДАЛАНУШЫ ТІРКЕЛДІ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Username: @{message.from_user.username or '—'}\n"
            f"🆔 Telegram ID: <code>{message.from_user.id}</code>\n"
            f"📱 Телефон: <code>{contact.phone_number}</code>\n"
            f"📛 Аты: {message.from_user.full_name}\n"
            f"📅 Тіркелді: {db_user.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        for admin_id in config.admin_ids:
            try:
                await bot.send_message(admin_id, admin_msg, parse_mode="HTML")
            except Exception:
                pass


async def _show_dashboard(message: Message, db_user: User):
    """Renders the Reseller Dashboard."""
    from datetime import datetime, timezone, timedelta
    tz = timezone(timedelta(hours=5))
    now = datetime.now(tz).strftime("%I:%M %p")

    text = (
        f"💠 <b>RESELLER DASHBOARD</b> 💠\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 User: @{message.from_user.username or 'no_username'}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n\n"
        f"📊 <b>STATISTICS:</b>\n"
        f"   💳 Balance: <b>{db_user.balance:,.0f} ₸</b>\n"
        f"   🛒 Spent:   <b>{db_user.total_spent:,.0f} ₸</b>\n"
        f"   🛡 Status:  🟢 Active\n\n"
        f"🕒 Time: {now}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")


@router.message(F.text == "👤 My Profile")
async def profile_handler(message: Message, db_user: User):
    text = (
        f"👤 <b>MY PROFILE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{db_user.tg_id}</code>\n"
        f"👤 Username: @{message.from_user.username or 'no_username'}\n"
        f"📱 Phone: <code>{db_user.phone_number or '—'}</code>\n\n"
        f"💳 Balance:     <b>{db_user.balance:,.0f} ₸</b>\n"
        f"🛒 Total spent: <b>{db_user.total_spent:,.0f} ₸</b>\n"
        f"📅 Joined: {db_user.created_at.strftime('%d.%m.%Y')}"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "👥 Referral")
async def referral_handler(message: Message, db_user: User):
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={db_user.tg_id}"
    text = (
        f"👥 <b>REFERRAL SYSTEM</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Достарыңызды шақырыңыз!\n\n"
        f"🔗 Сіздің сілтемеңіз:\n"
        f"<code>{ref_link}</code>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🌐 Useful Links")
async def links_handler(message: Message):
    text = (
        f"🌐 <b>USEFUL LINKS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🌐 <a href='{config.official_website}'>Official Website</a>\n"
        f"⬇️ <a href='{config.download_link}'>Download DRIP CLIENT</a>\n"
        f"📢 <a href='{config.telegram_channel}'>Telegram Channel</a>\n"
        f"💬 <a href='{config.contact_admin}'>Contact Admin</a>"
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
