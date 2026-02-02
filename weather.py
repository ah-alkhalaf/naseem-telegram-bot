import requests


def get_weather(city: str) -> str:
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_res = requests.get(geo_url).json()

        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&current_weather=true"
        )

        data = requests.get(weather_url).json()
        temp = data["current_weather"]["temperature"]
        wind = data["current_weather"]["windspeed"]

        return f"🌡️ {temp}°C | 💨 رياح {wind} km/h"

    except Exception:
        return "⚠️ تعذر جلب الطقس اليوم"
