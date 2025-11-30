import requests
from tools.helpers import get_coords

def get_weather(city: str):
    """Fetch current weather (numeric only) using Open-Meteo API."""
    
    # 1) Geocode
    lat, lon = get_coords(city)
    if lat is None:
        return {"status": "error", "message": f"Could not geocode {city}"}

    # 2) Fetch weather
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "precipitation",
            "weather_code",
            "cloud_cover"
        ],
        "timezone": "auto",
    }

    resp = requests.get(url, params=params).json()

    if "current" not in resp:
        return {"status": "error", "message": "Weather data unavailable", "raw": resp}

    c = resp["current"]

    # Return raw numerical values only
    return {
        "status": "success",
        "source": "Open-Meteo",
        "input_city": city,
        "coords": {"lat": lat, "lon": lon},

        # Raw weather metrics
        "temperature_c": c.get("temperature_2m"),
        "humidity": c.get("relative_humidity_2m"),
        "wind_speed": c.get("wind_speed_10m"),
        "wind_direction": c.get("wind_direction_10m"),
        "precipitation_mm": c.get("precipitation"),
        "cloud_cover_percent": c.get("cloud_cover"),
        "weather_code": c.get("weather_code"),   # RAW weather code only

        # Full raw data
        "raw": c
    }