def get_tip(weather_text: str) -> str:
    if "°C" in weather_text:
        temp = int(weather_text.split("°C")[0].split()[-1])

        if temp <= 5:
            return "❄️ الجو بارد – لا تنسَ الملابس الثقيلة"
        if temp >= 25:
            return "☀️ الجو حار – اشرب ماء كفاية"

    if "رياح" in weather_text:
        return "💨 انتبه من الرياح أثناء الخروج"

    return "✨ يومك مبارك، جعل الله فيه الخير"
