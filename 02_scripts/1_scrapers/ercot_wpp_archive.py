"""
ERCOT Archive API — Wind Power Production Historical Backfill (NP4-742-CD)
==========================================================================
Endpoint : GET  https://api.ercot.com/api/public-reports/archive/NP4-742-CD
           POST https://api.ercot.com/api/public-reports/archive/NP4-742-CD/download
Auth     : Azure AD B2C ROPC flow → id_token (Bearer) + Ocp-Apim-Subscription-Key

The live API endpoint (/np4-742-cd/wpp_hrly_actual_fcast_geo) only returns recent data
(Dec 2023+). This script uses the archive API to backfill 2021-01-01 – 2023-11-30,
producing a parquet with an identical schema to the live extract.

Archive API response format:
  GET /archive/NP4-742-CD → { "_meta": { totalPages, ... }, "archives": [ { docId, ... } ] }

Two-step archive flow:
  1. GET /archive/NP4-742-CD  → paginated list of docIds (~24 per day — one per hourly snapshot)
  2. POST /archive/NP4-742-CD/download  → outer ZIP binary (batch up to 1000 docIds)
  3. Outer ZIP → inner ZIPs (one per docId) → one CSV each (~216 rows rolling window each)
  4. Read CSV → normalise columns → deduplicate → append to parquet

IMPORTANT — Snapshot / revision model
--------------------------------------
Like the live endpoint, each archive doc is a rolling-window snapshot covering ~9 days
of (DELIVERY_DATE, HOUR_ENDING) pairs. Multiple docs therefore overlap on the same pair.
After unpacking all docs, deduplicate: keep one row per (deliveryDate, hourEnding).
Since all revisions carry the same settled ACTUAL_* values, any revision is equivalent —
deduplication here only removes redundant rows, not conflicting ones.

Confirmed CSV schema (2021 vintage):
  DELIVERY_DATE   MM/DD/YYYY
  HOUR_ENDING     integer 1–24  (NOT HH:MM — normalize to "HH:00" to match live schema)
  ACTUAL_SYSTEM_WIDE, ACTUAL_PANHANDLE, ACTUAL_COASTAL, ACTUAL_SOUTH, ACTUAL_WEST, ACTUAL_NORTH
  COP_HSL_*, STWPF_*, WGRPP_*  ← forecast/limit columns — dropped
  DSTFlag         Y/N string → bool

Output schema (matches live wpp_geo parquet exactly):
  deliveryDate    VARCHAR   (YYYY-MM-DD)
  hourEnding      VARCHAR   (HH:00, e.g. "01:00", "24:00")
  genSystemWide   DOUBLE
  genPanhandle    DOUBLE
  genCoastal      DOUBLE
  genSouth        DOUBLE
  genWest         DOUBLE
  genNorth        DOUBLE
  DSTFlag         BOOLEAN

Usage
-----
    export ERCOT_USERNAME="you@example.com"
    export ERCOT_PASSWORD="yourpassword"
    export ERCOT_SUBSCRIPTION_KEY="your_subscription_key"

    python 02_scripts/1_scrapers/ercot_wpp_archive.py --trial-only
    python 02_scripts/1_scrapers/ercot_wpp_archive.py --auto
    python 02_scripts/1_scrapers/ercot_wpp_archive.py --from 2021-01-01 --to 2023-11-30 --auto

Outputs
-------
Trial (CSV)   : 01_data/1.2_raw_api/wpp_archive_trial.csv
Full (Parquet): 01_data/1.2_raw_api/wpp_archive_YYYYMMDD_YYYYMMDD.parquet
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

ARCHIVE_BASE      = "https://api.ercot.com/api/public-reports/archive/NP4-742-CD"
LIST_ENDPOINT     = ARCHIVE_BASE
DOWNLOAD_ENDPOINT = f"{ARCHIVE_BASE}/download"

# Output columns — must match live wpp_geo parquet exactly.
OUTPUT_COLS = [
    "deliveryDate", "hourEnding",
    "genSystemWide", "genPanhandle", "genCoastal",
    "genSouth", "genWest", "genNorth",
    "DSTFlag",
]

# Archive CSV uses UPPER_CASE ACTUAL_* names; map to live gen* names.
COLUMN_RENAMES = {
    "DELIVERY_DATE":       "deliveryDate",    # MM/DD/YYYY → normalized below
    "HOUR_ENDING":         "hourEnding",      # integer 1–24 → normalized to "HH:00" below
    "ACTUAL_SYSTEM_WIDE":  "genSystemWide",
    "ACTUAL_PANHANDLE":    "genPanhandle",
    "ACTUAL_COASTAL":      "genCoastal",
    "ACTUAL_SOUTH":        "genSouth",
    "ACTUAL_WEST":         "genWest",
    "ACTUAL_NORTH":        "genNorth",
    # DSTFlag keeps its name
}

NUMERIC_COLS = {"genSystemWide", "genPanhandle", "genCoastal", "genSouth", "genWest", "genNorth"}


def _validate_ymd_range(date_from: str, date_to: str) -> None:
    fmt = "%Y-%m-%d"
    try:
        d_from = datetime.strptime(date_from, fmt)
        d_to   = datetime.strptime(date_to,   fmt)
    except ValueError as exc:
        raise ValueError(f"Invalid date format (expected YYYY-MM-DD): {exc}") from exc
    if d_from > d_to:
        raise ValueError(f"--from ({date_from}) must not be after --to ({date_to}).")


def _ymd_to_iso_range(date_from: str, date_to: str) -> tuple[str, str]:
    return f"{date_from}T00:00:00", f"{date_to}T23:59:59"


def _parse_wpp_csv(raw: bytes) -> pd.DataFrame | None:
    """Parse raw CSV bytes from an archive ZIP, normalise to output schema."""
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

    # Must have at minimum deliveryDate and hourEnding.
    if "deliveryDate" not in df.columns or "hourEnding" not in df.columns:
        return None

    # Normalise deliveryDate: MM/DD/YYYY → YYYY-MM-DD
    sample = df["deliveryDate"].dropna().iloc[0] if not df["deliveryDate"].dropna().empty else ""
    if sample and "/" in sample:
        df["deliveryDate"] = (
            pd.to_datetime(df["deliveryDate"], format="%m/%d/%Y", errors="coerce")
            .dt.strftime("%Y-%m-%d")
        )

    # Normalise hourEnding: integer 1–24 → "HH:00" string (e.g. 1 → "01:00", 24 → "24:00")
    # Archive stores hour as plain integer; live API stores as "01:00", "02:00", etc.
    df["hourEnding"] = (
        pd.to_numeric(df["hourEnding"], errors="coerce")
        .astype("Int64")
        .apply(lambda h: f"{int(h):02d}:00" if pd.notna(h) else None)
    )

    # Normalise DSTFlag: Y/N → bool
    if "DSTFlag" in df.columns:
        df["DSTFlag"] = (
            df["DSTFlag"].str.strip().str.upper()
            .map({"TRUE": True, "FALSE": False, "Y": True, "N": False, "1": True, "0": False})
            .astype("boolean")
        )

    # Numeric generation columns
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Keep only output columns that exist in this CSV
    available = [c for c in OUTPUT_COLS if c in df.columns]
    df = df[available]

    return df if not df.empty else None


def _month_boundaries(date_from: str, date_to: str) -> list[tuple[str, str]]:
    """Split a YYYY-MM-DD range into monthly (start, end) pairs."""
    import calendar
    start = datetime.strptime(date_from, "%Y-%m-%d").date()
    end   = datetime.strptime(date_to,   "%Y-%m-%d").date()
    intervals: list[tuple[str, str]] = []
    current = start.replace(day=1)
    while current <= end:
        last_day  = calendar.monthrange(current.year, current.month)[1]
        month_end = min(current.replace(day=last_day), end)
        month_start = max(current, start)
        intervals.append((month_start.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d")))
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1, day=1)
        else:
            current = current.replace(month=current.month + 1, day=1)
    return intervals


class ERCOTWindArchiveExtractor:
    """Backfill wind production data from the ERCOT archive API (NP4-742-CD)."""

    def __init__(self, client: ERCOTAPIClient) -> None:
        self._client = client

    # ── Step 1: list docIds for a date range ──────────────────────────────

    def _list_docs_for_month(self, date_from: str, date_to: str, page_size: int = 1000) -> list[int]:
        """Return all docIds posted within [date_from, date_to] (YYYY-MM-DD).

        ~24 docs per day (one hourly snapshot each). For a 30-day month: ~720 docs.
        """
        ts_from, ts_to = _ymd_to_iso_range(date_from, date_to)
        doc_ids: list[int] = []
        page = 1
        while True:
            params = {
                "postDatetimeFrom": ts_from,
                "postDatetimeTo":   ts_to,
                "page":  page,
                "size":  page_size,
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
                        wait = 30 * attempt
                        if attempt < MAX_RETRIES:
                            log.warning("HTTP 429 listing docs (attempt %d/%d) — retrying in %ds …",
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
                            log.warning("HTTP %s listing docs (attempt %d/%d) — retrying in %ds …",
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
                    log.warning("Network error listing docs (attempt %d/%d): %s — retrying in %ds …",
                                attempt, MAX_RETRIES, exc, wait)
                    if attempt < MAX_RETRIES:
                        time.sleep(wait)
                    else:
                        raise

            assert resp is not None
            body     = resp.json()
            meta     = body.get("_meta", {})
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
            time.sleep(1)

        return sorted(set(doc_ids))

    # ── Step 2: download a batch of ZIPs ─────────────────────────────────

    def _download_batch(self, doc_ids: list[int]) -> bytes:
        """POST docIds → receive outer ZIP binary. Retries on transient errors."""
        headers = {
            **self._client._headers(),
            "Content-Type": "application/json",
            "Accept":       "application/zip",
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
                    log.warning("HTTP 429 on batch download (attempt %d/%d) — retrying in %ds …",
                                attempt, MAX_RETRIES, wait)
                    time.sleep(wait)
                    continue
                if resp.status_code in (500, 502, 503, 504):
                    wait = BACKOFF_BASE ** attempt
                    log.warning("HTTP %s on batch download (attempt %d/%d) — retrying in %ds …",
                                resp.status_code, attempt, MAX_RETRIES, wait)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.content
            except (requests.ConnectionError, requests.Timeout) as exc:
                wait = BACKOFF_BASE ** attempt
                log.warning("Network error on batch download (attempt %d/%d): %s — retrying in %ds …",
                            attempt, MAX_RETRIES, exc, wait)
                if attempt < MAX_RETRIES:
                    time.sleep(wait)
                else:
                    raise

        raise RuntimeError(f"Failed batch download after {MAX_RETRIES} attempts.")

    # ── Step 3: unzip + parse CSVs ────────────────────────────────────────

    def _process_zip(self, zip_bytes: bytes) -> pd.DataFrame:
        """Outer ZIP → inner ZIPs → CSVs. Parse and normalise each CSV."""
        frames: list[pd.DataFrame] = []
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as outer_zf:
            for outer_name in outer_zf.namelist():
                inner_data = outer_zf.read(outer_name)
                try:
                    with zipfile.ZipFile(io.BytesIO(inner_data)) as inner_zf:
                        csv_names = [n for n in inner_zf.namelist() if n.lower().endswith(".csv")]
                        for csv_name in csv_names:
                            raw = inner_zf.read(csv_name)
                            df  = _parse_wpp_csv(raw)
                            if df is not None:
                                frames.append(df)
                except zipfile.BadZipFile:
                    df = _parse_wpp_csv(inner_data)
                    if df is not None:
                        frames.append(df)

        if not frames:
            return pd.DataFrame(columns=OUTPUT_COLS)
        return pd.concat(frames, ignore_index=True)

    # ── Public interface ──────────────────────────────────────────────────

    def trial_fetch(self, date_from: str, date_to: str) -> pd.DataFrame:
        """List docs for the first month of the range, download a small batch, print schema."""
        log.info("=== TRIAL FETCH ===")

        # Use just the first month for the trial
        from datetime import datetime
        import calendar
        start = datetime.strptime(date_from, "%Y-%m-%d").date()
        last_day = calendar.monthrange(start.year, start.month)[1]
        trial_end = start.replace(day=last_day).strftime("%Y-%m-%d")

        log.info("Listing docs for %s -> %s …", date_from, trial_end)
        doc_ids = self._list_docs_for_month(date_from, trial_end)

        if not doc_ids:
            log.warning("No documents found for %s -> %s. Check credentials and date range.", date_from, trial_end)
            return pd.DataFrame(columns=OUTPUT_COLS)

        log.info("Found %d docIds for %s -> %s. Downloading first batch (up to 50) …",
                 len(doc_ids), date_from, trial_end)
        zip_bytes = self._download_batch(doc_ids[:50])
        df_raw    = self._process_zip(zip_bytes)

        if df_raw.empty:
            log.warning("No rows extracted from trial batch. Check CSV column names.")
            return df_raw

        # Dedup for trial display (multiple docs cover same delivery hour)
        df_dedup = df_raw.drop_duplicates(subset=["deliveryDate", "hourEnding"]).sort_values(
            ["deliveryDate", "hourEnding"]
        )

        print("\n--- Trial result ---")
        print(f"Raw rows (before dedup) : {len(df_raw)}")
        print(f"Unique (date, hour) pairs: {len(df_dedup)}")
        print(f"Columns : {list(df_dedup.columns)}")
        print(f"Date range: {df_dedup['deliveryDate'].min()} → {df_dedup['deliveryDate'].max()}")
        print(f"Null genSystemWide: {df_dedup['genSystemWide'].isna().sum()}")
        print(df_dedup.head(5).to_string(index=False))
        print()

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        csv_path = OUT_DIR / "wpp_archive_trial.csv"
        df_dedup.to_csv(csv_path, index=False)
        log.info("Trial CSV saved -> %s", csv_path)
        return df_dedup

    def full_fetch(self, date_from: str, date_to: str, batch_size: int = 1000) -> None:
        """Full historical backfill. Processes month-by-month, deduplicates, writes parquet."""
        log.info("=== FULL FETCH (%s -> %s) ===", date_from, date_to)

        start_tag = date_from.replace("-", "")
        end_tag   = date_to.replace("-", "")
        pq_path   = OUT_DIR / f"wpp_archive_{start_tag}_{end_tag}.parquet"
        writer    = ParquetChunkWriter(pq_path)

        months = _month_boundaries(date_from, date_to)
        log.info("Processing %d monthly chunks …", len(months))

        seen_keys: set[tuple[str, str]] = set()  # (deliveryDate, hourEnding) pairs already written

        try:
            for m_from, m_to in months:
                log.info("Month %s -> %s: listing docIds …", m_from, m_to)
                doc_ids = self._list_docs_for_month(m_from, m_to)
                if not doc_ids:
                    log.warning("  No documents found for %s -> %s — skipping.", m_from, m_to)
                    continue

                log.info("  Found %d docIds. Downloading in batches of %d …", len(doc_ids), batch_size)
                month_rows = 0

                for i in range(0, len(doc_ids), batch_size):
                    batch      = doc_ids[i: i + batch_size]
                    batch_num  = i // batch_size + 1
                    total_batches = (len(doc_ids) + batch_size - 1) // batch_size
                    log.info("  Batch %d/%d (%d docIds) …", batch_num, total_batches, len(batch))

                    try:
                        zip_bytes = self._download_batch(batch)
                        df        = self._process_zip(zip_bytes)
                        if not df.empty:
                            # Deduplicate against already-seen (deliveryDate, hourEnding) pairs.
                            # Archive docs overlap on the same hours; values are identical across
                            # revisions so any first-seen row is authoritative.
                            df = df.dropna(subset=["deliveryDate", "hourEnding"])
                            key_tuples = list(zip(df["deliveryDate"], df["hourEnding"]))
                            new_mask   = [k not in seen_keys for k in key_tuples]
                            df_new     = df[new_mask]
                            seen_keys.update(k for k, m in zip(key_tuples, new_mask) if m)
                            if not df_new.empty:
                                writer.write(df_new)
                                month_rows += len(df_new)
                    except Exception as exc:
                        log.error("  Batch %d failed: %s — continuing.", batch_num, exc)

                    time.sleep(0.25)

                log.info("  Month %s: %d new unique rows (total so far: %d).",
                         m_from[:7], month_rows, writer.rows_written)
                time.sleep(5)  # cooldown between months to avoid 429

        finally:
            writer.close()

        if writer.rows_written == 0:
            log.warning("No data written. Check credentials and date range.")
        else:
            log.info("Total rows written: %d", writer.rows_written)
            log.info("Full Parquet saved -> %s", pq_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill ERCOT wind production data from the archive API (NP4-742-CD). "
            "Use this for pre-2023-12 data not available via the live API."
        )
    )
    parser.add_argument("--auto",       action="store_true",
                        help="Skip confirmation prompt and run full extract immediately.")
    parser.add_argument("--trial-only", action="store_true",
                        help="Run trial fetch only (no full extract).")
    parser.add_argument("--from", dest="date_from", default="2021-01-01",
                        help="Start date YYYY-MM-DD (default: 2021-01-01).")
    parser.add_argument("--to",   dest="date_to",   default="2023-11-30",
                        help="End date YYYY-MM-DD (default: 2023-11-30).")
    parser.add_argument("--batch-size", type=int, default=1000,
                        help="DocIds per download POST request (default: 1000).")
    args = parser.parse_args()

    try:
        _validate_ymd_range(args.date_from, args.date_to)
    except ValueError as exc:
        parser.error(str(exc))

    username         = require_env("ERCOT_USERNAME",         log)
    password         = require_env("ERCOT_PASSWORD",         log)
    subscription_key = require_env("ERCOT_SUBSCRIPTION_KEY", log)

    auth      = ERCOTAuth(username, password, log)
    client    = ERCOTAPIClient(auth, subscription_key, log)
    extractor = ERCOTWindArchiveExtractor(client)

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
