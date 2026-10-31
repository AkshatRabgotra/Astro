"""Comprehensive database of major Indian and global cities with exact coordinates and timezones."""

from typing import Dict, List

CITIES_DB: List[Dict[str, any]] = [
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
    {"name": "Srinagar, Jammu and Kashmir, India", "lat": 34.0837, "lon": 74.7973, "tz": "Asia/Kolkata"},
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
    {"name": "Solapur, Maharashtra, India", "lat": 17.6599, "lon": 75.9064, "tz": "Asia/Kolkata"},
    {"name": "Hubli-Dharwad, Karnataka, India", "lat": 15.3647, "lon": 75.1240, "tz": "Asia/Kolkata"},
    {"name": "Bareilly, Uttar Pradesh, India", "lat": 28.3670, "lon": 79.4304, "tz": "Asia/Kolkata"},
    {"name": "Moradabad, Uttar Pradesh, India", "lat": 28.8351, "lon": 78.7747, "tz": "Asia/Kolkata"},
    {"name": "Mysuru (Mysore), Karnataka, India", "lat": 12.2958, "lon": 76.6394, "tz": "Asia/Kolkata"},
    {"name": "Tiruchirappalli, Tamil Nadu, India", "lat": 10.7905, "lon": 78.7047, "tz": "Asia/Kolkata"},
    {"name": "Aligarh, Uttar Pradesh, India", "lat": 27.8974, "lon": 78.0880, "tz": "Asia/Kolkata"},
    {"name": "Jalandhar, Punjab, India", "lat": 31.3260, "lon": 75.5762, "tz": "Asia/Kolkata"},
    {"name": "Bhubaneswar, Odisha, India", "lat": 20.2961, "lon": 85.8245, "tz": "Asia/Kolkata"},
    {"name": "Salem, Tamil Nadu, India", "lat": 11.6643, "lon": 78.1460, "tz": "Asia/Kolkata"},
    {"name": "Mira-Bhayandar, Maharashtra, India", "lat": 19.2812, "lon": 72.8561, "tz": "Asia/Kolkata"},
    {"name": "Warangal, Telangana, India", "lat": 17.9689, "lon": 79.5941, "tz": "Asia/Kolkata"},
    {"name": "Thiruvananthapuram, Kerala, India", "lat": 8.5241, "lon": 76.9366, "tz": "Asia/Kolkata"},
    {"name": "Kochi, Kerala, India", "lat": 9.9312, "lon": 76.2673, "tz": "Asia/Kolkata"},
    {"name": "Kozhikode (Calicut), Kerala, India", "lat": 11.2588, "lon": 75.7804, "tz": "Asia/Kolkata"},
    {"name": "Dehradun, Uttarakhand, India", "lat": 30.3165, "lon": 78.0322, "tz": "Asia/Kolkata"},
    {"name": "Shimla, Himachal Pradesh, India", "lat": 31.1048, "lon": 77.1734, "tz": "Asia/Kolkata"},
    {"name": "Haridwar, Uttarakhand, India", "lat": 29.9457, "lon": 78.1642, "tz": "Asia/Kolkata"},
    {"name": "Ujjain, Madhya Pradesh, India", "lat": 23.1765, "lon": 75.7885, "tz": "Asia/Kolkata"},
    {"name": "Ayodhya, Uttar Pradesh, India", "lat": 26.7922, "lon": 82.1998, "tz": "Asia/Kolkata"},

    # Major International Cities
    {"name": "Dubai, United Arab Emirates", "lat": 25.2048, "lon": 55.2708, "tz": "Asia/Dubai"},
    {"name": "Abu Dhabi, United Arab Emirates", "lat": 24.4539, "lon": 54.3773, "tz": "Asia/Dubai"},
    {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "tz": "Asia/Singapore"},
    {"name": "London, United Kingdom", "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London"},
    {"name": "New York, USA", "lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"},
    {"name": "San Francisco, USA", "lat": 37.7749, "lon": -122.4194, "tz": "America/Los_Angeles"},
    {"name": "Los Angeles, USA", "lat": 34.0522, "lon": -118.2437, "tz": "America/Los_Angeles"},
    {"name": "Chicago, USA", "lat": 41.8781, "lon": -87.6298, "tz": "America/Chicago"},
    {"name": "Dallas / Houston, Texas, USA", "lat": 29.7604, "lon": -95.3698, "tz": "America/Chicago"},
    {"name": "Seattle, USA", "lat": 47.6062, "lon": -122.3321, "tz": "America/Los_Angeles"},
    {"name": "Toronto, Canada", "lat": 43.6532, "lon": -79.3832, "tz": "America/Toronto"},
    {"name": "Vancouver, Canada", "lat": 49.2827, "lon": -123.1207, "tz": "America/Vancouver"},
    {"name": "Sydney, Australia", "lat": -33.8688, "lon": 151.2093, "tz": "Australia/Sydney"},
    {"name": "Melbourne, Australia", "lat": -37.8136, "lon": 144.9631, "tz": "Australia/Melbourne"},
    {"name": "Tokyo, Japan", "lat": 35.6762, "lon": 139.6503, "tz": "Asia/Tokyo"},
    {"name": "Kuala Lumpur, Malaysia", "lat": 3.1390, "lon": 101.6869, "tz": "Asia/Kuala_Lumpur"},
    {"name": "Bangkok, Thailand", "lat": 13.7563, "lon": 100.5018, "tz": "Asia/Bangkok"},
    {"name": "Kathmandu, Nepal", "lat": 27.7172, "lon": 85.3240, "tz": "Asia/Kathmandu"},
    {"name": "Colombo, Sri Lanka", "lat": 6.9271, "lon": 79.8612, "tz": "Asia/Colombo"},
    {"name": "Dhaka, Bangladesh", "lat": 23.8103, "lon": 90.4125, "tz": "Asia/Dhaka"},
    {"name": "Paris, France", "lat": 48.8566, "lon": 2.3522, "tz": "Europe/Paris"},
    {"name": "Berlin, Germany", "lat": 52.5200, "lon": 13.4050, "tz": "Europe/Berlin"},
    {"name": "Amsterdam, Netherlands", "lat": 52.3676, "lon": 4.9041, "tz": "Europe/Amsterdam"},
]


def search_cities(query: str, limit: int = 10) -> List[Dict[str, any]]:
    """Search cities matching query prefix or substring."""
    q = query.strip().lower()
    if not q:
        return CITIES_DB[:limit]

    matches = []
    # 1. Exact / prefix matches
    for city in CITIES_DB:
        name_lower = city["name"].lower()
        if name_lower.startswith(q) or any(part.strip().startswith(q) for part in name_lower.split(",")):
            matches.append(city)
            if len(matches) >= limit:
                return matches

    # 2. Substring matches
    for city in CITIES_DB:
        if city not in matches and q in city["name"].lower():
            matches.append(city)
            if len(matches) >= limit:
                return matches

    return matches
