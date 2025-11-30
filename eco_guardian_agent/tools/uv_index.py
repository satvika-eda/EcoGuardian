import requests
from tools.helpers import get_coords


def get_uv_index(city: str):
    """Retrieve UV index data (current + forecast) using Open-Meteo Air Quality API."""
    
    # Step 1: Convert city → coordinates
    lat, lon = get_coords(city)
    if lat is None:
        return {"status": "error", "message": f"City not found: {city}"}

    # Step 2: Request hourly UV index values
    uv_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "uv_index,uv_index_clear_sky"
    }

    resp = requests.get(uv_url, params=params).json()

    if "hourly" not in resp:
        return {"status": "error", "message": "UV data not available", "raw": resp}

    hourly = resp["hourly"]

    return {
        "status": "success",
        "city": city,
        "coords": {"lat": lat, "lon": lon},
        "uv_index": hourly.get("uv_index", []),
        "uv_index_clear_sky": hourly.get("uv_index_clear_sky", []),
        "raw": resp
    }