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
    postedDatetime  - DATETIME   (of the latest snapshot used for this row)

IMPORTANT — Snapshot / revision model
--------------------------------------
The API publishes a fresh snapshot roughly every hour. Each snapshot covers a rolling
window of delivery dates and includes ALL delivery dates that were outstanding at the
time of posting.  For any given (deliveryDate, hourEnding) pair:

  • Snapshots posted BEFORE the delivery hour elapses  → genSystemWide is NULL
    (only a forecast exists; the actual has not yet been measured)
  • Snapshots posted AFTER the delivery hour elapses   → genSystemWide is non-NULL
    (actual settled generation, and the value is stable from then on)

This means the raw API response contains ~100+ duplicate rows per
(deliveryDate, hourEnding) — most of them with null actuals.  The extractor
deduplicates after fetching: it keeps only the row with the MAXIMUM postedDatetime
per (deliveryDate, hourEnding), which is the most recently settled actual (or the
latest forecast if the hour is still in the future).

Note on nighttime hours: genSystemWide = 0 (not null) for hours with no sunlight.
Nulls after deduplication indicate a genuine missing actual, not nighttime darkness.

Usage
-----
Set env vars (or use .env file), then run:

    export ERCOT_USERNAME="you@example.com"
    export ERCOT_PASSWORD="yourpassword"
    export ERCOT_SUBSCRIPTION_KEY="your_subscription_key"

    python src/extraction/ercot_spp_by_geo.py              # trial then prompt for full run
    python src/extraction/ercot_spp_by_geo.py --auto       # skip prompt, run full extract
    python src/extraction/ercot_spp_by_geo.py --trial-only # trial only (CSV)

Outputs
-------
Trial (CSV)   : data/spp_trial_geo.csv
Full (Parquet): data/spp_geo_YYYYMMDD_YYYYMMDD.parquet  (deduplicated)
The _raw.parquet (all revisions) is written as an intermediate and deleted after successful dedup.
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

        if df_raw.empty:
            raise AssertionError(
                f"Trial fetch returned 0 rows for range {date_from} -> {date_to}. "
                "Check credentials, subscription key, and date range."
            )

        missing = [c for c in KEEP_COLS if c not in df_raw.columns]
        if missing:
            raise AssertionError(
                f"Expected columns missing from API response: {missing}. "
                f"Actual columns: {list(df_raw.columns)}. "
                "Update KEEP_COLS to match the actual API schema."
            )

        df = df_raw[KEEP_COLS]

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

    def full_fetch(self, date_from: str, date_to: str, page_size: int = 1000, start_page: int = 1) -> pd.DataFrame:
        """
        Paginate all results, write raw to parquet, then deduplicate.

        The API returns ~100 revisions per (deliveryDate, hourEnding) — one per
        hourly snapshot.  Only the latest revision per key has settled actuals;
        earlier revisions have null gen* values (forecasts).  After all pages are
        written we deduplicate: keep the row with the maximum postedDatetime per
        (deliveryDate, hourEnding).

        Use start_page > 1 to resume a failed run from a specific page.  The raw
        file gets a _raw suffix; the final deduplicated file has a clean name.
        """
        log.info("=== FULL FETCH (%s -> %s, starting page %d) ===", date_from, date_to, start_page)

        params = {
            "deliveryDateFrom": date_from,
            "deliveryDateTo": date_to,
        }

        start_tag = date_from.replace("-", "")
        end_tag = date_to.replace("-", "")
        suffix = f"_from_p{start_page}" if start_page > 1 else ""
        raw_path = OUT_DIR / f"spp_geo_{start_tag}_{end_tag}{suffix}_raw.parquet"
        writer = ParquetChunkWriter(raw_path)

        try:
            rows, meta = self._client.fetch_page(SPP_ENDPOINT, params=params, page=start_page, size=page_size)
            total_pages = int(meta.get("totalPages", 1))
            total_records = int(meta.get("totalRecords", len(rows)))
            log.info("page %d/%d (%d total records)", start_page, total_pages, total_records)

            df_raw = pd.DataFrame(rows)
            available = [c for c in KEEP_COLS if c in df_raw.columns]
            writer.write(df_raw[available])

            for page in range(start_page + 1, total_pages + 1):
                rows, _ = self._client.fetch_page(SPP_ENDPOINT, params=params, page=page, size=page_size)
                log.info("page %d/%d", page, total_pages)
                writer.write(pd.DataFrame(rows)[available])
                time.sleep(1.0)
        finally:
            writer.close()

        if writer.rows_written == 0:
            raise AssertionError(
                f"Full fetch returned 0 rows for range {date_from} -> {date_to}. "
                "Check credentials and date range."
            )

        log.info("Raw rows fetched: %d  -> %s", writer.rows_written, raw_path)

        # Deduplicate: for each (deliveryDate, hourEnding) keep only the row
        # with the latest postedDatetime.  That row has settled actuals for past
        # hours; for future hours it is the most recent forecast (gen* still null).
        clean_path = OUT_DIR / f"spp_geo_{start_tag}_{end_tag}{suffix}.parquet"
        self._deduplicate(raw_path, clean_path, date_to=date_to)
        return pd.DataFrame()

    def _deduplicate(self, raw_path: Path, clean_path: Path, date_to: str) -> None:
        """
        Read raw parquet, keep max-postedDatetime row per (deliveryDate, hourEnding),
        then validate null coverage for past delivery dates.

        Known-legitimate nulls (warned but not raised):
          • DST spring-forward hour: hourEnding == 2 on a 23-hour delivery date.
            The clock jumps 1 AM → 3 AM so that hour literally never occurs.
          • Extraction boundary: hours on date_to that were not yet settled when
            the last API snapshot was published.

        Everything else that is null for a past date raises AssertionError.
        Note: genSystemWide = 0 (not null) for nighttime hours — 0 is valid, null is not.
        """
        log.info("Deduplicating %s ...", raw_path.name)
        df = pd.read_parquet(raw_path)
        raw_rows = len(df)

        # Sort descending so the first occurrence of each key is the latest posting.
        df_clean = (
            df.sort_values("postedDatetime", ascending=False)
            .drop_duplicates(subset=["deliveryDate", "hourEnding"], keep="first")
            .sort_values(["deliveryDate", "hourEnding"])
            .reset_index(drop=True)
        )

        if df_clean.empty:
            raise AssertionError(
                f"Deduplication produced 0 rows from {raw_rows} raw rows in {raw_path.name}. "
                "Something is wrong with the raw data."
            )

        # ── Null validation ──────────────────────────────────────────────────────
        today = today_ymd()
        past_null = df_clean[
            (df_clean["deliveryDate"] < today) & df_clean["genSystemWide"].isna()
        ].copy()

        if not past_null.empty:
            # Hours per date — a 23-hour day signals DST spring-forward.
            hours_per_date = df_clean.groupby("deliveryDate")["hourEnding"].count()

            # Category 1: DST spring-forward (23-hour day, missing hour is always 2).
            dst_mask = past_null.apply(
                lambda r: hours_per_date.get(r["deliveryDate"], 24) == 23
                and r["hourEnding"] == 2,
                axis=1,
            )
            dst_nulls = past_null[dst_mask]
            if not dst_nulls.empty:
                log.warning(
                    "DST spring-forward null (expected — hour 2 does not exist): %d row(s)\n%s",
                    len(dst_nulls),
                    dst_nulls[["deliveryDate", "hourEnding"]].to_string(index=False),
                )

            # Category 2: extraction boundary (hours on date_to not yet settled).
            boundary_mask = ~dst_mask & (past_null["deliveryDate"] == date_to)
            boundary_nulls = past_null[boundary_mask]
            if not boundary_nulls.empty:
                log.warning(
                    "Extraction-boundary null (hours on date_to=%s not yet settled "
                    "when snapshot was published): %d row(s) — hourEndings %s",
                    date_to,
                    len(boundary_nulls),
                    sorted(boundary_nulls["hourEnding"].tolist()),
                )

            # Everything else is an unexplained data gap — hard stop.
            unexplained = past_null[~dst_mask & ~boundary_mask]
            if not unexplained.empty:
                raise AssertionError(
                    f"{len(unexplained)} past-date row(s) have null genSystemWide "
                    f"after deduplication and are not explained by DST or the "
                    f"extraction boundary.\n"
                    f"{unexplained[['deliveryDate', 'hourEnding', 'postedDatetime']].to_string(index=False)}\n"
                    "The API never published actuals for these hours. "
                    "Inspect the raw parquet or re-run with a narrower date range."
                )

        table = pa.Table.from_pandas(df_clean, preserve_index=False)
        pq.write_table(table, clean_path, compression="snappy")

        raw_path.unlink()
        log.info("Raw parquet deleted -> %s", raw_path.name)

        non_null = df_clean["genSystemWide"].notna().sum()
        log.info(
            "Deduplication: %d raw rows -> %d unique (deliveryDate, hourEnding) pairs "
            "(%d with non-null genSystemWide, %d null/future)",
            raw_rows,
            len(df_clean),
            non_null,
            len(df_clean) - non_null,
        )
        log.info("Deduplicated Parquet saved -> %s", clean_path)


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
    parser.add_argument("--start-page", type=int, default=1, help="Resume from this page number (default: 1). Use to continue a failed run.")
    args = parser.parse_args()

    username = require_env("ERCOT_USERNAME", log)
    password = require_env("ERCOT_PASSWORD", log)
    subscription_key = require_env("ERCOT_SUBSCRIPTION_KEY", log)

    auth = ERCOTAuth(username, password, log)
    client = ERCOTAPIClient(auth, subscription_key, log)
    extractor = ERCOTSolarExtractor(client)

    if args.start_page == 1:
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
