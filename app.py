import os
import json
import requests
from fastapi import FastAPI, Request, Header
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CRON_SECRET = os.getenv("CRON_SECRET")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
USERS_FILE = "users.json"

app = FastAPI()


# =====================================================
# Utilities
# =====================================================

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def send_message(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )
    except Exception as e:
        print("Telegram send error:", e)


def get_weather(city):
    try:
        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        ).json()

        if "results" not in geo or not geo["results"]:
            return None

        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]

        weather = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        ).json()

        if "current_weather" not in weather:
            return None

        temp = weather["current_weather"]["temperature"]
        return f"🌡️ {temp}°C"

    except Exception as e:
        print("Weather API error:", e)
        return None


def get_prayer_times(city):
    try:
        data = requests.get(
            f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=Germany&method=3"
        ).json()

        if "data" not in data:
            return None

        timings = data["data"]["timings"]

        return (
            f"الفجر: {timings.get('Fajr','-')}\n"
            f"الظهر: {timings.get('Dhuhr','-')}\n"
            f"المغرب: {timings.get('Maghrib','-')}"
        )
    except Exception as e:
        print("Prayer API error:", e)
        return None


def build_daily_message(city):
    weather = get_weather(city)
    prayers = get_prayer_times(city)

    if weather is None:
        return None

    return f"""
🌬️ Naseem | نسيم

🌦️ طقس اليوم – {city}
{weather}

🕌 أوقات الصلاة
{prayers if prayers else "غير متاحة حالياً"}

📅 ستصلك هذه المعلومات يومياً الساعة 4 صباحاً.
"""


# =====================================================
# Health Check
# =====================================================

@app.get("/")
def health():
    return {"status": "Naseem Webhook Running"}


# =====================================================
# Telegram Webhook
# =====================================================

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()

        if "message" not in data:
            return {"ok": True}

        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()

        if not text:
            return {"ok": True}

        # منع استخدام /
        if text.startswith("/"):
            send_message(chat_id, "✍️ فقط اكتب اسم مدينتك بدون /")
            return {"ok": True}

        users = load_users()

        # =============================================
        # أول تسجيل
        # =============================================
        if str(chat_id) not in users:
            message = build_daily_message(text)

            if message is None:
                send_message(
                    chat_id,
                    "❌ لم أستطع العثور على المدينة.\n"
                    "تأكد من كتابة الاسم بالإنجليزية مثل:\nBerlin"
                )
                return {"ok": True}

            users[str(chat_id)] = {"city": text}
            save_users(users)

            send_message(
                chat_id,
                f"🎉 شكراً لاشتراكك في Naseem!\n\n{message}"
            )
            return {"ok": True}

        # =============================================
        # مستخدم مسجل
        # =============================================
        city = users[str(chat_id)]["city"]

        # إذا كتب نفس المدينة → أرسل المعلومات
        if text.lower() == city.lower():
            message = build_daily_message(city)
            if message:
                send_message(chat_id, message)
            return {"ok": True}

        # تغيير المدينة
        if text.lower() in ["تغيير", "change", "reset"]:
            del users[str(chat_id)]
            save_users(users)
            send_message(chat_id, "✏️ أرسل اسم مدينتك الجديدة.")
            return {"ok": True}

        # أي نص آخر
        send_message(
            chat_id,
            f"📍 مدينتك الحالية: {city}\n\n"
            "إذا أردت تحديث المعلومات اكتب اسم المدينة مرة أخرى.\n"
            "أو اكتب 'تغيير' لتحديث مدينتك."
        )

        return {"ok": True}

    except Exception as e:
        print("Webhook error:", e)
        return {"ok": True}


# =====================================================
# Daily Cron Endpoint (4 AM)
# =====================================================

@app.post("/daily")
async def daily_broadcast(x_cron_secret: str = Header(None)):
    if x_cron_secret != CRON_SECRET:
        return {"error": "unauthorized"}

    users = load_users()

    for user_id, data in users.items():
        city = data["city"]
        message = build_daily_message(city)

        if message:
            send_message(int(user_id), message)

    return {"status": "daily messages sent"}
