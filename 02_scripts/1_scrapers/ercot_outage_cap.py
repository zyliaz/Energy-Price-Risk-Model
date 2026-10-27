"""
ERCOT Public API — Hourly Resource Outage Capacity (NP3-233-CD)
===============================================================
Endpoint : GET https://api.ercot.com/api/public-reports/np3-233-cd/hourly_res_outage_cap
Auth     : Azure AD B2C ROPC flow → id_token (Bearer) + Ocp-Apim-Subscription-Key

Stores ALL hourly postings (no dedup). Each row is one forecast snapshot for a given
(operatingDate, hourEnding) pair. Downstream cleaning selects the 1-hour-ahead entries.

Live API coverage: Dec 10, 2023 → present (~4.65M records as of Sept 2026).

Schema (kept columns):
    postedDatetime              - DATETIME  (YYYY-MM-DDTHH:MM:SS)
    operatingDate               - DATE      (YYYY-MM-DD)
    hourEnding                  - INTEGER   (1–24)
    totalResourceMWZoneSouth    - INTEGER   MW
    totalResourceMWZoneNorth    - INTEGER   MW
    totalResourceMWZoneWest     - INTEGER   MW
    totalResourceMWZoneHouston  - INTEGER   MW

Usage
-----
    python 02_scripts/1_scrapers/ercot_outage_cap.py --trial-only
    python 02_scripts/1_scrapers/ercot_outage_cap.py --auto
    python 02_scripts/1_scrapers/ercot_outage_cap.py --auto --start-page 500

Outputs
-------
Trial (CSV)   : 01_data/1.2_raw_api/outage_cap_trial.csv
Full (Parquet): 01_data/1.2_raw_api/outage_cap_YYYYMMDD_YYYYMMDD.parquet
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

API_BASE = "https://api.ercot.com/api/public-reports/np3-233-cd"
ENDPOINT = f"{API_BASE}/hourly_res_outage_cap"

KEEP_COLS = [
    "postedDatetime",
    "operatingDate",
    "hourEnding",
    "totalResourceMWZoneSouth",
    "totalResourceMWZoneNorth",
    "totalResourceMWZoneWest",
    "totalResourceMWZoneHouston",
]


class ERCOTOutageCapExtractor:
    """Extract hourly resource outage capacity from ERCOT Public API (live)."""

    def __init__(self, client: ERCOTAPIClient) -> None:
        self._client = client

    def trial_fetch(self, date_from: str, date_to: str) -> pd.DataFrame:
        log.info("=== TRIAL FETCH (5 rows) ===")
        params = {
            "operatingDateFrom": date_from,
            "operatingDateTo": date_to,
        }
        rows, meta = self._client.fetch_page(ENDPOINT, params=params, page=1, size=5)
        df = pd.DataFrame(rows)

        available = [c for c in KEEP_COLS if c in df.columns]
        missing = [c for c in KEEP_COLS if c not in df.columns]
        if missing:
            log.warning("Missing columns: %s", missing)
        df = df[available]

        print("\n--- Trial result ---")
        print(f"Shape   : {df.shape}")
        print(f"Meta    : {meta}")
        print(f"Columns : {list(df.columns)}")
        print(df.to_string(index=False))
        print()

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        csv_path = OUT_DIR / "outage_cap_trial.csv"
        df.to_csv(csv_path, index=False)
        log.info("Trial CSV saved -> %s", csv_path)
        return df

    def full_fetch(
        self,
        date_from: str,
        date_to: str,
        page_size: int = 1000,
        start_page: int = 1,
    ) -> None:
        log.info("=== FULL FETCH (%s -> %s) ===", date_from, date_to)

        params = {
            "operatingDateFrom": date_from,
            "operatingDateTo": date_to,
        }

        start_tag = date_from.replace("-", "")
        end_tag = date_to.replace("-", "")
        suffix = f"_from_p{start_page}" if start_page > 1 else ""
        pq_path = OUT_DIR / f"outage_cap_{start_tag}_{end_tag}{suffix}.parquet"
        writer = ParquetChunkWriter(pq_path)

        try:
            rows, meta = self._client.fetch_page(
                ENDPOINT, params=params, page=start_page, size=page_size
            )
            total_pages = int(meta.get("totalPages", 1))
            total_records = int(meta.get("totalRecords", len(rows)))
            log.info(
                "page %d/%d (%d total records)",
                start_page, total_pages, total_records,
            )
            df = pd.DataFrame(rows)
            available = [c for c in KEEP_COLS if c in df.columns]
            writer.write(df[available])

            for page in range(start_page + 1, total_pages + 1):
                rows, _ = self._client.fetch_page(
                    ENDPOINT, params=params, page=page, size=page_size
                )
                log.info("page %d/%d", page, total_pages)
                writer.write(pd.DataFrame(rows)[available])
                time.sleep(1.0)
        finally:
            writer.close()

        if writer.rows_written == 0:
            log.warning("No data returned for the requested range.")
        else:
            log.info("Total rows fetched: %d", writer.rows_written)
            log.info("Full Parquet saved -> %s", pq_path)


def main() -> None:
    today = today_ymd()

    parser = argparse.ArgumentParser(
        description="Extract ERCOT hourly resource outage capacity (NP3-233-CD) from the live API."
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="Skip confirmation prompt and run full extract immediately.",
    )
    parser.add_argument(
        "--trial-only", action="store_true",
        help="Run trial fetch only (no full extract).",
    )
    parser.add_argument(
        "--from", dest="date_from", default="2023-12-10",
        help="Start date YYYY-MM-DD (default: 2023-12-10, earliest live coverage).",
    )
    parser.add_argument(
        "--to", dest="date_to", default=today,
        help=f"End date YYYY-MM-DD (default: today {today}).",
    )
    parser.add_argument(
        "--page-size", type=int, default=1000,
        help="Records per page (default: 1000).",
    )
    parser.add_argument(
        "--start-page", type=int, default=1,
        help="Resume from this page number (default: 1).",
    )
    args = parser.parse_args()

    username = require_env("ERCOT_USERNAME", log)
    password = require_env("ERCOT_PASSWORD", log)
    subscription_key = require_env("ERCOT_SUBSCRIPTION_KEY", log)

    auth = ERCOTAuth(username, password, log)
    client = ERCOTAPIClient(auth, subscription_key, log)
    extractor = ERCOTOutageCapExtractor(client)

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
        start_page=args.start_page,
    )


if __name__ == "__main__":
    main()
