"""
ERCOT Archive API — Load Historical Backfill (NP6-346-CD)
=========================================================
Endpoint : GET  https://api.ercot.com/api/public-reports/archive/NP6-346-CD
           POST https://api.ercot.com/api/public-reports/archive/NP6-346-CD/download
Auth     : Azure AD B2C ROPC flow → id_token (Bearer) + Ocp-Apim-Subscription-Key

The live API endpoint (/np6-346-cd/act_sys_load_by_fzn) only returns recent data
(Dec 2023+). This script uses the archive API to backfill 2021-01-01 – 2023-11-30,
producing a parquet with an identical schema to the live extract.

Archive API response format (differs from live public-reports endpoints):
  GET /archive/NP6-346-CD → { "_meta": { totalPages, ... }, "archives": [ { docId, ... } ] }
  (NOT the fields/data format used by parse_payload — the archive list is handled directly.)

Two-step archive flow:
  1. GET /archive/NP6-346-CD  → paginated list of docIds (one ZIP per hour)
  2. POST /archive/NP6-346-CD/download  → outer ZIP binary (batch up to 1000 docIds)
  3. Outer ZIP → inner ZIPs (one per docId) → one CSV each
  4. Read CSV → normalise columns → append to parquet

Confirmed CSV schema variations across archive vintages:
  OperatingDay / operatingDay  → operatingDay  (YYYY-MM-DD string)
  HourEnding / hourEnding      → hourEnding    (HH:MM string, may include '24:00')
  North / north                → north         (DOUBLE)
  South / south                → south
  West  / west                 → west
  Houston / houston            → houston
  Total / total                → total
  DSTFlag / DST / dstFlag      → DSTFlag       (bool)

Output schema (matches live load_fzn parquet exactly):
  operatingDay  VARCHAR
  hourEnding    VARCHAR   (preserves '24:00' edge case for downstream SQL)
  north         DOUBLE
  south         DOUBLE
  west          DOUBLE
  houston       DOUBLE
  total         DOUBLE
  DSTFlag       BOOLEAN

Usage
-----
    export ERCOT_USERNAME="you@example.com"
    export ERCOT_PASSWORD="yourpassword"
    export ERCOT_SUBSCRIPTION_KEY="your_subscription_key"

    python 02_scripts/1_scrapers/ercot_load_archive.py --trial-only
    python 02_scripts/1_scrapers/ercot_load_archive.py --auto
    python 02_scripts/1_scrapers/ercot_load_archive.py --from 2021-01-01 --to 2023-11-30 --auto

Outputs
-------
Trial (CSV)   : 01_data/1.2_raw_api/load_archive_trial.csv
Full (Parquet): 01_data/1.2_raw_api/load_archive_YYYYMMDD_YYYYMMDD.parquet
"""

from __future__ import annotations

import argparse
import io
import logging
import time
import zipfile
from datetime import datetime

import pandas as pd
import requests

from ercot_common import (
    BACKOFF_BASE,
    CONNECT_TIMEOUT,
    MAX_RETRIES,
    OUT_DIR,
    READ_TIMEOUT,
    ERCOTAuth,
    ERCOTAPIClient,
    ParquetChunkWriter,
    require_env,
)


def _validate_ymd_range(date_from: str, date_to: str) -> None:
    """Raise ValueError if dates are not valid YYYY-MM-DD or from > to."""
    fmt = "%Y-%m-%d"
    try:
        d_from = datetime.strptime(date_from, fmt)
        d_to = datetime.strptime(date_to, fmt)
    except ValueError as exc:
        raise ValueError(f"Invalid date format (expected YYYY-MM-DD): {exc}") from exc
    if d_from > d_to:
        raise ValueError(f"--from ({date_from}) must not be after --to ({date_to}).")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

ARCHIVE_BASE = "https://api.ercot.com/api/public-reports/archive/NP6-346-CD"
LIST_ENDPOINT = ARCHIVE_BASE
DOWNLOAD_ENDPOINT = f"{ARCHIVE_BASE}/download"

# Canonical output column names — must match live load_fzn parquet exactly.
OUTPUT_COLS = ["operatingDay", "hourEnding", "north", "south", "west", "houston", "total", "DSTFlag"]

# Map known archive CSV column name variants → output names.
# Confirmed 2021 archive schema: OperDay,HourEnding,NORTH,SOUTH,WEST,HOUSTON,TOTAL,DSTFlag
COLUMN_RENAMES = {
    "OperDay":      "operatingDay",   # confirmed in 2021 archive CSVs (MM/DD/YYYY format)
    "OperatingDay": "operatingDay",   # live API variant
    "HourEnding":   "hourEnding",
    "NORTH":        "north",
    "North":        "north",
    "SOUTH":        "south",
    "South":        "south",
    "WEST":         "west",
    "West":         "west",
    "HOUSTON":      "houston",
    "Houston":      "houston",
    "TOTAL":        "total",
    "Total":        "total",
    "DST":          "DSTFlag",
    "dstFlag":      "DSTFlag",
    "DstFlag":      "DSTFlag",
}

NUMERIC_COLS = {"north", "south", "west", "houston", "total"}


def _ymd_to_iso_range(date_from: str, date_to: str) -> tuple[str, str]:
    """Convert YYYY-MM-DD to ISO timestamps covering the full day range."""
    return f"{date_from}T00:00:00", f"{date_to}T23:59:59"


def _parse_load_csv(raw: bytes) -> "pd.DataFrame | None":
    """Parse raw CSV bytes from an archive ZIP, normalise columns.

    Handles known schema variations across archive vintages:
    - Column name capitalisation (OperatingDay vs operatingDay, etc.)
    - DSTFlag values: Y/N, TRUE/FALSE, 1/0 → bool
    Returns None if CSV cannot be parsed or yields no rows.
    """
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(io.BytesIO(raw), dtype=str, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        return None

    if df.empty:
        return None

    df = df.rename(columns=COLUMN_RENAMES)
    df = df[[c for c in OUTPUT_COLS if c in df.columns]]

    # Must have at minimum operatingDay and hourEnding to be useful
    if "operatingDay" not in df.columns or "hourEnding" not in df.columns:
        return None

    # Normalise operatingDay: MM/DD/YYYY → YYYY-MM-DD
    if "operatingDay" in df.columns:
        sample = df["operatingDay"].dropna().iloc[0] if not df["operatingDay"].dropna().empty else ""
        if sample and "/" in sample:
            df["operatingDay"] = (
                pd.to_datetime(df["operatingDay"], format="%m/%d/%Y", errors="coerce")
                .dt.strftime("%Y-%m-%d")
            )

    # Normalise DSTFlag: Y/N, TRUE/FALSE, 1/0 → bool
    if "DSTFlag" in df.columns:
        df["DSTFlag"] = (
            df["DSTFlag"].str.strip().str.upper()
            .map({"TRUE": True, "FALSE": False, "Y": True, "N": False, "1": True, "0": False})
            .astype("boolean")
        )

    # Numeric load columns
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df if not df.empty else None


def _month_boundaries(date_from: str, date_to: str) -> list[tuple[str, str]]:
    """Split a YYYY-MM-DD range into monthly (start, end) pairs."""
    import calendar
    start = datetime.strptime(date_from, "%Y-%m-%d").date()
    end = datetime.strptime(date_to, "%Y-%m-%d").date()
    intervals: list[tuple[str, str]] = []
    current = start.replace(day=1)
    while current <= end:
        last_day = calendar.monthrange(current.year, current.month)[1]
        month_end = min(current.replace(day=last_day), end)
        month_start = max(current, start)
        intervals.append((month_start.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d")))
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1, day=1)
        else:
            current = current.replace(month=current.month + 1, day=1)
    return intervals


class ERCOTLoadArchiveExtractor:
    """Backfill load data from the ERCOT archive API (NP6-346-CD)."""

    def __init__(self, client: ERCOTAPIClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Step 1: list docIds for a date range
    # ------------------------------------------------------------------

    def _list_docs_for_month(self, date_from: str, date_to: str, page_size: int = 1000) -> list[int]:
        """Return all docIds posted within [date_from, date_to] (YYYY-MM-DD).

        Archive list format:
          { "_meta": { totalPages, ... }, "archives": [ { "docId": ..., ... } ] }
        """
        ts_from, ts_to = _ymd_to_iso_range(date_from, date_to)
        doc_ids: list[int] = []
        page = 1
        while True:
            params = {
                "postDatetimeFrom": ts_from,
                "postDatetimeTo": ts_to,
                "page": page,
                "size": page_size,
            }
            resp: requests.Response | None = None
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    resp = self._client._session.get(
                        LIST_ENDPOINT,
                        headers=self._client._headers(),
                        params=params,
                        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                    )
                    if resp.status_code == 401 and attempt < MAX_RETRIES:
                        self._client._auth.force_refresh()
                        time.sleep(BACKOFF_BASE ** attempt)
                        continue
                    if resp.status_code == 429:
                        # Rate limit — use long fixed waits (30s / 60s / 90s)
                        wait = 30 * attempt
                        if attempt < MAX_RETRIES:
                            log.warning("HTTP 429 listing docs (attempt %d/%d) - retrying in %ds ...",
                                        attempt, MAX_RETRIES, wait)
                            time.sleep(wait)
                            continue
                        raise RuntimeError(
                            f"HTTP 429 listing docs for {date_from} -> {date_to} "
                            f"after {MAX_RETRIES} attempts."
                        )
                    if resp.status_code in (500, 502, 503, 504):
                        wait = BACKOFF_BASE ** attempt
                        if attempt < MAX_RETRIES:
                            log.warning("HTTP %s listing docs (attempt %d/%d) - retrying in %ds ...",
                                        resp.status_code, attempt, MAX_RETRIES, wait)
                            time.sleep(wait)
                            continue
                        raise RuntimeError(
                            f"HTTP {resp.status_code} listing docs for {date_from} -> {date_to} "
                            f"after {MAX_RETRIES} attempts."
                        )
                    resp.raise_for_status()
                    break
                except (requests.ConnectionError, requests.Timeout) as exc:
                    wait = BACKOFF_BASE ** attempt
                    log.warning("Network error listing docs (attempt %d/%d): %s - retrying in %ds ...",
                                attempt, MAX_RETRIES, exc, wait)
                    if attempt < MAX_RETRIES:
                        time.sleep(wait)
                    else:
                        raise

            assert resp is not None
            body = resp.json()
            meta = body.get("_meta", {})
            archives = body.get("archives", [])
            for arch in archives:
                raw_id = arch.get("docId")
                if raw_id is not None:
                    doc_ids.append(int(raw_id))

            total_pages = int(meta.get("totalPages", 1))
            log.debug("  list page %d/%d — %d docIds so far", page, total_pages, len(doc_ids))
            if page >= total_pages:
                break
            page += 1
            time.sleep(1)  # pace list requests to stay under rate limit
        return sorted(set(doc_ids))

    # ------------------------------------------------------------------
    # Step 2: download a batch of ZIPs
    # ------------------------------------------------------------------

    def _download_batch(self, doc_ids: list[int]) -> bytes:
        """POST docIds → receive ZIP binary. Retries on transient errors."""
        headers = {
            **self._client._headers(),
            "Content-Type": "application/json",
            "Accept": "application/zip",
        }
        payload = {"docIds": doc_ids}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self._client._session.post(
                    DOWNLOAD_ENDPOINT,
                    headers=headers,
                    json=payload,
                    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT * 4),
                )
                if resp.status_code == 401 and attempt < MAX_RETRIES:
                    self._client._auth.force_refresh()
                    time.sleep(BACKOFF_BASE ** attempt)
                    continue
                if resp.status_code == 429:
                    wait = 30 * attempt
                    log.warning("HTTP 429 on batch download (attempt %d/%d) - retrying in %ds ...",
                                attempt, MAX_RETRIES, wait)
                    time.sleep(wait)
                    continue
                if resp.status_code in (500, 502, 503, 504):
                    wait = BACKOFF_BASE ** attempt
                    log.warning("HTTP %s on batch download (attempt %d/%d) - retrying in %ds ...",
                                resp.status_code, attempt, MAX_RETRIES, wait)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.content
            except (requests.ConnectionError, requests.Timeout) as exc:
                wait = BACKOFF_BASE ** attempt
                log.warning("Network error on batch download (attempt %d/%d): %s - retrying in %ds ...",
                            attempt, MAX_RETRIES, exc, wait)
                if attempt < MAX_RETRIES:
                    time.sleep(wait)
                else:
                    raise

        raise RuntimeError(f"Failed batch download after {MAX_RETRIES} attempts.")

    # ------------------------------------------------------------------
    # Step 3: unzip + parse CSVs → normalised DataFrame
    # ------------------------------------------------------------------

    def _process_zip(self, zip_bytes: bytes) -> pd.DataFrame:
        """Unzip in-memory, parse every CSV, normalise columns.

        Outer ZIP → inner ZIPs (one per docId) → one CSV each.
        Falls back to treating an outer entry as a raw CSV for older vintages.
        """
        frames: list[pd.DataFrame] = []
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as outer_zf:
            for outer_name in outer_zf.namelist():
                inner_data = outer_zf.read(outer_name)
                try:
                    with zipfile.ZipFile(io.BytesIO(inner_data)) as inner_zf:
                        csv_names = [n for n in inner_zf.namelist() if n.lower().endswith(".csv")]
                        for csv_name in csv_names:
                            raw = inner_zf.read(csv_name)
                            df = _parse_load_csv(raw)
                            if df is not None:
                                frames.append(df)
                except zipfile.BadZipFile:
                    df = _parse_load_csv(inner_data)
                    if df is not None:
                        frames.append(df)

        if not frames:
            return pd.DataFrame(columns=OUTPUT_COLS)
        return pd.concat(frames, ignore_index=True)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def trial_fetch(self, date_from: str, date_to: str) -> pd.DataFrame:
        """Fetch a handful of rows to validate the archive API and CSV schema."""
        log.info("=== TRIAL FETCH ===")
        log.info("Listing docs for %s -> %s ...", date_from, date_to)

        trial_date = date_from
        doc_ids = self._list_docs_for_month(trial_date, trial_date)
        if not doc_ids:
            log.warning("No documents found for %s. Archive endpoint may not exist for NP6-346-CD.", trial_date)
            return pd.DataFrame(columns=OUTPUT_COLS)

        log.info("Found %d docIds for %s. Downloading first batch (up to 50) ...", len(doc_ids), trial_date)
        zip_bytes = self._download_batch(doc_ids[:50])
        df = self._process_zip(zip_bytes)

        if df.empty:
            log.warning("No rows extracted from trial batch. Check CSV column names.")
            return df

        df_trial = df.head(5)
        print("\n--- Trial result ---")
        print(f"Shape   : {df_trial.shape}")
        print(f"Columns : {list(df_trial.columns)}")
        print(df_trial.to_string(index=False))
        print()

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        csv_path = OUT_DIR / "load_archive_trial.csv"
        df_trial.to_csv(csv_path, index=False)
        log.info("Trial CSV saved -> %s", csv_path)
        return df_trial

    def full_fetch(self, date_from: str, date_to: str, batch_size: int = 1000) -> None:
        """Full historical backfill. Processes month-by-month, writes incrementally to parquet."""
        log.info("=== FULL FETCH (%s -> %s) ===", date_from, date_to)

        start_tag = date_from.replace("-", "")
        end_tag = date_to.replace("-", "")
        pq_path = OUT_DIR / f"load_archive_{start_tag}_{end_tag}.parquet"
        writer = ParquetChunkWriter(pq_path)

        months = _month_boundaries(date_from, date_to)
        log.info("Processing %d monthly chunks ...", len(months))

        try:
            for m_from, m_to in months:
                log.info("Month %s -> %s: listing docIds ...", m_from, m_to)
                doc_ids = self._list_docs_for_month(m_from, m_to)
                if not doc_ids:
                    log.warning("  No documents found for %s -> %s — skipping.", m_from, m_to)
                    continue

                log.info("  Found %d docIds. Downloading in batches of %d ...", len(doc_ids), batch_size)
                total_rows_month = 0

                for i in range(0, len(doc_ids), batch_size):
                    batch = doc_ids[i: i + batch_size]
                    batch_num = i // batch_size + 1
                    total_batches = (len(doc_ids) + batch_size - 1) // batch_size
                    log.info("  Batch %d/%d (%d docIds) ...", batch_num, total_batches, len(batch))

                    try:
                        zip_bytes = self._download_batch(batch)
                        df = self._process_zip(zip_bytes)
                        if not df.empty:
                            writer.write(df)
                            total_rows_month += len(df)
                    except Exception as exc:
                        log.error("  Batch %d failed: %s — continuing.", batch_num, exc)

                    time.sleep(0.25)

                log.info("  Month %s: %d rows written (total so far: %d).",
                         m_from[:7], total_rows_month, writer.rows_written)
                time.sleep(5)  # cooldown between months to avoid 429

        finally:
            writer.close()

        if writer.rows_written == 0:
            log.warning("No data written. Archive endpoint may not exist for NP6-346-CD, "
                        "or the date range has no documents.")
        else:
            log.info("Total rows written: %d", writer.rows_written)
            log.info("Full Parquet saved -> %s", pq_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill ERCOT load data from the archive API (NP6-346-CD). "
            "Use this for pre-2023-12 data not available via the live API."
        )
    )
    parser.add_argument("--auto", action="store_true",
                        help="Skip confirmation prompt and run full extract immediately.")
    parser.add_argument("--trial-only", action="store_true",
                        help="Run trial fetch only (no full extract).")
    parser.add_argument("--from", dest="date_from", default="2021-01-01",
                        help="Start date YYYY-MM-DD (default: 2021-01-01).")
    parser.add_argument("--to", dest="date_to", default="2023-11-30",
                        help="End date YYYY-MM-DD (default: 2023-11-30).")
    parser.add_argument("--batch-size", type=int, default=1000,
                        help="DocIds per download POST request (default: 1000, max: 1000).")
    args = parser.parse_args()
    try:
        _validate_ymd_range(args.date_from, args.date_to)
    except ValueError as exc:
        parser.error(str(exc))

    username = require_env("ERCOT_USERNAME", log)
    password = require_env("ERCOT_PASSWORD", log)
    subscription_key = require_env("ERCOT_SUBSCRIPTION_KEY", log)

    auth = ERCOTAuth(username, password, log)
    client = ERCOTAPIClient(auth, subscription_key, log)
    extractor = ERCOTLoadArchiveExtractor(client)

    extractor.trial_fetch(date_from=args.date_from, date_to=args.date_to)

    if args.trial_only:
        log.info("--trial-only flag set. Done.")
        return

    if not args.auto:
        answer = input(
            f"\nTrial successful. Proceed with full archive extraction "
            f"({args.date_from} -> {args.date_to})? [y/N]: "
        ).strip().lower()
        if answer not in ("y", "yes"):
            log.info("Full extraction cancelled by user.")
            return

    extractor.full_fetch(
        date_from=args.date_from,
        date_to=args.date_to,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
