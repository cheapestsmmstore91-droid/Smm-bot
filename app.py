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
            InlineKeyboardButton(
                "🛍 Services",
                callback_data="services"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 Balance",
                callback_data="balance"
            ),
            InlineKeyboardButton(
                "📦 My Orders",
                callback_data="orders"
            )
        ],
        [
            InlineKeyboardButton(
                "➕ Add Balance",
                callback_data="addbalance"
            )
        ],
        [
            InlineKeyboardButton(
                "ℹ️ Help",
                callback_data="help"
            )
        ]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    users.setdefault(
        uid,
        {
            "balance": 0.0,
            "orders": []
        }
    )

    await update.message.reply_text(
        "👋 Welcome to RAYAN STORE\n\n"
        "Choose an option:",
        reply_markup=menu()
    )


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Main Menu",
        reply_markup=menu()
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    users.setdefault(
        uid,
        {
            "balance": 0.0,
            "orders": []
        }
    )

    if query.data == "services":

        try:
            result = api({
                "action": "services"
            })

            if isinstance(result, list):

                lines = [
                    "🛍 Available Services\n"
                ]

                for service in result[:30]:

                    lines.append(
                        f"ID: {service.get('service')} | "
                        f"{service.get('name', 'Service')} | "
                        f"₹{service.get('rate')}/1k"
                    )

                await query.message.reply_text(
                    "\n".join(lines)
                )

            else:
                await query.message.reply_text(
                    "❌ Services load nahi ho paye."
                )

        except Exception:
            await query.message.reply_text(
                "❌ SMM API error.\n"
                "Thodi der baad try karo."
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
                "📦 My Orders\n\n"
                + "\n".join(orders[-10:])
            )

    elif query.data == "addbalance":

        await query.message.reply_text(
            "➕ Add Balance\n\n"
            "Payment ke liye admin se contact karo."
        )

    elif query.data == "help":

        await query.message.reply_text(
            "ℹ️ Help\n\n"
            "🛍 Services - available services dekho\n"
            "💰 Balance - account balance dekho\n"
            "📦 My Orders - apne orders dekho\n"
            "➕ Add Balance - balance add karne ke liye admin se contact karo"
        )


async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "📋 Menu open karne ke liye /menu bhejo.",
        reply_markup=menu()
    )


async def addbalance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "➕ Balance add karne ke liye admin se contact karo."
    )


async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        result = api({
            "action": "balance"
        })

        await update.message.reply_text(
            f"API Balance: {result.get('balance', 'N/A')}"
        )

    except Exception:

        await update.message.reply_text(
            "❌ API connection failed."
        )


@app.get("/")
def home():

    return "RAYAN STORE BOT is running", 200


def run_flask():

    port = int(
        os.getenv("PORT", "10000")
    )

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


tg_app.add_handler(
    CommandHandler("start", start)
)

tg_app.add_handler(
    CommandHandler("menu", menu_cmd)
)

tg_app.add_handler(
    CommandHandler("addbalance", addbalance)
)

tg_app.add_handler(
    CommandHandler("status", status)
)

tg_app.add_handler(
    CallbackQueryHandler(buttons)
)

tg_app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        text_handler
    )
)


if __name__ == "__main__":

    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    tg_app.run_polling()
