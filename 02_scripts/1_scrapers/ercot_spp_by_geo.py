"""
ERCOT Public API — Solar Power Production Hourly by Geographical Region
=======================================================================
Endpoint : GET https://api.ercot.com/api/public-reports/np4-745-cd/spp_hrly_actual_fcast_geo
Auth     : Azure AD B2C ROPC flow → id_token (Bearer) + Ocp-Apim-Subscription-Key

API returns all regions wide; this extractor filters client-side via KEEP_COLS.

Region → LZ_NORTH mapping (source: Wind and Solar Regions to County Mapping.xlsx):
    Solar has no "North" zone. Cross-referencing Wind North's 78 counties against all
    7 solar regions shows:
        FarEast    covers 49/78 Wind-North counties (62.8%)
        CenterEast covers 29/78 Wind-North counties (37.2%)
        FarEast + CenterEast together cover all 78 Wind-North counties exactly.
        NorthWest covers 0 Wind-North counties — name is misleading, it maps to the Panhandle.
    → Best proxies for LZ_NORTH are FarEast + CenterEast (no SystemWide needed).

Schema saved (one row per delivery date x hour ending):
    deliveryDate    - DATE       (YYYY-MM-DD)
    hourEnding      - INTEGER    (1 .. 24)
    genSystemWide   - DOUBLE     MW  — actual realized solar generation, all regions combined
    genCenterWest   - DOUBLE     MW  — actual realized solar generation, CenterWest region
    genNorthWest    - DOUBLE     MW  — actual realized solar generation, NorthWest (Panhandle) region
    genFarWest      - DOUBLE     MW  — actual realized solar generation, FarWest region
    genFarEast      - DOUBLE     MW  — actual realized solar generation, FarEast region
    genSouthEast    - DOUBLE     MW  — actual realized solar generation, SouthEast region
    genCenterEast   - DOUBLE     MW  — actual realized solar generation, CenterEast region
    DSTFlag         - BOOLEAN
    postedDatetime  - DATETIME

Usage
-----
Set env vars (or use .env file), then run:

    export ERCOT_USERNAME="you@example.com"
    export ERCOT_PASSWORD="yourpassword"
    export ERCOT_SUBSCRIPTION_KEY="your_subscription_key"

    python 02_scripts/1_scrapers/ercot_spp_by_geo.py              # trial then prompt for full run
    python 02_scripts/1_scrapers/ercot_spp_by_geo.py --auto       # skip prompt, run full extract
    python 02_scripts/1_scrapers/ercot_spp_by_geo.py --trial-only # trial only (CSV)

Outputs
-------
Trial (CSV)   : 01_data/1.2_raw_api/spp_trial_geo.csv
Full (Parquet): 01_data/1.2_raw_api/spp_geo_YYYYMMDD_YYYYMMDD.parquet
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

API_BASE = "https://api.ercot.com/api/public-reports/np4-745-cd"
SPP_ENDPOINT = f"{API_BASE}/spp_hrly_actual_fcast_geo"

# ---------------------------------------------------------------------------
# Region tuning — edit KEEP_COLS to control which columns are saved.
#
# Available regions (confirmed from live API, trial run 2026-02-19):
#   SystemWide  CenterWest  NorthWest  FarWest  FarEast  SouthEast  CenterEast
#
# Each region exposes four measures (replace <Region> with the name above):
#   gen<Region>       MW  — actual realized solar generation
#   COPHSL<Region>    MW  — COP High Sustained Limit
#   STPPF<Region>     MW  — short-term solar power forecast
#   PVGRPP<Region>    MW  — PV generation resource power potential
#
# Exception: High Sustained Limit is only available system-wide → HSLSystemWide
#
# Current selection: gen-only for FarEast + CenterEast (best proxy for LZ_NORTH).
# FarEast + CenterEast together cover all 78 Wind-North counties exactly (source: county mapping xlsx).
# NorthWest sounds right but maps to the Panhandle — 0 overlap with LZ_NORTH counties.
# SystemWide excluded — not needed for zone-level analysis.
#
# To add a region's gen column, append before "DSTFlag", e.g.:
#   "genNorthWest",
#
# To add all 4 measures for a region, append its four columns before "DSTFlag", e.g.:
#   "genNorthWest", "COPHSLNorthWest", "STPPFNorthWest", "PVGRPPNorthWest",
#
# To keep all regions and measures, replace the list with:
#   available = list(df_raw.columns)  # then pass available instead of KEEP_COLS
# ---------------------------------------------------------------------------
KEEP_COLS = [
    "deliveryDate",
    "hourEnding",
    "genSystemWide",
    "genCenterWest",
    "genNorthWest",
    "genFarWest",
    "genFarEast",
    "genSouthEast",
    "genCenterEast",
    "DSTFlag",
    "postedDatetime",
]


class ERCOTSolarExtractor:
    """Extract hourly solar power production by geographical region from ERCOT Public API."""

    def __init__(self, client: ERCOTAPIClient) -> None:
        self._client = client

    def trial_fetch(self, date_from: str, date_to: str) -> pd.DataFrame:
        log.info("=== TRIAL FETCH (5 rows) ===")
        params = {
            "deliveryDateFrom": date_from,
            "deliveryDateTo": date_to,
        }
        rows, meta = self._client.fetch_page(SPP_ENDPOINT, params=params, page=1, size=5)
        df_raw = pd.DataFrame(rows)

        log.info("Raw columns from API: %s", list(df_raw.columns))

        # Identify which KEEP_COLS are actually present and warn about missing ones.
        available = [c for c in KEEP_COLS if c in df_raw.columns]
        missing = [c for c in KEEP_COLS if c not in df_raw.columns]
        if missing:
            log.warning(
                "Expected columns not found in response: %s. "
                "Update KEEP_COLS to match actual API column names above.",
                missing,
            )

        df = df_raw[available]

        print("\n--- Trial result ---")
        print(f"Shape : {df.shape}")
        print(f"Meta  : {meta}")
        print(df.to_string(index=False))
        print()

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        csv_path = OUT_DIR / "spp_trial_geo.csv"
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
            "deliveryDateFrom": date_from,
            "deliveryDateTo": date_to,
        }

        start_tag = date_from.replace("-", "")
        end_tag = date_to.replace("-", "")
        pq_path = OUT_DIR / f"spp_geo_{start_tag}_{end_tag}.parquet"
        writer = ParquetChunkWriter(pq_path)

        try:
            rows, meta = self._client.fetch_page(SPP_ENDPOINT, params=params, page=1, size=page_size)
            total_pages = int(meta.get("totalPages", 1))
            total_records = int(meta.get("totalRecords", len(rows)))
            log.info("page 1/%d (%d total records)", total_pages, total_records)

            df_raw = pd.DataFrame(rows)
            available = [c for c in KEEP_COLS if c in df_raw.columns]
            writer.write(df_raw[available])

            for page in range(2, total_pages + 1):
                rows, _ = self._client.fetch_page(SPP_ENDPOINT, params=params, page=page, size=page_size)
                log.info("page %d/%d", page, total_pages)
                df_raw = pd.DataFrame(rows)
                writer.write(df_raw[available])
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
        description="Extract ERCOT solar power production hourly by geographical region (NP4-745-CD)."
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
    extractor = ERCOTSolarExtractor(client)

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
