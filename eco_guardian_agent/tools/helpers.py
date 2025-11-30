import requests

def get_coords(city: str):
    """Geocode city using Open-Meteo (free, fast, no key)."""
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    resp = requests.get(geo_url, params={"name": city, "count": 1}).json()

    if "results" not in resp or not resp["results"]:
        return None, None

    r = resp["results"][0]
    return r["latitude"], r["longitude"]

def get_zip_from_coords(lat, lon):
    """Reverse geocode coordinates → ZIP code."""
    url = "https://nominatim.openstreetmap.org/reverse"
    resp = requests.get(url, params={
        "lat": lat,
        "lon": lon,
        "format": "json"
    }, headers={"User-Agent": "EcoGuardian/1.0"}).json()

    address = resp.get("address", {})
    return address.get("postcode")
