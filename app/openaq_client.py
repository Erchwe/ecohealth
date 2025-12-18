import os
import json
import requests
from datetime import datetime
from config import OPENAQ_V3_URL, API_KEY, CITY_COORDINATES, RAW_DATA_DIR

os.makedirs(RAW_DATA_DIR, exist_ok=True)

HEADERS = {
    "X-API-Key": API_KEY
}

def fetch_city_pm25_v3(city_name: str):
    coord = CITY_COORDINATES[city_name]
    lat = coord["lat"]
    lon = coord["lon"]
    radius = coord["radius"]

    params = {
        "coordinates": f"{lat},{lon}",
        "radius": radius,
        "limit": 100
    }

    resp = requests.get(
        OPENAQ_V3_URL,
        params=params,
        headers=HEADERS,
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()

def save_raw_json(city_name: str, data: dict):
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"{city_name.lower()}_{ts}.json"
    path = os.path.join(RAW_DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

def fetch_all_cities_pm25():
    results = []
    for city in CITY_COORDINATES.keys():
        print(f"[OpenAQ v3] Fetching locations for {city}...")
        data = fetch_city_pm25_v3(city)
        save_path = save_raw_json(city, data)
        print(f"  Saved raw JSON → {save_path}")
        results.append({"city": city, "raw": data})
    return results
