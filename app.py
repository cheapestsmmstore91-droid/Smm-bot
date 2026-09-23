import os
import threading
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
SMM_API_URL = os.getenv("SMM_API_URL", "https://smmstores.in/api/v2")
SMM_API_KEY = os.getenv("SMM_API_KEY")

FORCE_CHANNEL = "@cheapest_smm_store"
FORCE_CHANNEL_URL = "https://t.me/cheapest_smm_store"

app = Flask(__name__)

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not SMM_API_KEY:
    raise RuntimeError("SMM_API_KEY is missing")

users = {}


def api(payload):
    data = {
        "key": SMM_API_KEY,
        **payload
    }

    response = requests.post(
        SMM_API_URL,
        data=data,
        timeout=30
    )

    response.raise_for_status()
    return response.json()


def menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛍 SERVICES", callback_data="services"),
        ],
        [
            InlineKeyboardButton("💰 BALANCE", callback_data="balance"),
            InlineKeyboardButton("📦 MY ORDERS", callback_data="orders"),
        ],
        [
            InlineKeyboardButton("💳 ADD BALANCE", callback_data="addbalance"),
        ],
        [
            InlineKeyboardButton("📞 SUPPORT", callback_data="help"),
        ],
    ])


def join_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=FORCE_CHANNEL_URL)],
        [InlineKeyboardButton("✅ Verify Join", callback_data="verify_join")]
    ])


async def is_joined(user_id, bot):
    try:
        member = await bot.get_chat_member(
            chat_id=FORCE_CHANNEL,
            user_id=user_id
        )
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


async def join_required(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔐 CHANNEL VERIFICATION\n\n"
        "CHEAPEST SMM STORE use karne ke liye pehle\n"
        "hamara official channel join karo.\n\n"
        "1️⃣ Join Channel\n"
        "2️⃣ Join karne ke baad Verify Join\n"
        "3️⃣ Menu automatically unlock ho jayega"
    )

    if update.callback_query:
        await update.callback_query.message.reply_text(
            text,
            reply_markup=join_menu()
        )
    elif update.message:
        await update.message.reply_text(
            text,
            reply_markup=join_menu()
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    users.setdefault(uid, {"balance": 0.0, "orders": []})

    if not await is_joined(uid, context.bot):
        await join_required(update, context)
        return

    await update.message.reply_text(
        "╔════════════════════╗\n"
        "     🛒 CHEAPEST SMM STORE\n"
        "╚════════════════════╝\n\n"
        "⚡ Fast • Reliable • Affordable\n"
        "📲 Choose an option below:",
        reply_markup=menu()
    )


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if not await is_joined(uid, context.bot):
        await join_required(update, context)
        return

    await update.message.reply_text(
        "🏠 CHEAPEST SMM STORE • MAIN MENU\n\n"
        "Select what you want to do:",
        reply_markup=menu()
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    users.setdefault(uid, {"balance": 0.0, "orders": []})

    if query.data == "verify_join":
        if await is_joined(uid, context.bot):
            await query.message.reply_text(
                "✅ JOIN VERIFIED\n\n"
                "Welcome to CHEAPEST SMM STORE ❤️\n"
                "Your menu is now unlocked.",
                reply_markup=menu()
            )
        else:
            await query.message.reply_text(
                "❌ Abhi tak channel join nahi hua.\n\n"
                "Pehle channel join karo, phir Verify Join dabao.",
                reply_markup=join_menu()
            )
        return

    if not await is_joined(uid, context.bot):
        await join_required(update, context)
        return

    if query.data == "services":
        try:
            result = api({"action": "services"})

            if isinstance(result, list):
                lines = ["🛍 Available Services\n"]

                for service in result[:30]:
                    lines.append(
                        f"ID: {service.get('service')} | "
                        f"{service.get('name', 'Service')} | "
                        f"₹{service.get('rate')}/1k"
                    )

                await query.message.reply_text("\n".join(lines))
            else:
                await query.message.reply_text(
                    "❌ Services load nahi ho paye."
                )

        except Exception:
            await query.message.reply_text(
                "❌ SMM API error.\nThodi der baad try karo."
            )

    elif query.data == "balance":
        balance = users[uid]["balance"]
        await query.message.reply_text(
            f"💰 Your Balance: ₹{balance:.2f}"
        )

    elif query.data == "orders":
        orders = users[uid]["orders"]

        if not orders:
            await query.message.reply_text(
                "📦 Abhi koi order nahi hai."
            )
        else:
            await query.message.reply_text(
                "📦 My Orders\n\n" + "\n".join(orders[-10:])
            )

    elif query.data == "addbalance":
        await query.message.reply_text(
            "➕ Add Balance\n\n"
            "Payment ke liye admin se contact karo."
        )

    elif query.data == "help":
        await query.message.reply_text(
            "📞 CHEAPEST SMM STORE SUPPORT\n\n"
            "🛍 Services — available services\n"
            "💰 Balance — account balance\n"
            "📦 My Orders — your orders\n"
            "💳 Add Balance — payment/balance help\n\n"
            "Need help? Contact the admin."
        )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if not await is_joined(uid, context.bot):
        await join_required(update, context)
        return

    await update.message.reply_text(
        "📋 Menu open karne ke liye /menu bhejo.",
        reply_markup=menu()
    )


async def addbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if not await is_joined(uid, context.bot):
        await join_required(update, context)
        return

    await update.message.reply_text(
        "➕ Balance add karne ke liye admin se contact karo."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if not await is_joined(uid, context.bot):
        await join_required(update, context)
        return

    try:
        result = api({"action": "balance"})

        await update.message.reply_text(
            f"API Balance: {result.get('balance', 'N/A')}"
        )

    except Exception:
        await update.message.reply_text(
            "❌ API connection failed."
        )


@app.get("/")
def home():
    return "CHEAPEST SMM STORE BOT is running", 200


def run_flask():
    port = int(os.getenv("PORT", "10000"))

    app.run(
        host="0.0.0.0",
        port=port,
        use_reloader=False
    )


tg_app = (
    Application
    .builder()
    .token(BOT_TOKEN)
    .build()
)

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("menu", menu_cmd))
tg_app.add_handler(CommandHandler("addbalance", addbalance))
tg_app.add_handler(CommandHandler("status", status))
tg_app.add_handler(CallbackQueryHandler(buttons))
tg_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
)

if __name__ == "__main__":
    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    tg_app.run_polling()
