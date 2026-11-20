# LuckyLab — Number Selection Experience

A clean Django number-selection experience with two-stage Telegram admin review (Approve / Reject).

## Features
- Platform selection: Spin City, MWNOS, Africanbet
- Virtual points amount (1–10,000)
- Phone number **first**, then four lucky digits (0–9, unique)
- Six lucky numbers (0–49, unique)
- Auto-advance to the next box when you type a number
- **Two-stage Telegram approval**
  1. After phone + four digits → Telegram Approve / Reject. Only if approved can the user open the six-number page.
  2. After six numbers → second Telegram Approve / Reject (final).
- Waiting page after stage 1 (auto-refreshes)
- Final page tells the customer to wait for results (auto-refreshes until you decide)
- Session receipt with reference
- Responsible Gaming footer
- Django admin for sessions and event history
- SQLite by default

## Safety and scope
This project is an entertainment number-selection experience.  
It does **not** connect to betting accounts, process real-money deposits or withdrawals, or request passwords / SMS codes / OTPs.

## Quick start
```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Put credentials in aviator.env (or .env)
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHAT_ID=...
# SECRET_KEY=...
# DEBUG=True
# ALLOWED_HOSTS=127.0.0.1,localhost

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## How to implement Telegram (step by step)

### 1. Create a bot
1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **bot token** (looks like `123456:ABC-DEF...`)

### 2. Get your chat ID
1. Start a chat with your new bot (press Start)
2. Send any message to the bot
3. Open this URL in a browser (replace TOKEN):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
4. Find `"chat":{"id": 123456789}` — that number is your **TELEGRAM_CHAT_ID**

### 3. Put credentials in the project
Edit `aviator.env` (or `.env`) in the project root:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
SECRET_KEY=any-long-random-string
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost,your-domain.com
```

### 4. Deploy so the site has a public HTTPS URL
Telegram only accepts **HTTPS** webhooks (not localhost).

**Option A — Render / Railway / any host**
- Deploy the Django app
- Note your public URL, e.g. `https://aviator00.onrender.com`

**Option B — Local testing with ngrok**
```bash
ngrok http 8000
# Copy the https URL, e.g. https://abc123.ngrok-free.app
```

### 5. Set the webhook (important)
The app listens at: **`/telegram/webhook/`**

Using the management command (recommended):
```bash
python manage.py set_telegram_webhook --url https://YOUR-DOMAIN/telegram/webhook/
```

Or with curl:
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://YOUR-DOMAIN/telegram/webhook/"
```

Check it worked:
```bash
python manage.py set_telegram_webhook --info
```

### 6. Test the flow
1. Open the site → choose platform → set points
2. Enter **phone first**, then four digits (0–9) → Submit
3. You should get a Telegram message: **Stage 1** with Approve / Reject
4. Press **Approve** → user waiting page redirects to six numbers
5. User enters six numbers (0–49) → Submit
6. You get **Stage 2** Telegram message → Approve / Reject
7. Final page on the site updates automatically

### Common problems
| Problem | Fix |
|--------|-----|
| No Telegram message | Token/Chat ID wrong, or webhook not set to HTTPS |
| Buttons do nothing | Webhook URL must end with `/telegram/webhook/` and the server must be reachable |
| `Already pending_four` | Session already decided; start a new demo |
| Localhost does not work | Use ngrok or deploy; Telegram cannot call localhost |

## Flow summary
```
Home → Amount → Phone + 4 digits → [Telegram Stage 1]
         ↓ Approve
    Six numbers → [Telegram Stage 2]
         ↓
    Final page ("wait for results" until you approve/reject)
```

## Production checklist
- Strong unique `SECRET_KEY`, `DEBUG=False`
- Correct `ALLOWED_HOSTS`
- HTTPS + secure cookies
- PostgreSQL recommended
- Keep Telegram credentials in environment variables only (never commit real tokens)
