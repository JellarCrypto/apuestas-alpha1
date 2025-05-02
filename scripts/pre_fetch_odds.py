# scripts/pre_fetch_odds.py

import os
from datetime import datetime, timedelta
from dateutil.parser import isoparse

# Importa las funciones de tu data_ingest con cache
from data_ingest import fetch_upcoming_fixtures, fetch_odds_for_fixture

def main():
    api_key = os.environ["API_FOOTBALL_KEY"]
    season  = int(os.environ.get("SEASON", "2024"))
    now = datetime.utcnow()
    window_end = now + timedelta(days=7)

    # IDs Top5 ligas a monitorizar
    top5 = [39, 78, 140, 135, 61]

    for league_id in top5:
        # Pre‑carga fixtures próximos 7 días (usa cache FIXTURES_TTL)
        fixtures = fetch_upcoming_fixtures(league_id, season, api_key)
        for f in fixtures:
            dt = isoparse(f["fixture"]["date"])
            # solo fixtures entre ahora y window_end
            if now <= dt <= window_end:
                # Esto rellena cache/odds_<fixture_id>.json si TTL expiró
                fetch_odds_for_fixture(f["fixture"]["id"], api_key)
                print(f"[pre-fetch] Fixture {f['fixture']['id']} cached at {dt.isoformat()}")

    print("[pre-fetch] ✅ Pre‑fetch completed.")

if __name__ == "__main__":
    main()
