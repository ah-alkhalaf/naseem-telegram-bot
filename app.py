import os
import json
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

USERS_FILE = "users.json"

app = FastAPI()


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )


def get_weather(city):
    geo = requests.get(
        f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    ).json()

    lat = geo["results"][0]["latitude"]
    lon = geo["results"][0]["longitude"]

    weather = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    ).json()

    temp = weather["current_weather"]["temperature"]
    return f"🌡️ {temp}°C"


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "").strip()

    users = load_users()

    # إذا لم يسجل المستخدم بعد → أول رسالة تعتبر مدينة
    if str(chat_id) not in users:
        users[str(chat_id)] = {"city": text}
        save_users(users)

        weather = get_weather(text)

        send_message(
            chat_id,
            f"✅ تم تسجيل مدينتك: {text}\n\n{weather}"
        )
        return {"ok": True}

    # إذا كتب نفس المدينة
    if text.lower() == users[str(chat_id)]["city"].lower():
        weather = get_weather(text)
        send_message(chat_id, weather)
        return {"ok": True}

    # أي نص آخر
    send_message(
        chat_id,
        "❓ لم أفهم طلبك.\nاكتب اسم مدينتك فقط."
    )

    return {"ok": True}
