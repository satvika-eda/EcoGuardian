import requests
import os
from tools.helpers import get_coords

OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY")

def get_air_quality(city: str):
    """Return air quality (PM2.5 + all pollutants) from OpenAQ v3."""
    if not OPENAQ_API_KEY:
        return {"status": "error", "message": "Missing OPENAQ_API_KEY"}

    headers = {
        "X-API-Key": OPENAQ_API_KEY,
        "User-Agent": "EcoGuardian/1.0"
    }

    # STEP 1 — Geocode
    lat, lon = get_coords(city)
    if lat is None:
        return {"status": "error", "message": f"Could not geocode: {city}"}

    # STEP 2 — Find nearest monitoring station
    loc_url = "https://api.openaq.org/v3/locations"
    loc_params = {
        "coordinates": f"{lat},{lon}",
        "radius": 25000,   # 25 km
        "limit": 1,
        "isMonitor": True
    }

    loc_resp = requests.get(loc_url, params=loc_params, headers=headers).json()
    print("[DEBUG] /locations:", loc_resp)

    if not loc_resp.get("results"):
        return {"status": "error", "message": "No monitoring stations nearby!", "raw": loc_resp}

    station = loc_resp["results"][0]
    station_id = station["id"]
    print("[DEBUG] station_id:", station_id)

    # sensorId → parameter name mapping
    sensor_map = {
        s["id"]: {
            "name": s["parameter"]["name"],
            "units": s["parameter"]["units"],
        }
        for s in station.get("sensors", [])
    }

    # STEP 3 — Fetch LATEST readings
    latest_url = f"https://api.openaq.org/v3/locations/{station_id}/latest"
    latest_resp = requests.get(latest_url, headers=headers).json()

    print("[DEBUG] /latest:", latest_resp)

    if not latest_resp.get("results"):
        return {
            "status": "error",
            "message": "No latest data for this station",
            "station_id": station_id,
            "raw": latest_resp
        }

    # STEP 4 — Extract ALL pollutant values with metadata
    components = {}

    for m in latest_resp["results"]:
        sensor_id = m.get("sensorsId")
        meta = sensor_map.get(sensor_id)

        if not meta:
            continue

        param = meta["name"]
        units = meta["units"]

        components[param] = {
            "value": m.get("value"),
            "units": units,
            "datetime_utc": m["datetime"]["utc"],
            "datetime_local": m["datetime"]["local"],
            "coordinates": m.get("coordinates"),
            "sensor_id": sensor_id,
        }

    return {
        "status": "success",
        "source": "OpenAQ",
        "input_city": city,
        "coords": {"lat": lat, "lon": lon},
        "station": {
            "id": station_id,
            "name": station.get("name"),
            "country": station.get("country", {}).get("name"),
        },
        "components": components,  # ALL pollutants with metadata
        "latest_raw": latest_resp,
    }
