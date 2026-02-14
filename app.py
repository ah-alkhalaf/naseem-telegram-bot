import os
import requests
import psycopg2
from weather import get_weather
from prayer import get_prayer_times
from fastapi import FastAPI, Request, Header
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CRON_SECRET = os.getenv("CRON_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = FastAPI()

# =========================
# Database
# =========================

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id BIGINT PRIMARY KEY,
            city TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()


def save_user(chat_id, city):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (chat_id, city)
        VALUES (%s, %s)
        ON CONFLICT (chat_id)
        DO UPDATE SET city = EXCLUDED.city
    """, (chat_id, city))
    conn.commit()
    cur.close()
    conn.close()


def get_user(chat_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT city FROM users WHERE chat_id = %s", (chat_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None


def get_all_users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT chat_id, city FROM users")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def delete_user(chat_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE chat_id = %s", (chat_id,))
    conn.commit()
    cur.close()
    conn.close()


# =========================
# Helpers
# =========================

def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

def build_message(city):
    weather = get_weather(city)
    prayers = get_prayer_times(city)

    if not weather:
        return None

    return f"""
🌬️ Naseem | نسيم

📍 {city}

{weather}

🕌 أوقات الصلاة:
{prayers if prayers else "غير متاحة حالياً"}

📅 ستصلك هذه المعلومات يومياً الساعة 4 صباحاً.
"""



# =========================
# Health
# =========================

@app.get("/")
def home():
    return {"status": "Running with PostgreSQL"}


# =========================
# Webhook
# =========================

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "").strip()

    if not text:
        return {"ok": True}

    if text.startswith("/"):
        send_message(chat_id, "✍️ فقط اكتب اسم مدينتك.")
        return {"ok": True}

    existing_city = get_user(chat_id)

    # أول تسجيل
    if not existing_city:
        msg = build_message(text)
        if not msg:
            send_message(chat_id, "❌ المدينة غير موجودة.")
            return {"ok": True}

        save_user(chat_id, text)
        send_message(chat_id, f"🎉 شكراً لاشتراكك!\n\n{msg}")
        return {"ok": True}

    # مستخدم مسجل
    if text.lower() == existing_city.lower():
        msg = build_message(existing_city)
        if msg:
            send_message(chat_id, msg)
        return {"ok": True}

    if text.lower() in ["change", "تغيير"]:
        delete_user(chat_id)
        send_message(chat_id, "✏️ أرسل اسم مدينتك الجديدة.")
        return {"ok": True}

    send_message(chat_id, f"مدينتك الحالية: {existing_city}")
    return {"ok": True}


# =========================
# Cron
# =========================

@app.post("/daily")
async def daily(x_cron_secret: str = Header(None)):
    if x_cron_secret != CRON_SECRET:
        return {"error": "unauthorized"}

    users = get_all_users()

    for chat_id, city in users:
        msg = build_message(city)
        if msg:
            send_message(chat_id, msg)

    return {"status": "sent"}
