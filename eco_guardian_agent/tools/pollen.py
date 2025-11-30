import requests
from tools.helpers import get_coords, get_zip_from_coords

def get_pollen(city: str):
    """Fetch pollen levels (tree, grass, weed) using Pollen.com unofficial API."""
    
    # Step 1: Get lat/lon
    lat, lon = get_coords(city)
    if lat is None:
        return {"status": "error", "message": f"City not found: {city}"}

    # Step 2: Get ZIP code (required by pollen.com)
    zipcode = get_zip_from_coords(lat, lon)
    if not zipcode:
        return {"status": "error", "message": f"Cannot find ZIP code for city: {city}"}

    # Step 3: Query pollen.com
    url = f"https://www.pollen.com/api/forecast/current/pollen/{zipcode}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.pollen.com",
    }

    resp = requests.get(url, headers=headers).json()
    print("[DEBUG] pollen.com response:", resp)

    if "Location" not in resp:
        return {"status": "error", "message": "Pollen data not available", "raw": resp}

    # Extract today's pollen data
    periods = resp["Location"]["periods"]
    primary = periods[1] if len(periods) > 1 else periods[0]

    # Fix: Triggers may be [] or {}
    triggers = primary.get("Triggers", {})
    if isinstance(triggers, list):
        triggers = {}

    tree = triggers.get("Tree", {})
    grass = triggers.get("Grass", {})
    weed = triggers.get("Weed", {})

    return {
        "status": "success",
        "city": city,
        "zipcode": zipcode,
        "lat": lat,
        "lon": lon,
        "tree_pollen": tree,
        "grass_pollen": grass,
        "weed_pollen": weed,
        "raw": resp
    }