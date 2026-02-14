import os
import json
from datetime import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from weather import get_weather
from prayer import get_prayer_times
from tips import get_tip

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
USERS_FILE = "users.json"


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "🌬️ *Naseem | نسيم*\n\n"
        "بوت يومي يرسل لك:\n"
        "🌦️ الطقس\n"
        "🕌 أوقات الصلاة\n"
        "🧠 نصيحة ذكية\n\n"
        "📍 أرسل مدينتك هكذا:\n"
        "`/city Berlin`"
    )
    await update.message.reply_text(message, parse_mode="Markdown")


async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ اكتب المدينة بعد الأمر\nمثال: /city Berlin")
        return

    city = " ".join(context.args)
    user_id = str(update.effective_user.id)

    users = load_users()
    users[user_id] = {"city": city}
    save_users(users)

    await update.message.reply_text(f"✅ تم حفظ مدينتك: {city}")
# 👇 إرسال الحالة فورًا
    weather = get_weather(city)
    prayers = get_prayer_times(city)
    tip = get_tip(weather)

    message = f"""
🌬️ *Naseem | نسيم*

🌦️ *طقس اليوم – {city}*
{weather}

🕌 *أوقات الصلاة*
{prayers}

🧠 *نصيحة نسيم*
{tip}
"""
    await update.message.reply_text(message, parse_mode="Markdown")

async def now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        await update.message.reply_text("❗ لم تحدد مدينة بعد. استخدم /city")
        return

    city = users[user_id]["city"]
    weather = get_weather(city)
    prayers = get_prayer_times(city)
    tip = get_tip(weather)

    message = f"""
🌬️ *Naseem | نسيم*

🌦️ *طقس اليوم – {city}*
{weather}

🕌 *أوقات الصلاة*
{prayers}

🧠 *نصيحة نسيم*
{tip}
"""
    await update.message.reply_text(message, parse_mode="Markdown")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id in users:
        del users[user_id]
        save_users(users)

    await update.message.reply_text("🛑 تم إيقاف الرسائل اليومية. نراك قريبًا 👋")


async def send_daily(context: ContextTypes.DEFAULT_TYPE):
    users = load_users()

    for user_id, data in users.items():
        city = data["city"]

        weather = get_weather(city)
        prayers = get_prayer_times(city)
        tip = get_tip(weather)

        message = f"""
🌬️ *Naseem | نسيم*

🌦️ *طقس اليوم – {city}*
{weather}

🕌 *أوقات الصلاة*
{prayers}

🧠 *نصيحة نسيم*
{tip}
"""
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Error sending to {user_id}: {e}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("city", set_city))
    app.add_handler(CommandHandler("now", now))
    app.add_handler(CommandHandler("stop", stop))
    

    # رسالة يومية الساعة 7 صباحًا
    app.job_queue.run_daily(
        send_daily,
        time=time(hour=7, minute=0)
    )

    print("✅ Naseem Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
