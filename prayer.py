import requests

def get_prayer_times(city):
    try:
        response = requests.get(
            f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=Germany&method=3",
            timeout=10
        )

        if response.status_code != 200:
            print("Prayer API status error:", response.status_code)
            return None

        data = response.json()

        if "data" not in data:
            print("Prayer API invalid structure:", data)
            return None

        timings = data["data"]["timings"]

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
