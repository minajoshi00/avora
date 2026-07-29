import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

try:
    from app_paths import APP_DATA_DIR
    env_path = APP_DATA_DIR / ".env"
    load_dotenv(env_path)
except Exception:
    try:
        load_dotenv()
    except Exception:
        pass


def _normalize_location(location: str) -> str:
    return str(location or "").strip()


def get_weather_info(location: str, original_text: str = ""):
    location = _normalize_location(location)
    if not location:
        return "Tell me the city or place you want the weather for."

    try:
        api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
        if not api_key:
            return "Weather lookup is not configured yet."

        url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?q={requests.utils.quote(location)}"
            f"&appid={api_key}"
            f"&units=metric"
        )
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()

        if data.get("cod") not in (200, "200"):
            return f"I couldn't fetch weather for {location}."

        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        wind = data.get("wind", {})
        sys_info = data.get("sys", {})
        city_name = data.get("name", location)

        summary = weather.get("description", "Clear").capitalize()
        temp = main.get("temp")
        feels_like = main.get("feels_like")
        humidity = main.get("humidity")
        wind_speed = wind.get("speed")
        sunrise = sys_info.get("sunrise")
        sunset = sys_info.get("sunset")

        lines = [
            f"Weather in {city_name}: {summary}",
            f"Temperature: {temp}°C",
            f"Feels like: {feels_like}°C",
            f"Humidity: {humidity}%",
            f"Wind: {wind_speed} m/s",
        ]
        if sunrise is not None:
            lines.append(f"Sunrise: {sunrise}")
        if sunset is not None:
            lines.append(f"Sunset: {sunset}")
        return "\n".join(lines)
    except requests.RequestException as error:
        print("[Weather Request Error]", error)
        return "I couldn't reach the weather service right now."
    except Exception as error:
        print("[Weather Error]", error)
        return "I couldn't process the weather information."
