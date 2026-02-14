import requests


def get_prayer_times(city):
    try:
        response = requests.get(
            f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=DE&method=3",
            timeout=10
        )

        # تحقق من نجاح الطلب
        if response.status_code != 200:
            print("Prayer API status error:", response.status_code)
            return None

        # تحقق من أن الرد JSON
        try:
            data = response.json()
        except Exception as e:
            print("Prayer API invalid JSON:", e)
            print("Response text:", response.text)
            return None

        if not isinstance(data, dict):
            return None

        if "data" not in data:
            return None

        timings = data["data"].get("timings")

        if not timings:
            return None

        return (
            f"الفجر: {timings.get('Fajr','-')}\n"
            f"الشروق: {timings.get('Sunrise','-')}\n"
            f"الظهر: {timings.get('Dhuhr','-')}\n"
            f"العصر: {timings.get('Asr','-')}\n"
            f"المغرب: {timings.get('Maghrib','-')}\n"
            f"العشاء: {timings.get('Isha','-')}"
        )

    except Exception as e:
        print("Prayer API error:", e)
        return None
