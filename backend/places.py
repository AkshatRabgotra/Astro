"""Comprehensive global place search and geocoding engine.

Combines high-speed curated in-memory database with Open-Meteo & OpenStreetMap
Nominatim live global geocoding to cover every city, district, town, and village on Earth.
"""

import logging
from typing import Any, Dict, List
import httpx

logger = logging.getLogger("melooha.places")

# High-priority curated cities for instant zero-latency responses
CITIES_DB: List[Dict[str, Any]] = [
    # Jammu & Kashmir / Ladakh
    {"name": "Jammu, Jammu and Kashmir, India", "lat": 32.7353, "lon": 74.8617, "tz": "Asia/Kolkata"},
    {"name": "Srinagar, Jammu and Kashmir, India", "lat": 34.0837, "lon": 74.7973, "tz": "Asia/Kolkata"},
    {"name": "Udhampur, Jammu and Kashmir, India", "lat": 32.9250, "lon": 75.1417, "tz": "Asia/Kolkata"},
    {"name": "Kathua, Jammu and Kashmir, India", "lat": 32.3694, "lon": 75.5254, "tz": "Asia/Kolkata"},
    {"name": "Anantnag, Jammu and Kashmir, India", "lat": 33.7307, "lon": 75.1542, "tz": "Asia/Kolkata"},
    {"name": "Baramulla, Jammu and Kashmir, India", "lat": 34.2000, "lon": 74.3500, "tz": "Asia/Kolkata"},
    {"name": "Katra, Jammu and Kashmir, India", "lat": 32.9922, "lon": 74.9317, "tz": "Asia/Kolkata"},
    {"name": "Leh, Ladakh, India", "lat": 34.1526, "lon": 77.5771, "tz": "Asia/Kolkata"},
    {"name": "Rajouri, Jammu and Kashmir, India", "lat": 33.3812, "lon": 74.3142, "tz": "Asia/Kolkata"},
    {"name": "Poonch, Jammu and Kashmir, India", "lat": 33.7667, "lon": 74.1000, "tz": "Asia/Kolkata"},

    # Top Indian Metros & State Capitals
    {"name": "Mumbai, Maharashtra, India", "lat": 19.0760, "lon": 72.8777, "tz": "Asia/Kolkata"},
    {"name": "New Delhi, Delhi, India", "lat": 28.6139, "lon": 77.2090, "tz": "Asia/Kolkata"},
    {"name": "Bengaluru, Karnataka, India", "lat": 12.9716, "lon": 77.5946, "tz": "Asia/Kolkata"},
    {"name": "Hyderabad, Telangana, India", "lat": 17.3850, "lon": 78.4867, "tz": "Asia/Kolkata"},
    {"name": "Ahmedabad, Gujarat, India", "lat": 23.0225, "lon": 72.5714, "tz": "Asia/Kolkata"},
    {"name": "Chennai, Tamil Nadu, India", "lat": 13.0827, "lon": 80.2707, "tz": "Asia/Kolkata"},
    {"name": "Kolkata, West Bengal, India", "lat": 22.5726, "lon": 88.3639, "tz": "Asia/Kolkata"},
    {"name": "Surat, Gujarat, India", "lat": 21.1702, "lon": 72.8311, "tz": "Asia/Kolkata"},
    {"name": "Pune, Maharashtra, India", "lat": 18.5204, "lon": 73.8567, "tz": "Asia/Kolkata"},
    {"name": "Jaipur, Rajasthan, India", "lat": 26.9124, "lon": 75.7873, "tz": "Asia/Kolkata"},
    {"name": "Lucknow, Uttar Pradesh, India", "lat": 26.8467, "lon": 80.9462, "tz": "Asia/Kolkata"},
    {"name": "Kanpur, Uttar Pradesh, India", "lat": 26.4499, "lon": 80.3319, "tz": "Asia/Kolkata"},
    {"name": "Nagpur, Maharashtra, India", "lat": 21.1458, "lon": 79.0882, "tz": "Asia/Kolkata"},
    {"name": "Indore, Madhya Pradesh, India", "lat": 22.7196, "lon": 75.8577, "tz": "Asia/Kolkata"},
    {"name": "Thane, Maharashtra, India", "lat": 19.2183, "lon": 72.9781, "tz": "Asia/Kolkata"},
    {"name": "Bhopal, Madhya Pradesh, India", "lat": 23.2599, "lon": 77.4126, "tz": "Asia/Kolkata"},
    {"name": "Visakhapatnam, Andhra Pradesh, India", "lat": 17.6868, "lon": 83.2185, "tz": "Asia/Kolkata"},
    {"name": "Patna, Bihar, India", "lat": 25.5941, "lon": 85.1376, "tz": "Asia/Kolkata"},
    {"name": "Vadodara, Gujarat, India", "lat": 22.3072, "lon": 73.1812, "tz": "Asia/Kolkata"},
    {"name": "Ghaziabad, Uttar Pradesh, India", "lat": 28.6692, "lon": 77.4538, "tz": "Asia/Kolkata"},
    {"name": "Ludhiana, Punjab, India", "lat": 30.9010, "lon": 75.8573, "tz": "Asia/Kolkata"},
    {"name": "Agra, Uttar Pradesh, India", "lat": 27.1767, "lon": 78.0081, "tz": "Asia/Kolkata"},
    {"name": "Nashik, Maharashtra, India", "lat": 19.9975, "lon": 73.7898, "tz": "Asia/Kolkata"},
    {"name": "Faridabad, Haryana, India", "lat": 28.4089, "lon": 77.3178, "tz": "Asia/Kolkata"},
    {"name": "Meerut, Uttar Pradesh, India", "lat": 28.9845, "lon": 77.7064, "tz": "Asia/Kolkata"},
    {"name": "Rajkot, Gujarat, India", "lat": 22.3039, "lon": 70.8022, "tz": "Asia/Kolkata"},
    {"name": "Varanasi, Uttar Pradesh, India", "lat": 25.3176, "lon": 82.9739, "tz": "Asia/Kolkata"},
    {"name": "Aurangabad, Maharashtra, India", "lat": 19.8762, "lon": 75.3433, "tz": "Asia/Kolkata"},
    {"name": "Dhanbad, Jharkhand, India", "lat": 23.7957, "lon": 86.4304, "tz": "Asia/Kolkata"},
    {"name": "Amritsar, Punjab, India", "lat": 31.6340, "lon": 74.8723, "tz": "Asia/Kolkata"},
    {"name": "Navi Mumbai, Maharashtra, India", "lat": 19.0330, "lon": 73.0297, "tz": "Asia/Kolkata"},
    {"name": "Allahabad (Prayagraj), UP, India", "lat": 25.4358, "lon": 81.8463, "tz": "Asia/Kolkata"},
    {"name": "Ranchi, Jharkhand, India", "lat": 23.3441, "lon": 85.3096, "tz": "Asia/Kolkata"},
    {"name": "Howrah, West Bengal, India", "lat": 22.5958, "lon": 88.2636, "tz": "Asia/Kolkata"},
    {"name": "Coimbatore, Tamil Nadu, India", "lat": 11.0168, "lon": 76.9558, "tz": "Asia/Kolkata"},
    {"name": "Jabalpur, Madhya Pradesh, India", "lat": 23.1815, "lon": 79.9864, "tz": "Asia/Kolkata"},
    {"name": "Gwalior, Madhya Pradesh, India", "lat": 26.2183, "lon": 78.1828, "tz": "Asia/Kolkata"},
    {"name": "Vijayawada, Andhra Pradesh, India", "lat": 16.5062, "lon": 80.6480, "tz": "Asia/Kolkata"},
    {"name": "Jodhpur, Rajasthan, India", "lat": 26.2389, "lon": 73.0243, "tz": "Asia/Kolkata"},
    {"name": "Madurai, Tamil Nadu, India", "lat": 9.9252, "lon": 78.1198, "tz": "Asia/Kolkata"},
    {"name": "Raipur, Chhattisgarh, India", "lat": 21.2514, "lon": 81.6296, "tz": "Asia/Kolkata"},
    {"name": "Kota, Rajasthan, India", "lat": 25.2138, "lon": 75.8648, "tz": "Asia/Kolkata"},
    {"name": "Chandigarh, India", "lat": 30.7333, "lon": 76.7794, "tz": "Asia/Kolkata"},
    {"name": "Guwahati, Assam, India", "lat": 26.1445, "lon": 91.7362, "tz": "Asia/Kolkata"},

    # Global Centers
    {"name": "Austin, Texas, USA", "lat": 30.2672, "lon": -97.7431, "tz": "America/Chicago"},
    {"name": "New York, USA", "lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"},
    {"name": "San Francisco, USA", "lat": 37.7749, "lon": -122.4194, "tz": "America/Los_Angeles"},
    {"name": "Seattle, USA", "lat": 47.6062, "lon": -122.3321, "tz": "America/Los_Angeles"},
    {"name": "Chicago, USA", "lat": 41.8781, "lon": -87.6298, "tz": "America/Chicago"},
    {"name": "London, UK", "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London"},
    {"name": "Dubai, UAE", "lat": 25.2048, "lon": 55.2708, "tz": "Asia/Dubai"},
    {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "tz": "Asia/Singapore"},
    {"name": "Toronto, Canada", "lat": 43.6532, "lon": -79.3832, "tz": "America/Toronto"},
    {"name": "Sydney, Australia", "lat": -33.8688, "lon": 151.2093, "tz": "Australia/Sydney"},
    {"name": "Tokyo, Japan", "lat": 35.6762, "lon": 139.6503, "tz": "Asia/Tokyo"},
    {"name": "Paris, France", "lat": 48.8566, "lon": 2.3522, "tz": "Europe/Paris"},
    {"name": "Berlin, Germany", "lat": 52.5200, "lon": 13.4050, "tz": "Europe/Berlin"},
]


STATE_ABBREVIATIONS = {
    "jk": "jammu and kashmir",
    "j&k": "jammu and kashmir",
    "up": "uttar pradesh",
    "u.p.": "uttar pradesh",
    "mp": "madhya pradesh",
    "m.p.": "madhya pradesh",
    "mh": "maharashtra",
    "tn": "tamil nadu",
    "wb": "west bengal",
    "ka": "karnataka",
    "gj": "gujarat",
    "rj": "rajasthan",
    "pb": "punjab",
    "hr": "haryana",
    "dl": "delhi",
    "ncr": "delhi",
    "uk": "uttarakhand",
    "hp": "himachal pradesh",
    "ny": "new york",
    "ca": "california",
}


def _normalize_query(query: str) -> str:
    """Expand common state/regional abbreviations like 'jk', 'up', 'mh'."""
    q_clean = query.strip().lower().replace(",", " ")
    words = q_clean.split()
    expanded = []
    for w in words:
        if w in STATE_ABBREVIATIONS:
            expanded.append(STATE_ABBREVIATIONS[w])
        else:
            expanded.append(w)
    return " ".join(expanded)


def _search_open_meteo(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Query Open-Meteo Global Geocoding API (free, fast, includes IANA timezone)."""
    clean_q = query.strip().split(",")[0].strip()
    if not clean_q:
        return []

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={clean_q}&count={limit}&language=en&format=json"
    results: List[Dict[str, Any]] = []
    try:
        with httpx.Client(timeout=2.5) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("results", []):
                    name = item.get("name", "")
                    admin = item.get("admin1") or ""
                    country = item.get("country") or ""
                    parts = [name]
                    if admin and admin.lower() != name.lower():
                        parts.append(admin)
                    if country:
                        parts.append(country)

                    display_name = ", ".join(parts)
                    tz = item.get("timezone") or ("Asia/Kolkata" if country == "India" else "UTC")
                    results.append({
                        "name": display_name,
                        "lat": round(float(item["latitude"]), 4),
                        "lon": round(float(item["longitude"]), 4),
                        "tz": tz,
                    })
    except Exception as e:
        logger.debug(f"Open-Meteo geocoding non-blocking error: {e}")

    return results


def _search_nominatim(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Query OpenStreetMap Nominatim for complex or compound queries like 'jammu jk'."""
    q = query.strip()
    if not q:
        return []

    url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&addressdetails=1&limit={limit}"
    results: List[Dict[str, Any]] = []
    headers = {"User-Agent": "MeloohaAstrologyApp/1.0 (geocoding@melooha.ai)"}
    try:
        with httpx.Client(timeout=2.5, headers=headers) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for item in data:
                    raw_name = item.get("display_name", "")
                    parts = [p.strip() for p in raw_name.split(",") if not p.strip().isdigit()]
                    short_name = ", ".join(parts[:3]) if len(parts) >= 3 else raw_name
                    is_india = "India" in raw_name
                    results.append({
                        "name": short_name,
                        "lat": round(float(item["lat"]), 4),
                        "lon": round(float(item["lon"]), 4),
                        "tz": "Asia/Kolkata" if is_india else "UTC",
                    })
    except Exception as e:
        logger.debug(f"Nominatim geocoding non-blocking error: {e}")

    return results


def search_cities(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    """
    Search cities across:
    1. Fast in-memory curated cache with regional abbreviation expansion ('jk', 'up', 'mh').
    2. Open-Meteo global geocoding API for worldwide towns/cities.
    3. OpenStreetMap Nominatim for compound queries.
    """
    q_raw = query.strip()
    if not q_raw:
        return CITIES_DB[:limit]

    normalized_q = _normalize_query(q_raw)
    q_tokens = [tok.strip() for tok in normalized_q.split() if len(tok.strip()) > 1]
    matches: List[Dict[str, Any]] = []

    # 1. Multi-token match in curated database (e.g. 'jammu jk' -> 'Jammu, Jammu and Kashmir, India')
    for city in CITIES_DB:
        c_lower = city["name"].lower()
        if all(tok in c_lower for tok in q_tokens):
            matches.append(city)
            if len(matches) >= limit:
                return matches

    # Prefix match on city name parts
    q_first = q_raw.lower()
    for city in CITIES_DB:
        if city not in matches and any(part.strip().startswith(q_first) for part in city["name"].lower().split(",")):
            matches.append(city)
            if len(matches) >= limit:
                return matches

    # If we already have matches from curated fast database, return immediately without network latency
    if matches:
        return matches[:limit]

    # 2. Query Live Open-Meteo Global Geocoder (covers every town/village worldwide)
    if len(q_raw) >= 2:
        om_results = _search_open_meteo(q_raw, limit=limit)
        for res in om_results:
            if not any(abs(res["lat"] - m["lat"]) < 0.05 and abs(res["lon"] - m["lon"]) < 0.05 for m in matches):
                matches.append(res)
                if len(matches) >= limit:
                    return matches

    # 3. Query OpenStreetMap Nominatim for complex search phrases
    if len(matches) < limit and len(q_raw) >= 3:
        nom_results = _search_nominatim(q_raw, limit=limit - len(matches))
        for res in nom_results:
            if not any(abs(res["lat"] - m["lat"]) < 0.05 and abs(res["lon"] - m["lon"]) < 0.05 for m in matches):
                matches.append(res)
                if len(matches) >= limit:
                    return matches

    return matches
