"""
ERCOT NP3-233-CD live extraction — attempt 2 (resume from page 836)
===================================================================
Reads the partial parquet from attempt 1 (pages 1–834, ~834K rows),
fetches pages 836→end, and writes one combined parquet.

Att1 died at page 835 after 10 retries (read timeout). This script
skips the trial fetch and goes straight to resuming.
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

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


def main() -> None:
    today = today_ymd()

    parser = argparse.ArgumentParser(
        description="Resume ERCOT NP3-233-CD live extraction from a partial parquet."
    )
    parser.add_argument(
        "--start-page", type=int, required=True,
        help="First page to fetch (the one after the last successful page).",
    )
    parser.add_argument(
        "--from", dest="date_from", default="2023-12-10",
        help="Start date (must match attempt 1).",
    )
    parser.add_argument(
        "--to", dest="date_to", default=today,
        help=f"End date (default: today {today}).",
    )
    parser.add_argument(
        "--page-size", type=int, default=1000,
        help="Records per page (default: 1000).",
    )
    args = parser.parse_args()

    start_tag = args.date_from.replace("-", "")
    candidates = sorted(OUT_DIR.glob(f"outage_cap_{start_tag}_*.parquet"))
    if not candidates:
        log.error("No partial parquet found in %s matching outage_cap_%s_*.parquet", OUT_DIR, start_tag)
        raise SystemExit(1)
    existing_path = candidates[-1]

    existing_df = pd.read_parquet(existing_path)
    log.info("Loaded existing parquet: %d rows from %s", len(existing_df), existing_path)

    username = require_env("ERCOT_USERNAME", log)
    password = require_env("ERCOT_PASSWORD", log)
    subscription_key = require_env("ERCOT_SUBSCRIPTION_KEY", log)

    auth = ERCOTAuth(username, password, log)
    client = ERCOTAPIClient(auth, subscription_key, log)

    params = {
        "operatingDateFrom": args.date_from,
        "operatingDateTo": args.date_to,
    }

    end_tag = args.date_to.replace("-", "")
    out_path = OUT_DIR / f"outage_cap_{start_tag}_{end_tag}.parquet"

    writer = ParquetChunkWriter(out_path)

    try:
        available = [c for c in KEEP_COLS if c in existing_df.columns]
        writer.write(existing_df[available])
        log.info("Wrote %d existing rows to new parquet", len(existing_df))

        rows, meta = client.fetch_page(
            ENDPOINT, params=params, page=args.start_page, size=args.page_size
        )
        total_pages = int(meta.get("totalPages", 1))
        total_records = int(meta.get("totalRecords", len(rows)))
        log.info(
            "Resuming: page %d/%d (%d total records)",
            args.start_page, total_pages, total_records,
        )
        writer.write(pd.DataFrame(rows)[available])

        for page in range(args.start_page + 1, total_pages + 1):
            rows, _ = client.fetch_page(
                ENDPOINT, params=params, page=page, size=args.page_size
            )
            log.info("page %d/%d", page, total_pages)
            writer.write(pd.DataFrame(rows)[available])
            time.sleep(1.0)
    finally:
        writer.close()

    log.info("Total rows in combined parquet: %d", writer.rows_written)
    log.info("Saved -> %s", out_path)


if __name__ == "__main__":
    main()
