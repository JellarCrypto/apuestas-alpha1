# data_ingest.py

import os
import time
import json
import requests

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS_HOST = "api-football-v1.p.rapidapi.com"

# TheOddsAPI endpoint and league → sport_key mapping
ODDSAPI_URL = "https://api.the-odds-api.com/v4/sports"
LEAGUE_SPORT_KEYS = {
    39:  "soccer_epl",               # Premier League
    78:  "soccer_germany_bundesliga",
    140: "soccer_spain_la_liga",
    135: "soccer_italy_serie_a",
    61:  "soccer_france_ligue_one"
}
ODDSAPI_REGIONS = "uk,us,eu"

# Cache directory and TTLs (seconds)
CACHE_DIR     = "cache"
FIXTURES_TTL  = 12 * 3600   # 12 hours
ODDS_TTL      = 5  * 60     # 5 minutes

def _get(endpoint: str, params: dict, api_key: str) -> list:
    if not api_key:
        raise ValueError("Falta API_FOOTBALL_KEY en secretos.")
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": HEADERS_HOST
    }
    resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, params=params or {})
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        raise ValueError(f"Error API-Football: {data['errors']}")
    return data["response"]

def _cache_load(path: str, ttl: int):
    if os.path.exists(path) and (time.time() - os.path.getmtime(path) < ttl):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def _cache_save(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)

def fetch_upcoming_fixtures(league_id: int, season: int, api_key: str) -> list:
    cache_path = os.path.join(CACHE_DIR, f"fixtures_{league_id}_{season}.json")
    cached = _cache_load(cache_path, FIXTURES_TTL)
    if cached is not None:
        return cached
    fixtures = _get("/fixtures", {"league": league_id, "season": season}, api_key)
    _cache_save(cache_path, fixtures)
    return fixtures

def fetch_live_fixtures(api_key: str) -> list:
    return _get("/fixtures", {"live": "all"}, api_key)

def fetch_odds_alt(league_id: int, home: str, away: str) -> list:
    """
    Fallback to TheOddsAPI for 1X2 odds.
    """
    key = os.getenv("ODDS_API_KEY")
    if not key or league_id not in LEAGUE_SPORT_KEYS:
        return []
    sport_key = LEAGUE_SPORT_KEYS[league_id]
    url = f"{ODDSAPI_URL}/{sport_key}/odds"
    params = {
        "apiKey": key,
        "regions": ODDSAPI_REGIONS,
        "markets": "h2h",
        "dateFormat": "iso"
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    for match in data:
        if home.lower() in match.get("home_team","").lower() and away.lower() in match.get("away_team","").lower():
            return match.get("bookmakers", [])
    return []

def fetch_odds_for_fixture(fixture_id: int, api_key: str, bookmaker: str = None) -> list:
    cache_path = os.path.join(CACHE_DIR, f"odds_{fixture_id}.json")
    cached = _cache_load(cache_path, ODDS_TTL)
    if cached is not None:
        return cached

    params = {"fixture": fixture_id}
    if bookmaker:
        params["bookmaker"] = bookmaker

    odds = _get("/odds", params, api_key)

    if not odds:
        # attempt fallback
        # find league_id, home, away from cached fixtures
        for fname in os.listdir(CACHE_DIR):
            if fname.startswith("fixtures_") and fname.endswith(".json"):
                parts = fname.rstrip(".json").split("_")
                lid = int(parts[1])
                fixtures = json.load(open(os.path.join(CACHE_DIR, fname), "r", encoding="utf-8"))
                for f in fixtures:
                    if f["fixture"]["id"] == fixture_id:
                        home = f["teams"]["home"]["name"]
                        away = f["teams"]["away"]["name"]
                        alt = fetch_odds_alt(lid, home, away)
                        # adapt to API-Football format
                        adapted = []
                        for bm in alt:
                            outcomes = bm.get("markets", [])[0].get("outcomes", [])
                            values = [{"value": o.get("name"), "odd": o.get("price")} for o in outcomes]
                            adapted.append({
                                "bookmaker": {"name": bm.get("title")},
                                "bets": [{"name": "Match Winner", "values": values}]
                            })
                        odds = adapted
                        break
                break

    _cache_save(cache_path, odds)
    return odds
