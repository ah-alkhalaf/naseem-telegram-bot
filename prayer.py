import requests


def get_prayer_times(city: str) -> str:
    try:
        url = (
            "https://api.aladhan.com/v1/timingsByCity"
            f"?city={city}&country=Germany&method=3"
        )

        data = requests.get(url).json()["data"]["timings"]

        return (
            f"الفجر: {data['Fajr']}\n"
            f"الظهر: {data['Dhuhr']}\n"
            f"العصر: {data['Asr']}\n"
            f"المغرب: {data['Maghrib']}\n"
            f"العشاء: {data['Isha']}"
        )

    except Exception:
        return "⚠️ تعذر جلب أوقات الصلاة"
