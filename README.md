# RAYAN STORE — Free Telegram SMM Bot

## What this starter does
- Telegram bot with menu/buttons
- Loads SMM services from `smmstores.in`
- Places orders through the standard SMM API
- Manual admin balance system
- Order status command
- Render-friendly webhook server

## Important
This free version stores balances/orders in memory. Render Free web services have an ephemeral filesystem and can restart/spin down, so user balances/orders can reset. For real money use, move balances/orders to a persistent database before going live.

## Render setup
1. Create a GitHub repository and upload these files.
2. On Render, choose **New → Web Service** and connect the repository.
3. Runtime: Python.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
6. Plan: **Free**.
7. Add environment variables:
   - `BOT_TOKEN` = your BotFather token
   - `ADMIN_ID` = `5770813197`
   - `SMM_API_URL` = `https://smmstores.in/api/v2`
   - `SMM_API_KEY` = your provider API key
8. Deploy.
9. Open the Render service URL in a browser. It should show `RAYAN STORE bot is running`.
10. Open your Telegram bot and send `/start`.

## Admin
Add balance:
`/addbalance USER_ID AMOUNT`

Check an order:
`/status ORDER_ID`

## Free-tier caveat
Render Free web services can spin down after 15 minutes without inbound traffic. A sleeping service may take about a minute to wake. This is suitable for testing, not guaranteed 24/7 production uptime.

Do not put BOT_TOKEN or SMM_API_KEY inside GitHub code. Use Render Environment Variables.
