import requests

WEATHER_CODES = {
    0: "☀️ صافي",
    1: "🌤️ مشمس جزئياً",
    2: "⛅ غائم جزئياً",
    3: "☁️ غائم",
    45: "🌫️ ضباب",
    48: "🌫️ ضباب كثيف",
    51: "🌦️ رذاذ",
    61: "🌧️ مطر",
    71: "❄️ ثلج",
    80: "🌧️ زخات مطر",
    95: "⛈️ عاصفة"
}

def get_coordinates(city):
    geo = requests.get(
        f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&country=DE"
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

    current = weather["current_weather"]

    temp = current["temperature"]
    wind = current["windspeed"]
    code = current["weathercode"]

    description = WEATHER_CODES.get(code, "🌡️ حالة غير معروفة")

    return (
        f"🌡️ الحرارة: {temp}°C\n"
        f"{description}\n"
        f"💨 سرعة الرياح: {wind} km/h"
    )
