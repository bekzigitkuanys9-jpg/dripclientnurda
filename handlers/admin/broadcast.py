import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User
from config import config

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids

class BroadcastState(StatesGroup):
    text = State()
    button_text = State()
    button_url = State()
    confirm = State()

def cancel_markup():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Жою")]], resize_keyboard=True)

def skip_markup():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="⏩ Өткізіп жіберу")], [KeyboardButton(text="❌ Жою")]], resize_keyboard=True)

def confirm_markup():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✅ Жіберу")], [KeyboardButton(text="❌ Жою")]], resize_keyboard=True)

@router.message(F.text == "📢 Хабарлама жіберу")
async def broadcast_start(message: Message, state: FSMContext, db_user: User):
    if not is_admin(db_user.tg_id):
        return
    await message.answer("Хабарлама мәтінін енгізіңіз (HTML тегтерін қолдануға болады):", reply_markup=cancel_markup())
    await state.set_state(BroadcastState.text)

@router.message(StateFilter(BroadcastState.text), F.text == "❌ Жою")
@router.message(StateFilter(BroadcastState.button_text), F.text == "❌ Жою")
@router.message(StateFilter(BroadcastState.button_url), F.text == "❌ Жою")
@router.message(StateFilter(BroadcastState.confirm), F.text == "❌ Жою")
async def cancel_broadcast(message: Message, state: FSMContext):
    await state.clear()
    from keyboards.admin_kb import admin_panel_keyboard
    await message.answer("Хабарлама жіберу тоқтатылды.", reply_markup=admin_panel_keyboard())

@router.message(StateFilter(BroadcastState.text))
async def broadcast_text(message: Message, state: FSMContext):
    await state.update_data(text=message.html_text)
    await message.answer("Одан кейін батырма мәтінін енгізіңіз немесе өткізіп жіберіңіз:", reply_markup=skip_markup())
    await state.set_state(BroadcastState.button_text)

@router.message(StateFilter(BroadcastState.button_text))
async def broadcast_btn_text(message: Message, state: FSMContext):
    if message.text == "⏩ Өткізіп жіберу":
        await state.update_data(button_text=None, button_url=None)
        await show_preview(message, state)
    else:
        await state.update_data(button_text=message.text)
        await message.answer("Батырма сілтемесін (URL) енгізіңіз (міндетті түрде http немесе https арқылы басталуы керек):", reply_markup=cancel_markup())
        await state.set_state(BroadcastState.button_url)

@router.message(StateFilter(BroadcastState.button_url))
async def broadcast_btn_url(message: Message, state: FSMContext):
    if not message.text.startswith("http"):
        await message.answer("Сілтеме `http://` немесе `https://` арқылы басталуы керек. Қайта енгізіңіз:")
        return
    await state.update_data(button_url=message.text)
    await show_preview(message, state)

async def show_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    text = data.get("text")
    btn_text = data.get("button_text")
    btn_url = data.get("button_url")
    
    markup = None
    if btn_text and btn_url:
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=btn_text, url=btn_url)]])
        
    await message.answer(f"<b>Алдын ала қарау:</b>\n\n{text}", reply_markup=markup, parse_mode="HTML")
    await message.answer("Жіберуді растайсыз ба?", reply_markup=confirm_markup())
    await state.set_state(BroadcastState.confirm)

@router.message(StateFilter(BroadcastState.confirm), F.text == "✅ Жіберу")
async def confirm_broadcast(message: Message, state: FSMContext, bot: Bot, db_session: AsyncSession):
    data = await state.get_data()
    text = data.get("text")
    btn_text = data.get("button_text")
    btn_url = data.get("button_url")
    await state.clear()
    
    from keyboards.admin_kb import admin_panel_keyboard
    await message.answer("Жіберілуде...", reply_markup=admin_panel_keyboard())
    
    markup = None
    if btn_text and btn_url:
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=btn_text, url=btn_url)]])
        
    users = await db_session.scalars(select(User.tg_id))
    success = 0
    fail = 0
    
    for tg_id in users:
        try:
            await bot.send_message(chat_id=tg_id, text=text, reply_markup=markup, parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1
            
    await message.answer(f"📢 Жіберу аяқталды!\n\n✅ Сәтті: {success}\n❌ Қатемен: {fail}")
