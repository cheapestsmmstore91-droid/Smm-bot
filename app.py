import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN")
SMM_API_URL = os.getenv("SMM_API_URL")
SMM_API_KEY = os.getenv("SMM_API_KEY")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# =========================
# MAIN MENU
# =========================

def main_menu():
    kb = InlineKeyboardBuilder()

    kb.button(text="🛍️ PLACE ORDER", callback_data="place_order")
    kb.button(text="👤 MY PROFILE", callback_data="profile")

    kb.button(text="💳 ADD FUNDS", callback_data="add_funds")
    kb.button(text="📍 ORDER STATUS", callback_data="track_order")

    kb.button(text="📦 ALL ORDERS", callback_data="my_orders")
    kb.button(text="🎧 GET SUPPORT", callback_data="support")

    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()


# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🛒 <b>CHEAPEST SMM STORE</b>\n\n"
        "Welcome! Select an option below 👇",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# =========================
# PLACE ORDER
# =========================

@dp.callback_query(lambda c: c.data == "place_order")
async def place_order(callback: types.CallbackQuery):

    kb = InlineKeyboardBuilder()
    kb.button(text="📸 Instagram", callback_data="cat_instagram")
    kb.button(text="✈️ Telegram", callback_data="cat_telegram")
    kb.adjust(2)

    await callback.message.edit_text(
        "📂 <b>Select Category</b>",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )


# =========================
# INSTAGRAM
# =========================

@dp.callback_query(lambda c: c.data == "cat_instagram")
async def instagram(callback: types.CallbackQuery):

    await callback.message.edit_text(
        "📸 <b>Instagram Services</b>\n\n"
        "⭐ Instagram Reels + Video Views\n"
        "⏳ Start - 1min/30min\n"
        "⚡️ Speed - 5M/Day\n"
        "💥 Drop - Lifetime Non Drop\n"
        "🔗 Link - Video & Reel Link\n\n"
        "Service select karne ke liye API services load hongi.",
        parse_mode="HTML"
    )


# =========================
# TELEGRAM
# =========================

@dp.callback_query(lambda c: c.data == "cat_telegram")
async def telegram(callback: types.CallbackQuery):

    await callback.message.edit_text(
        "✈️ <b>Telegram Services</b>\n\n"
        "👥 Members\n"
        "👁️ Post Views\n"
        "❤️ Reactions\n\n"
        "Service select karne ke liye API services load hongi.",
        parse_mode="HTML"
    )


# =========================
# PROFILE
# =========================

@dp.callback_query(lambda c: c.data == "profile")
async def profile(callback: types.CallbackQuery):

    await callback.message.edit_text(
        f"👤 <b>MY PROFILE</b>\n\n"
        f"🆔 User ID: <code>{callback.from_user.id}</code>\n"
        f"💰 Balance: ₹0.00",
        parse_mode="HTML"
    )


# =========================
# ADD FUNDS
# =========================

@dp.callback_query(lambda c: c.data == "add_funds")
async def add_funds(callback: types.CallbackQuery):

    await callback.message.edit_text(
        "💳 <b>ADD FUNDS</b>\n\n"
        "Amount enter karo.\n"
        "Example: <code>100</code>\n\n"
        "Payment gateway connect hone ke baad "
        "payment automatically verify hoga.",
        parse_mode="HTML"
    )


# =========================
# TRACK ORDER
# =========================

@dp.callback_query(lambda c: c.data == "track_order")
async def track_order(callback: types.CallbackQuery):

    await callback.message.edit_text(
        "📍 <b>ORDER STATUS</b>\n\n"
        "Order ID bhejo.\n"
        "Example: <code>12345678</code>",
        parse_mode="HTML"
    )


# =========================
# MY ORDERS
# =========================

@dp.callback_query(lambda c: c.data == "my_orders")
async def my_orders(callback: types.CallbackQuery):

    await callback.message.edit_text(
        "📦 <b>ALL ORDERS</b>\n\n"
        "Abhi tak koi order nahi mila.",
        parse_mode="HTML"
    )


# =========================
# SUPPORT
# =========================

@dp.callback_query(lambda c: c.data == "support")
async def support(callback: types.CallbackQuery):

    await callback.message.edit_text(
        "🎧 <b>GET SUPPORT</b>\n\n"
        "Support ke liye admin se contact karein.",
        parse_mode="HTML"
    )


# =========================
# RUN
# =========================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":

    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    tg_app.run_polling()
