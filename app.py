import os
import threading
import asyncio
import requests

from flask import Flask, request, jsonify

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# ENVIRONMENT VARIABLES
# =========================

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

SMM_API_URL = os.getenv(
    "SMM_API_URL",
    "https://smmstores.in/api/v2"
)

SMM_API_KEY = os.environ["SMM_API_KEY"]


# =========================
# FLASK + TELEGRAM
# =========================

app = Flask(__name__)

tg_app = Application.builder().token(BOT_TOKEN).build()


# =========================
# MEMORY STORAGE
# =========================

users = {}
pending = {}


# =========================
# SMM API
# =========================

def api(payload):
    try:
        response = requests.post(
            SMM_API_URL,
            data={
                "key": SMM_API_KEY,
                **payload
            },
            timeout=20
        )

        response.raise_for_status()
        return response.json()

    except Exception as e:
        return {
            "error": str(e)
        }


# =========================
# MAIN MENU
# =========================

def main_menu():

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
                "ℹ️ Help",
                callback_data="help"
            )
        ]
    ])


# =========================
# /START
# =========================

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
        reply_markup=main_menu()
    )


# =========================
# /MENU
# =========================

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Menu:",
        reply_markup=main_menu()
    )


# =========================
# BUTTON HANDLER
# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

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

    # -------------------------
    # BALANCE
    # -------------------------

    if query.data == "balance":

        await query.edit_message_text(
            f"💰 Balance: ₹{users[uid]['balance']:.2f}",
            reply_markup=main_menu()
        )

    # -------------------------
    # ORDERS
    # -------------------------

    elif query.data == "orders":

        orders = users[uid]["orders"][-10:]

        if not orders:

            text = "📦 No orders yet."

        else:

            text = (
                "📦 Recent orders:\n\n"
                +
                "\n".join(
                    f"#{order['id']} • "
                    f"Service {order['service']} • "
                    f"{order['status']}"
                    for order in orders
                )
            )

        await query.edit_message_text(
            text,
            reply_markup=main_menu()
        )

    # -------------------------
    # HELP
    # -------------------------

    elif query.data == "help":

        await query.edit_message_text(
            "ℹ️ Help\n\n"
            "• Services → choose a service and place an order\n"
            "• Balance → see your current balance\n"
            "• My Orders → see recent orders\n"
            "• Admin can manually add balance\n\n"
            "Send /menu anytime.",
            reply_markup=main_menu()
        )

    # -------------------------
    # SERVICES
    # -------------------------

    elif query.data == "services":

        data = api({
            "action": "services"
        })

        if not isinstance(data, list):

            await query.edit_message_text(
                f"❌ Could not load services.\n{data}",
                reply_markup=main_menu()
            )

            return

        rows = []

        for service in data[:30]:

            name = str(
                service.get(
                    "name",
                    "Service"
                )
            )[:32]

            price = service.get(
                "rate",
                "?"
            )

            service_id = service.get(
                "service"
            )

            rows.append([
                InlineKeyboardButton(
                    f"{name} | {price}",
                    callback_data=f"svc:{service_id}"
                )
            ])

        rows.append([
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="back"
            )
        ])

        await query.edit_message_text(
            "🛍 Select a service:",
            reply_markup=InlineKeyboardMarkup(rows)
        )

    # -------------------------
    # SELECT SERVICE
    # -------------------------

    elif query.data.startswith("svc:"):

        service_id = query.data.split(
            ":",
            1
        )[1]

        data = api({
            "action": "services"
        })

        if not isinstance(data, list):

            await query.edit_message_text(
                "❌ Could not load services.",
                reply_markup=main_menu()
            )

            return

        service = next(
            (
                service
                for service in data
                if str(service.get("service")) == service_id
            ),
            None
        )

        if not service:

            await query.edit_message_text(
                "❌ Service not found.",
                reply_markup=main_menu()
            )

            return

        pending[uid] = {
            "service": service_id,
            "service_data": service
        }

        await query.edit_message_text(
            f"🛒 {service.get('name')}\n"
            f"Rate: {service.get('rate')}\n"
            f"Min: {service.get('min')} | "
            f"Max: {service.get('max')}\n\n"
            "Now send the post/profile URL.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "❌ Cancel",
                        callback_data="back"
                    )
                ]
            ])
        )

    # -------------------------
    # BACK
    # -------------------------

    elif query.data == "back":

        pending.pop(
            uid,
            None
        )

        await query.edit_message_text(
            "Menu:",
            reply_markup=main_menu()
        )


# =========================
# TEXT HANDLER
# =========================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    uid = update.effective_user.id

    users.setdefault(
        uid,
        {
            "balance": 0.0,
            "orders": []
        }
    )

    pending_data = pending.get(uid)

    if not pending_data:

        await update.message.reply_text(
            "Use /menu to open the menu."
        )

        return

    # -------------------------
    # URL
    # -------------------------

    if pending_data.get("url") is None:

        pending_data["url"] = (
            update.message.text.strip()
        )

        await update.message.reply_text(
            "Now send the quantity (example: 1000)."
        )

        return

    # -------------------------
    # QUANTITY
    # -------------------------

    try:

        quantity = int(
            update.message.text.strip()
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Quantity must be a number."
        )

        return

    service = pending_data["service_data"]

    min_quantity = int(
        service.get("min", 0)
    )

    max_quantity = int(
        service.get("max", 10**18)
    )

    if quantity < min_quantity or quantity > max_quantity:

        await update.message.reply_text(
            f"❌ Quantity must be between "
            f"{min_quantity} and {max_quantity}."
        )

        return

    # -------------------------
    # COST
    # -------------------------

    try:

        rate = float(
            service.get("rate", 0)
        )

        cost = (
            rate *
            quantity /
            1000.0
        )

    except Exception:

        await update.message.reply_text(
            "❌ Invalid service rate."
        )

        return

    # -------------------------
    # BALANCE CHECK
    # -------------------------

    if users[uid]["balance"] < cost:

        await update.message.reply_text(
            f"❌ Insufficient balance.\n\n"
            f"Order cost: ₹{cost:.2f}\n"
            f"Your balance: "
            f"₹{users[uid]['balance']:.2f}\n\n"
            "Ask admin to add balance."
        )

        pending.pop(
            uid,
            None
        )

        return

    # -------------------------
    # PLACE ORDER
    # -------------------------

    result = api({
        "action": "add",
        "service": pending_data["service"],
        "link": pending_data["url"],
        "quantity": quantity
    })

    if "order" not in result:

        await update.message.reply_text(
            f"❌ Order failed:\n{result}"
        )

        pending.pop(
            uid,
            None
        )

        return

    # -------------------------
    # SAVE ORDER
    # -------------------------

    users[uid]["balance"] -= cost

    order_id = str(
        result["order"]
    )

    users[uid]["orders"].append({
        "id": order_id,
        "service": pending_data["service"],
        "status": "Placed",
        "cost": cost
    })

    pending.pop(
        uid,
        None
    )

    await update.message.reply_text(
        f"✅ Order placed!\n\n"
        f"Order ID: #{order_id}\n"
        f"Quantity: {quantity}\n"
        f"Cost: ₹{cost:.2f}\n"
        f"Balance left: "
        f"₹{users[uid]['balance']:.2f}",
        reply_markup=main_menu()
    )


# =========================
# ADMIN ADD BALANCE
# =========================

async def addbalance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:

        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "Usage:\n"
            "/addbalance USER_ID AMOUNT"
        )

        return

    try:

        uid = int(
            context.args[0]
        )

        amount = float(
            context.args[1]
        )

    except ValueError:

        await update.message.reply_text(
            "Invalid USER_ID or amount."
        )

        return

    users.setdefault(
        uid,
        {
            "balance": 0.0,
            "orders": []
        }
    )

    users[uid]["balance"] += amount

    await update.message.reply_text(
        f"✅ Added ₹{amount:.2f} to {uid}."
    )


# =========================
# ORDER STATUS
# =========================

async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if len(context.args) != 1:

        await update.message.reply_text(
            "Usage:\n"
            "/status ORDER_ID"
        )

        return

    result = api({
        "action": "status",
        "order": context.args[0]
    })

    await update.message.reply_text(
        f"📦 Status:\n{result}"
    )


# =========================
# HEALTH CHECK
# =========================

@app.get("/")
def health():

    return (
        "RAYAN STORE bot is running",
        200
    )


# =========================
# TELEGRAM WEBHOOK
# =========================

@app.post("/telegram")
def telegram_webhook():

    try:

        data = request.get_json(
            force=True
        )

        update = Update.de_json(
            data,
            tg_app.bot
        )

        tg_app.create_task(
            tg_app.process_update(update)
        )

        return jsonify(
            ok=True
        )

    except Exception as e:

        return jsonify(
            ok=False,
            error=str(e)
        ), 400


# =========================
# TELEGRAM HANDLERS
# =========================

tg_app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

tg_app.add_handler(
    CommandHandler(
        "menu",
        menu
    )
)

tg_app.add_handler(
    CommandHandler(
        "addbalance",
        addbalance
    )
)

tg_app.add_handler(
    CommandHandler(
        "status",
        status
    )
)

tg_app.add_handler(
    CallbackQueryHandler(
        button
    )
)

tg_app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        text_handler
    )
)


# =========================
# START TELEGRAM
# =========================

async def start_telegram():

    await tg_app.initialize()

    await tg_app.start()

    public_url = os.getenv(
        "RENDER_EXTERNAL_URL"
    )

    if public_url:

        webhook_url = (
            public_url.rstrip("/")
            + "/telegram"
        )

        await tg_app.bot.set_webhook(
            webhook_url
        )

        print(
            "Telegram webhook set:",
            webhook_url
        )

    else:

        print(
            "WARNING: "
            "RENDER_EXTERNAL_URL not set."
        )


# =========================
# START FLASK
# =========================

def run_flask():

    port = int(
        os.getenv(
            "PORT",
            "10000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    # Start Flask in background
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    # Start Telegram application
    asyncio.run(
        start_telegram()
    )

    # Keep main process alive
    flask_thread.join()         InlineKeyboardButton("📦 My Orders", callback_data="orders")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users.setdefault(uid, {"balance": 0.0, "orders": []})
    await update.message.reply_text(
        "👋 Welcome to RAYAN STORE\n\nChoose an option:",
        reply_markup=main_menu()
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menu:", reply_markup=main_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    users.setdefault(uid, {"balance": 0.0, "orders": []})

    if q.data == "balance":
        await q.edit_message_text(
            f"💰 Balance: ₹{users[uid]['balance']:.2f}",
            reply_markup=main_menu()
        )

    elif q.data == "orders":
        orders = users[uid]["orders"][-10:]
        if not orders:
            txt = "📦 No orders yet."
        else:
            txt = "📦 Recent orders:\n\n" + "\n".join(
                f"#{o['id']} • Service {o['service']} • {o['status']}" for o in orders
            )
        await q.edit_message_text(txt, reply_markup=main_menu())

    elif q.data == "help":
        await q.edit_message_text(
            "ℹ️ Help\n\n"
            "• Services → choose a service and place an order\n"
            "• Balance → see your current balance\n"
            "• Admin can manually add balance\n\n"
            "Send /menu anytime.",
            reply_markup=main_menu()
        )

    elif q.data == "services":
        data = api({"action": "services"})
        if not isinstance(data, list):
            await q.edit_message_text(f"❌ Could not load services.\n{data}", reply_markup=main_menu())
            return
        # Keep Telegram message manageable.
        rows = []
        for s in data[:30]:
            name = str(s.get("name", "Service"))[:32]
            price = s.get("rate", "?")
            rows.append([InlineKeyboardButton(
                f"{name} | {price}",
                callback_data=f"svc:{s.get('service')}"
            )])
        rows.append([InlineKeyboardButton("⬅️ Back", callback_data="back")])
        await q.edit_message_text(
            "🛍 Select a service:",
            reply_markup=InlineKeyboardMarkup(rows)
        )

    elif q.data.startswith("svc:"):
        sid = q.data.split(":", 1)[1]
        data = api({"action": "services"})
        service = next((x for x in data if str(x.get("service")) == sid), None) if isinstance(data, list) else None
        if not service:
            await q.edit_message_text("❌ Service not found.", reply_markup=main_menu())
            return
        pending[uid] = {"service": sid, "service_data": service}
        await q.edit_message_text(
            f"🛒 {service.get('name')}\n"
            f"Rate: {service.get('rate')}\n"
            f"Min: {service.get('min')} | Max: {service.get('max')}\n\n"
            "Now send the post/profile URL.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="back")]])
        )

    elif q.data == "back":
        pending.pop(uid, None)
        await q.edit_message_text("Menu:", reply_markup=main_menu())

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users.setdefault(uid, {"balance": 0.0, "orders": []})
    p = pending.get(uid)
    if not p:
        await update.message.reply_text("Use /menu to open the menu.")
        return

    if p.get("url") is None:
        p["url"] = update.message.text.strip()
        await update.message.reply_text(
            "Now send the quantity (example: 1000)."
        )
        return

    try:
        qty = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Quantity must be a number.")
        return

    s = p["service_data"]
    min_q = int(s.get("min", 0))
    max_q = int(s.get("max", 10**18))
    if qty < min_q or qty > max_q:
        await update.message.reply_text(f"❌ Quantity must be between {min_q} and {max_q}.")
        return

    try:
        rate = float(s.get("rate", 0))
        # Standard SMM API rates are commonly per 1000 units.
        cost = rate * qty / 1000.0
    except Exception:
        await update.message.reply_text("❌ Invalid service rate.")
        return

    if users[uid]["balance"] < cost:
        await update.message.reply_text(
            f"❌ Insufficient balance.\nOrder cost: ₹{cost:.2f}\n"
            f"Your balance: ₹{users[uid]['balance']:.2f}\n\n"
            "Ask admin to add balance."
        )
        pending.pop(uid, None)
        return

    result = api({
        "action": "add",
        "service": p["service"],
        "link": p["url"],
        "quantity": qty
    })

    if "order" not in result:
        await update.message.reply_text(f"❌ Order failed:\n{result}")
        pending.pop(uid, None)
        return

    users[uid]["balance"] -= cost
    order_id = str(result["order"])
    users[uid]["orders"].append({
        "id": order_id,
        "service": p["service"],
        "status": "Placed",
        "cost": cost
    })
    pending.pop(uid, None)

    await update.message.reply_text(
        f"✅ Order placed!\n\n"
        f"Order ID: #{order_id}\n"
        f"Quantity: {qty}\n"
        f"Cost: ₹{cost:.2f}\n"
        f"Balance left: ₹{users[uid]['balance']:.2f}",
        reply_markup=main_menu()
    )

async def addbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /addbalance USER_ID AMOUNT")
        return
    try:
        uid = int(context.args[0]); amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("Invalid USER_ID or amount.")
        return
    users.setdefault(uid, {"balance": 0.0, "orders": []})
    users[uid]["balance"] += amount
    await update.message.reply_text(f"✅ Added ₹{amount:.2f} to {uid}.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /status ORDER_ID")
        return
    result = api({"action": "status", "order": context.args[0]})
    await update.message.reply_text(f"📦 Status:\n{result}")

@app.get("/")
def health():
    return "RAYAN STORE bot is running", 200

@app.post("/telegram")
def telegram_webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, tg_app.bot)
    tg_app.create_task(tg_app.process_update(update))
    return jsonify(ok=True)

def run_flask():
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

async def post_init(application):
    public_url = os.getenv("RENDER_EXTERNAL_URL")
    if public_url:
        await application.bot.set_webhook(public_url.rstrip("/") + "/telegram")
    else:
        print("RENDER_EXTERNAL_URL not set; webhook not configured automatically.")

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("menu", menu))
tg_app.add_handler(CommandHandler("addbalance", addbalance))
tg_app.add_handler(CommandHandler("status", status))
tg_app.add_handler(CallbackQueryHandler(button))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
tg_app.post_init = post_init

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    tg_app.run_polling(close_loop=False, stop_signals=None)
