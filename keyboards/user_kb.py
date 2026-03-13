from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

# ─── CONTACT SHARE (first-time users) ────────────────────────────

def share_contact_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with a request_contact button for identity verification."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Контактімді жіберу", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# ─── USER KEYBOARDS ───────────────────────────────────────────────

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main dashboard keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Products"), KeyboardButton(text="💳 Top-up Balance")],
            [KeyboardButton(text="🔑 My Keys"),  KeyboardButton(text="👥 Referral")],
            [KeyboardButton(text="👤 My Profile"), KeyboardButton(text="🌐 Useful Links")],
        ],
        resize_keyboard=True
    )

def products_keyboard(products) -> InlineKeyboardMarkup:
    """One inline Buy button per product."""
    rows = []
    for p in products:
        rows.append([
            InlineKeyboardButton(
                text=f"🛍 {p.name} — {int(p.price)} ₸",
                callback_data=f"buy_{p.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
