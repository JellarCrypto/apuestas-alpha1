# scripts/pre_fetch_odds.py

import os
import sys
from datetime import datetime, timedelta, timezone
from dateutil.parser import isoparse

# ── Asegurar que el proyecto raíz está en sys.path ───────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from data_ingest import fetch_upcoming_fixtures, fetch_odds_for_fixture

def main():
    api_key = os.environ["API_FOOTBALL_KEY"]
    season  = int(os.environ.get("SEASON", "2024"))
    # Ahora usamos datetime con timezone UTC para que dt sea comparable
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=7)

    top5 = [39, 78, 140, 135, 61]  # IDs de Top5 ligas

    for league_id in top5:
        fixtures = fetch_upcoming_fixtures(league_id, season, api_key)
        for f in fixtures:
            dt = isoparse(f["fixture"]["date"])
            # dt tiene tzinfo, now también; ahora son comparables
            if now <= dt <= window_end:
                fetch_odds_for_fixture(f["fixture"]["id"], api_key)
                print(f"[pre-fetch] Fixture {f['fixture']['id']} cached at {dt.isoformat()}")

    print("[pre-fetch] ✅ Pre‑fetch completed.")

if __name__ == "__main__":
    main()
