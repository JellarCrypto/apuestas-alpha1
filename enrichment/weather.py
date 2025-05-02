import requests
from dateutil.parser import isoparse

def fetch_weather(lat: float, lon: float, date_iso: str) -> dict:
    """
    Usa Open-Meteo (gratuito) para temp, precipitación y viento.
    """
    dt = isoparse(date_iso)
    url = "https://api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": dt.date().isoformat(),
        "end_date":   dt.date().isoformat(),
        "hourly": "temperature_2m,precipitation,windgusts_10m"
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json().get("hourly", {})
    time_str = dt.strftime("%Y-%m-%dT%H:00")
    idx = data["time"].index(time_str)
    return {
        "temperature": data["temperature_2m"][idx],
        "rain":        data["precipitation"][idx],
        "wind_speed":  data["windgusts_10m"][idx]
    }
