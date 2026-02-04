import requests

BASE = "https://aviationweather.gov"

class AWCError(Exception):
    pass

def _get_json(path: str, params: dict, timeout: int = 20):
    url = f"{BASE}{path}"
    r = requests.get(
        url,
        params=params,
        timeout=timeout,
        headers={"User-Agent": "drone-wx-profile/1.0 (Streamlit Community Cloud)"}
    )
    if r.status_code != 200:
        raise AWCError(f"{r.status_code} from {r.url}: {r.text[:300]}")
    return r.json()

def metar(icao: str, hours: int = 3, fmt: str = "json"):
    # /api/data/metar exists per AWC OpenAPI schema. [2](http://www.raob.com/data_sources.php)
    return _get_json("/api/data/metar", {"ids": icao.upper(), "hours": hours, "format": fmt})

def pirep_bbox(lat1, lon1, lat2, lon2, hours: int = 6, fmt: str = "json"):
    # /api/data/pirep exists per AWC OpenAPI schema. [2](http://www.raob.com/data_sources.php)
    bbox = f"{lat1:.4f},{lon1:.4f},{lat2:.4f},{lon2:.4f}"
    return _get_json("/api/data/pirep", {"bbox": bbox, "hours": hours, "format": fmt})