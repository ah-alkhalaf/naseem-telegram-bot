import os
import requests
from fastapi import FastAPI, Request, Header
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CRON_SECRET = os.getenv("CRON_SECRET")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = FastAPI()

# تخزين بسيط في الذاكرة
users = {}


# =========================
# Helpers
# =========================

def send_message(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )
    except Exception as e:
        print("Telegram error:", e)


def get_coordinates(city):
    geo = requests.get(
        f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&country=DE"
    ).json()

    if "results" not in geo or not geo["results"]:
        return None

    return geo["results"][0]["latitude"], geo["results"][0]["longitude"]


def get_weather(city):
    coords = get_coordinates(city)
    if not coords:
        return None

    lat, lon = coords

    weather = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    ).json()

    if "current_weather" not in weather:
        return None

    temp = weather["current_weather"]["temperature"]
    wind = weather["current_weather"]["windspeed"]

    return f"🌡️ الحرارة: {temp}°C\n💨 الرياح: {wind} km/h"


def get_prayer_times(city):
    data = requests.get(
        f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=DE&method=3"
    ).json()

    if "data" not in data:
        return None

    t = data["data"]["timings"]

    return (
        f"الفجر: {t.get('Fajr')}\n"
        f"الشروق: {t.get('Sunrise')}\n"
        f"الظهر: {t.get('Dhuhr')}\n"
        f"العصر: {t.get('Asr')}\n"
        f"المغرب: {t.get('Maghrib')}\n"
        f"العشاء: {t.get('Isha')}"
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
{prayers if prayers else "غير متاحة"}

📅 ستصلك هذه المعلومات يومياً الساعة 4 صباحاً.
"""


# =========================
# Health
# =========================

@app.get("/")
def home():
    return {"status": "Running"}


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

    # تسجيل أول مرة
    if chat_id not in users:
        msg = build_message(text)
        if not msg:
            send_message(chat_id, "❌ المدينة غير موجودة. اكتب الاسم بالإنجليزية.")
            return {"ok": True}

        users[chat_id] = text
        send_message(chat_id, f"🎉 شكراً لاشتراكك!\n\n{msg}")
        return {"ok": True}

    # مستخدم مسجل
    city = users[chat_id]

    if text.lower() == city.lower():
        msg = build_message(city)
        if msg:
            send_message(chat_id, msg)
        return {"ok": True}

    if text.lower() in ["change", "تغيير"]:
        del users[chat_id]
        send_message(chat_id, "✏️ أرسل اسم مدينتك الجديدة.")
        return {"ok": True}

    send_message(chat_id, f"مدينتك الحالية: {city}\nاكتب اسم المدينة لتحديث المعلومات.")

    return {"ok": True}


# =========================
# Cron
# =========================

@app.post("/daily")
async def daily(x_cron_secret: str = Header(None)):
    if x_cron_secret != CRON_SECRET:
        return {"error": "unauthorized"}

    for chat_id, city in users.items():
        msg = build_message(city)
        if msg:
            send_message(chat_id, msg)

    return {"status": "sent"}
