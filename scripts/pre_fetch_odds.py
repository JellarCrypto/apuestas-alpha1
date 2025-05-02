# scripts/pre_fetch_odds.py

import os
import sys
from datetime import datetime, timedelta, timezone
from dateutil.parser import isoparse
import requests

# ── Asegurar que el proyecto raíz está en sys.path ───────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from data_ingest import fetch_upcoming_fixtures, fetch_odds_for_fixture

def main():
    api_key = os.environ["API_FOOTBALL_KEY"]
    season  = int(os.environ.get("SEASON", "2024"))
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=7)
    top5 = [39, 78, 140, 135, 61]

    for league_id in top5:
        try:
            fixtures = fetch_upcoming_fixtures(league_id, season, api_key)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"[pre-fetch] ⚠️ Skipped league {league_id} due to rate limit on fixtures")
                continue
            else:
                raise

        for f in fixtures:
            dt = isoparse(f["fixture"]["date"])
            if now <= dt <= window_end:
                fid = f["fixture"]["id"]
                try:
                    fetch_odds_for_fixture(fid, api_key)
                    print(f"[pre-fetch] Fixture {fid} cached at {dt.isoformat()}")
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        print(f"[pre-fetch] ⚠️ Skipped fixture {fid} due to rate limit on odds")
                    else:
                        raise

    print("[pre-fetch] ✅ Pre‑fetch completed.")

if __name__ == "__main__":
    main()
