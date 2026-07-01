"""
ERCOT Public API — Actual System Load by Forecast Zone
=======================================================
Endpoint : GET https://api.ercot.com/api/public-reports/np6-346-cd/act_sys_load_by_fzn
Auth     : Azure AD B2C ROPC flow → id_token (Bearer) + Ocp-Apim-Subscription-Key

Schema (one row per operating day x hour ending):
    operatingDay  - DATE       (YYYY-MM-DD)
    hourEnding    - VARCHAR    (HH:MM, e.g. "01:00" ... "24:00")
    north         - DOUBLE     MW
    south         - DOUBLE     MW
    west          - DOUBLE     MW
    houston       - DOUBLE     MW
    total         - DOUBLE     MW
    DSTFlag       - BOOLEAN

Usage
-----
Set env vars (or use .env file), then run:

    export ERCOT_USERNAME="you@example.com"
    export ERCOT_PASSWORD="yourpassword"
    export ERCOT_SUBSCRIPTION_KEY="your_subscription_key"

    python 02_scripts/1_scrapers/ercot_load_by_fzn.py              # trial then prompt for full run
    python 02_scripts/1_scrapers/ercot_load_by_fzn.py --auto       # skip prompt, run full extract
    python 02_scripts/1_scrapers/ercot_load_by_fzn.py --trial-only # trial only (CSV)

Outputs
-------
Trial (CSV)   : 01_data/1.2_raw_api/load_trial_fzn.csv
Full (Parquet): 01_data/1.2_raw_api/load_fzn_YYYYMMDD_YYYYMMDD.parquet
"""

from __future__ import annotations

import argparse
import logging
import time

import pandas as pd

from ercot_common import (
    OUT_DIR,
    ERCOTAPIClient,
    ERCOTAuth,
    ParquetChunkWriter,
    require_env,
    today_ymd,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

API_BASE = "https://api.ercot.com/api/public-reports/np6-346-cd"
LOAD_ENDPOINT = f"{API_BASE}/act_sys_load_by_fzn"


class ERCOTLoadExtractor:
    """Extract actual system load by forecast zone from ERCOT Public API."""

    def __init__(self, client: ERCOTAPIClient) -> None:
        self._client = client

    def trial_fetch(self, date_from: str, date_to: str) -> pd.DataFrame:
        log.info("=== TRIAL FETCH (5 rows) ===")
        params = {
            "operatingDayFrom": date_from,
            "operatingDayTo": date_to,
        }
        rows, meta = self._client.fetch_page(LOAD_ENDPOINT, params=params, page=1, size=5)
        df = pd.DataFrame(rows)

        print("\n--- Trial result ---")
        print(f"Shape : {df.shape}")
        print(f"Meta  : {meta}")
        print(df.to_string(index=False))
        print()

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        csv_path = OUT_DIR / "load_trial_fzn.csv"
        df.to_csv(csv_path, index=False)
        log.info("Trial CSV saved -> %s", csv_path)
        return df

    def full_fetch(self, date_from: str, date_to: str, page_size: int = 1000) -> pd.DataFrame:
        """
        Paginate all results in one pass and write incrementally to parquet.
        This avoids retaining the full dataset in memory.
        """
        log.info("=== FULL FETCH (%s -> %s) ===", date_from, date_to)

        params = {
            "operatingDayFrom": date_from,
            "operatingDayTo": date_to,
        }

        start_tag = date_from.replace("-", "")
        end_tag = date_to.replace("-", "")
        pq_path = OUT_DIR / f"load_fzn_{start_tag}_{end_tag}.parquet"
        writer = ParquetChunkWriter(pq_path)

        try:
            rows, meta = self._client.fetch_page(LOAD_ENDPOINT, params=params, page=1, size=page_size)
            total_pages = int(meta.get("totalPages", 1))
            total_records = int(meta.get("totalRecords", len(rows)))
            log.info("page 1/%d (%d total records)", total_pages, total_records)
            writer.write(pd.DataFrame(rows))

            for page in range(2, total_pages + 1):
                rows, _ = self._client.fetch_page(LOAD_ENDPOINT, params=params, page=page, size=page_size)
                log.info("page %d/%d", page, total_pages)
                writer.write(pd.DataFrame(rows))
                time.sleep(0.25)
        finally:
            writer.close()

        if writer.rows_written == 0:
            log.warning("No data returned for the requested range.")
            return pd.DataFrame()

        log.info("Total rows fetched: %d", writer.rows_written)
        log.info("Full Parquet saved -> %s", pq_path)
        return pd.DataFrame()


def main() -> None:
    today = today_ymd()

    parser = argparse.ArgumentParser(
        description="Extract ERCOT actual system load by forecast zone (NP6-346-CD)."
    )
    parser.add_argument("--auto", action="store_true", help="Skip confirmation prompt and run full extract immediately.")
    parser.add_argument("--trial-only", action="store_true", help="Run trial fetch only (no full extract).")
    parser.add_argument("--from", dest="date_from", default="2021-01-01", help="Start date YYYY-MM-DD (default: 2021-01-01).")
    parser.add_argument("--to", dest="date_to", default=today, help=f"End date YYYY-MM-DD (default: today {today}).")
    parser.add_argument("--page-size", type=int, default=1000, help="Records per page for full extract (default: 1000).")
    args = parser.parse_args()

    username = require_env("ERCOT_USERNAME", log)
    password = require_env("ERCOT_PASSWORD", log)
    subscription_key = require_env("ERCOT_SUBSCRIPTION_KEY", log)

    auth = ERCOTAuth(username, password, log)
    client = ERCOTAPIClient(auth, subscription_key, log)
    extractor = ERCOTLoadExtractor(client)

    extractor.trial_fetch(date_from=args.date_from, date_to=args.date_to)

    if args.trial_only:
        log.info("--trial-only flag set. Done.")
        return

    if not args.auto:
        answer = input(
            f"\nTrial successful. Proceed with full extraction "
            f"({args.date_from} -> {args.date_to})? [y/N]: "
        ).strip().lower()
        if answer not in ("y", "yes"):
            log.info("Full extraction cancelled by user.")
            return

    extractor.full_fetch(
        date_from=args.date_from,
        date_to=args.date_to,
        page_size=args.page_size,
    )


if __name__ == "__main__":
    main()
