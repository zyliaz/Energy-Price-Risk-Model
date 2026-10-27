"""
ERCOT Archive API — Hourly Resource Outage Capacity Backfill (NP3-233-CD)
=========================================================================
Endpoint : GET  https://api.ercot.com/api/public-reports/archive/np3-233-cd
           POST https://api.ercot.com/api/public-reports/archive/np3-233-cd/download
Auth     : Azure AD B2C ROPC flow → id_token (Bearer) + Ocp-Apim-Subscription-Key

The live API only returns data from Dec 2023 onward. This script uses the archive API
to backfill 2021-01-01 – 2023-12-09, storing ALL hourly postings (no dedup).

Archive CSV format changed between 2021 and 2022:
  2021 (168-row):  Date, HourEnding, TotalResourceMW (system-wide), TotalIRRMW, TotalNewEquipResourceMW
  2022+ (192-row): per-zone columns matching the live API schema

Both formats are normalised to a common output schema. The postDatetime from the
archive listing metadata is injected into every row so downstream can select
1-hour-ahead entries.

Output schema:
    postedDatetime              VARCHAR   (ISO timestamp from archive doc metadata)
    operatingDate               VARCHAR   (YYYY-MM-DD)
    hourEnding                  INTEGER   (1–24)
    totalResourceMW             DOUBLE    (system-wide total; from col for 2021, summed from zones for 2022+)

Usage
-----
    python 02_scripts/1_scrapers/ercot_outage_cap_archive.py --trial-only
    python 02_scripts/1_scrapers/ercot_outage_cap_archive.py --auto
    python 02_scripts/1_scrapers/ercot_outage_cap_archive.py --from 2021-01-01 --to 2023-12-09 --auto

Outputs
-------
Trial (CSV)   : 01_data/1.2_raw_api/outage_cap_archive_trial.csv
Full (Parquet): 01_data/1.2_raw_api/outage_cap_archive_YYYYMMDD_YYYYMMDD.parquet
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

ARCHIVE_BASE = "https://api.ercot.com/api/public-reports/archive/np3-233-cd"
LIST_ENDPOINT = ARCHIVE_BASE
DOWNLOAD_ENDPOINT = f"{ARCHIVE_BASE}/download"

OUTPUT_COLS = [
    "postedDatetime",
    "operatingDate",
    "hourEnding",
    "totalResourceMW",
]

# 2022+ archive CSVs have per-zone columns; we sum them to system-wide total.
_ZONE_COLS_2022 = [
    "totalResourceMWZoneSouth",
    "totalResourceMWZoneNorth",
    "totalResourceMWZoneWest",
    "totalResourceMWZoneHouston",
]

# 2021 archive CSV column renames
COLUMN_RENAMES_2021 = {
    "Date": "operatingDate",
    "HourEnding": "hourEnding",
    "TotalResourceMW": "totalResourceMW",
}

# 2022+ archive CSV column renames (handle case variations)
COLUMN_RENAMES_2022 = {
    "OperatingDate": "operatingDate",
    "Operating Date": "operatingDate",
    "HourEnding": "hourEnding",
    "Hour Ending": "hourEnding",
    "TotalResourceMWZoneSouth": "totalResourceMWZoneSouth",
    "Total Resource MW Zone South": "totalResourceMWZoneSouth",
    "TotalResourceMWZoneNorth": "totalResourceMWZoneNorth",
    "Total Resource MW Zone North": "totalResourceMWZoneNorth",
    "TotalResourceMWZoneWest": "totalResourceMWZoneWest",
    "Total Resource MW Zone West": "totalResourceMWZoneWest",
    "TotalResourceMWZoneHouston": "totalResourceMWZoneHouston",
    "Total Resource MW Zone Houston": "totalResourceMWZoneHouston",
}


def _validate_ymd_range(date_from: str, date_to: str) -> None:
    fmt = "%Y-%m-%d"
    d_from = datetime.strptime(date_from, fmt)
    d_to = datetime.strptime(date_to, fmt)
    if d_from > d_to:
        raise ValueError(f"--from ({date_from}) must not be after --to ({date_to}).")


def _ymd_to_iso_range(date_from: str, date_to: str) -> tuple[str, str]:
    return f"{date_from}T00:00:00", f"{date_to}T23:59:59"


def _month_boundaries(date_from: str, date_to: str) -> list[tuple[str, str]]:
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


def _parse_outage_csv(raw: bytes, posted_datetime: str) -> pd.DataFrame | None:
    """Parse archive CSV, detect format (2021 vs 2022+), normalise to common schema."""
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

    # Detect format by checking for system-wide TotalResourceMW column
    is_2021_format = "TotalResourceMW" in df.columns

    if is_2021_format:
        df = df.rename(columns=COLUMN_RENAMES_2021)
        if "operatingDate" in df.columns:
            sample = df["operatingDate"].dropna().iloc[0] if not df["operatingDate"].dropna().empty else ""
            if sample and "/" in sample:
                df["operatingDate"] = (
                    pd.to_datetime(df["operatingDate"], format="%m/%d/%Y", errors="coerce")
                    .dt.strftime("%Y-%m-%d")
                )
        df["totalResourceMW"] = pd.to_numeric(df["totalResourceMW"], errors="coerce")
    else:
        df = df.rename(columns=COLUMN_RENAMES_2022)
        available_zones = [c for c in _ZONE_COLS_2022 if c in df.columns]
        for col in available_zones:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        if available_zones:
            df["totalResourceMW"] = df[available_zones].sum(axis=1)
        else:
            df["totalResourceMW"] = pd.NA

    df["hourEnding"] = pd.to_numeric(df.get("hourEnding", pd.Series(dtype="float")), errors="coerce")
    df["postedDatetime"] = posted_datetime

    available = [c for c in OUTPUT_COLS if c in df.columns]
    return df[available] if not df[available].empty else None


class ERCOTOutageCapArchiveExtractor:
    """Backfill outage capacity data from the ERCOT archive API (NP3-233-CD)."""

    def __init__(self, client: ERCOTAPIClient) -> None:
        self._client = client

    def _list_docs_for_month(
        self, date_from: str, date_to: str, page_size: int = 1000
    ) -> list[dict]:
        """Return [{docId, postDatetime}, ...] for docs posted in [date_from, date_to]."""
        ts_from, ts_to = _ymd_to_iso_range(date_from, date_to)
        docs: list[dict] = []
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
                        wait = 30 * attempt
                        if attempt < MAX_RETRIES:
                            log.warning(
                                "HTTP 429 listing docs (attempt %d/%d) - retrying in %ds ...",
                                attempt, MAX_RETRIES, wait,
                            )
                            time.sleep(wait)
                            continue
                        raise RuntimeError(
                            f"HTTP 429 listing docs for {date_from} -> {date_to} "
                            f"after {MAX_RETRIES} attempts."
                        )
                    if resp.status_code in (500, 502, 503, 504):
                        wait = BACKOFF_BASE ** attempt
                        if attempt < MAX_RETRIES:
                            log.warning(
                                "HTTP %s listing docs (attempt %d/%d) - retrying in %ds ...",
                                resp.status_code, attempt, MAX_RETRIES, wait,
                            )
                            time.sleep(wait)
                            continue
                        raise RuntimeError(
                            f"HTTP {resp.status_code} listing docs after {MAX_RETRIES} attempts."
                        )
                    resp.raise_for_status()
                    break
                except (requests.ConnectionError, requests.Timeout) as exc:
                    wait = BACKOFF_BASE ** attempt
                    log.warning(
                        "Network error listing docs (attempt %d/%d): %s - retrying in %ds ...",
                        attempt, MAX_RETRIES, exc, wait,
                    )
                    if attempt < MAX_RETRIES:
                        time.sleep(wait)
                    else:
                        raise

            assert resp is not None
            body = resp.json()
            meta = body.get("_meta", {})
            for arch in body.get("archives", []):
                raw_id = arch.get("docId")
                if raw_id is not None:
                    docs.append({
                        "docId": int(raw_id),
                        "postDatetime": arch.get("postDatetime", ""),
                    })

            total_pages = int(meta.get("totalPages", 1))
            if page >= total_pages:
                break
            page += 1
            time.sleep(1)
        return docs

    def _download_batch(self, doc_ids: list[int]) -> bytes:
        """POST docIds → receive ZIP binary."""
        headers = {
            **self._client._headers(),
            "Content-Type": "application/json",
            "Accept": "application/zip",
        }
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self._client._session.post(
                    DOWNLOAD_ENDPOINT,
                    headers=headers,
                    json={"docIds": doc_ids},
                    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT * 4),
                )
                if resp.status_code == 401 and attempt < MAX_RETRIES:
                    self._client._auth.force_refresh()
                    time.sleep(BACKOFF_BASE ** attempt)
                    continue
                if resp.status_code == 429:
                    wait = 30 * attempt
                    log.warning(
                        "HTTP 429 on batch download (attempt %d/%d) - retrying in %ds ...",
                        attempt, MAX_RETRIES, wait,
                    )
                    time.sleep(wait)
                    continue
                if resp.status_code in (500, 502, 503, 504):
                    wait = BACKOFF_BASE ** attempt
                    log.warning(
                        "HTTP %s on batch download (attempt %d/%d) - retrying in %ds ...",
                        resp.status_code, attempt, MAX_RETRIES, wait,
                    )
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.content
            except (requests.ConnectionError, requests.Timeout) as exc:
                wait = BACKOFF_BASE ** attempt
                log.warning(
                    "Network error on batch download (attempt %d/%d): %s - retrying in %ds ...",
                    attempt, MAX_RETRIES, exc, wait,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(wait)
                else:
                    raise
        raise RuntimeError(f"Failed batch download after {MAX_RETRIES} attempts.")

    def _process_zip(
        self, zip_bytes: bytes, id_to_posted: dict[int, str]
    ) -> pd.DataFrame:
        """Unpack outer ZIP → inner ZIPs → CSVs, inject postDatetime per doc."""
        frames: list[pd.DataFrame] = []
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as outer_zf:
            for outer_name in outer_zf.namelist():
                # Extract docId from filename (first numeric segment)
                doc_id = None
                first_part = outer_name.split(".")[0]
                if first_part.isdigit():
                    doc_id = int(first_part)
                posted_dt = id_to_posted.get(doc_id, "") if doc_id else ""

                inner_data = outer_zf.read(outer_name)
                try:
                    with zipfile.ZipFile(io.BytesIO(inner_data)) as inner_zf:
                        for csv_name in inner_zf.namelist():
                            if csv_name.lower().endswith(".csv"):
                                raw = inner_zf.read(csv_name)
                                df = _parse_outage_csv(raw, posted_dt)
                                if df is not None:
                                    frames.append(df)
                except zipfile.BadZipFile:
                    if outer_name.lower().endswith(".csv"):
                        df = _parse_outage_csv(inner_data, posted_dt)
                        if df is not None:
                            frames.append(df)

        if not frames:
            return pd.DataFrame(columns=OUTPUT_COLS)
        return pd.concat(frames, ignore_index=True)

    def trial_fetch(self, date_from: str, date_to: str) -> pd.DataFrame:
        log.info("=== TRIAL FETCH ===")
        log.info("Listing docs for %s ...", date_from)

        docs = self._list_docs_for_month(date_from, date_from)
        if not docs:
            log.warning("No documents found for %s.", date_from)
            return pd.DataFrame(columns=OUTPUT_COLS)

        log.info("Found %d docs for %s. Downloading first 5 ...", len(docs), date_from)
        trial_docs = docs[:5]
        id_to_posted = {d["docId"]: d["postDatetime"] for d in trial_docs}
        zip_bytes = self._download_batch([d["docId"] for d in trial_docs])
        df = self._process_zip(zip_bytes, id_to_posted)

        if df.empty:
            log.warning("No rows extracted from trial batch.")
            return df

        print("\n--- Trial result ---")
        print(f"Shape   : {df.shape}")
        print(f"Columns : {list(df.columns)}")
        print(df.head(10).to_string(index=False))
        print()

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        csv_path = OUT_DIR / "outage_cap_archive_trial.csv"
        df.head(20).to_csv(csv_path, index=False)
        log.info("Trial CSV saved -> %s", csv_path)
        return df

    def full_fetch(self, date_from: str, date_to: str, batch_size: int = 100) -> None:
        log.info("=== FULL FETCH (%s -> %s) ===", date_from, date_to)

        start_tag = date_from.replace("-", "")
        end_tag = date_to.replace("-", "")
        pq_path = OUT_DIR / f"outage_cap_archive_{start_tag}_{end_tag}.parquet"
        writer = ParquetChunkWriter(pq_path)

        months = _month_boundaries(date_from, date_to)
        log.info("Processing %d monthly chunks ...", len(months))

        try:
            for m_from, m_to in months:
                log.info("Month %s -> %s: listing docs ...", m_from, m_to)
                docs = self._list_docs_for_month(m_from, m_to)
                if not docs:
                    log.warning("  No documents for %s -> %s — skipping.", m_from, m_to)
                    continue

                id_to_posted = {d["docId"]: d["postDatetime"] for d in docs}
                doc_ids = [d["docId"] for d in docs]
                log.info(
                    "  Found %d docs. Downloading in batches of %d ...",
                    len(doc_ids), batch_size,
                )
                total_rows_month = 0

                for i in range(0, len(doc_ids), batch_size):
                    batch = doc_ids[i : i + batch_size]
                    batch_num = i // batch_size + 1
                    total_batches = (len(doc_ids) + batch_size - 1) // batch_size
                    log.info(
                        "  Batch %d/%d (%d docs) ...",
                        batch_num, total_batches, len(batch),
                    )

                    try:
                        zip_bytes = self._download_batch(batch)
                        df = self._process_zip(zip_bytes, id_to_posted)
                        if not df.empty:
                            writer.write(df)
                            total_rows_month += len(df)
                    except Exception as exc:
                        log.error("  Batch %d failed: %s — continuing.", batch_num, exc)

                    time.sleep(1.5)

                log.info(
                    "  Month %s: %d rows (total so far: %d).",
                    m_from[:7], total_rows_month, writer.rows_written,
                )
                time.sleep(5)
        finally:
            writer.close()

        if writer.rows_written == 0:
            log.warning("No data written.")
        else:
            log.info("Total rows written: %d", writer.rows_written)
            log.info("Full Parquet saved -> %s", pq_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill ERCOT outage capacity from the archive API (NP3-233-CD). "
            "Use for pre-Dec-2023 data not available via the live API."
        )
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
        "--from", dest="date_from", default="2021-01-01",
        help="Start date YYYY-MM-DD (default: 2021-01-01).",
    )
    parser.add_argument(
        "--to", dest="date_to", default="2023-12-09",
        help="End date YYYY-MM-DD (default: 2023-12-09).",
    )
    parser.add_argument(
        "--batch-size", type=int, default=100,
        help="DocIds per download request (default: 100).",
    )
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
    extractor = ERCOTOutageCapArchiveExtractor(client)

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
