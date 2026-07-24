"""
ERCOT Archive API — Seven-Day Load Forecast by Weather Zone (NP3-561-CD)
========================================================================
List     : GET  https://api.ercot.com/api/public-reports/archive/NP3-561-CD
Download : POST https://api.ercot.com/api/public-reports/archive/NP3-561-CD/download
Auth     : Azure AD B2C ROPC flow -> id_token (Bearer) + Ocp-Apim-Subscription-Key

This extractor is the production form of the validated check notebook
03_notebooks/00_check/04_ercot_7d_load_fcast_by_wzn_endpoint_check.ipynb — the
list_docs / download_batch / process_zip / parse_csv / fetch_all helpers below are
the same ones the notebook proved on a one-day sample.

Why the archive (not the live endpoint)
---------------------------------------
The live endpoint (/np3-561-cd/7d_load_fcast_by_wzn) only retains a short rolling
window and returns 0 records for 2023. Historical months (e.g. Aug 2023) live in the
archive API, indexed by *posting time* (postDatetime), not delivery date.

Two archive quirks the check notebook uncovered
  1. POST /download is CASE-SENSITIVE — needs the UPPERCASE EMIL (NP3-561-CD);
     lowercase POST -> HTTP 405.
  2. POST /download caps at ~50 docIds — n>=100 -> HTTP 405. Downloads chunk at BATCH.

Data shape
----------
Each archive document is one hourly forecast posting: a full 8-day snapshot
(current day + 7 forward = 192 rows). The same (deliveryDate, hourEnding) appears
across ~192 successive postings. This extractor KEEPS EVERY POSTING, tagging each row
with its posting timestamp. `postedDatetime` is NOT in the CSV — it is injected from
the archive doc metadata (docId -> postDatetime) via the outer-ZIP entry's leading docId.

Output schema (5 cols)
  deliveryDate    VARCHAR  (YYYY-MM-DD; archive MM/DD/YYYY normalised)
  hourEnding      VARCHAR  (H:00 .. 24:00; '24:00' preserved)
  systemTotal     DOUBLE
  DSTFlag         BOOLEAN  (archive N/Y normalised)
  postedDatetime  DATETIME (injected from doc metadata)

Coverage
--------
To capture ALL delivery dates in [--from, --to], postings are listed from
(--from - LOOKBACK_DAYS) through --to (an 8-day forecast posted in late July already
covers early-August deliveries); rows are then filtered to deliveryDate in [--from, --to].

Usage
-----
    set -a && source .env && set +a
    python 02_scripts/1_scrapers/ercot_7d_load_fcast_wzn_archive.py --trial-only
    python 02_scripts/1_scrapers/ercot_7d_load_fcast_wzn_archive.py --from 2023-08-01 --to 2023-08-31 --auto

Outputs
-------
Trial (CSV)   : 01_data/1.2_raw_api/load_fcast_wzn_archive_trial.csv
Full (Parquet): 01_data/1.2_raw_api/load_fcast_wzn_archive_YYYYMMDD_YYYYMMDD.parquet
"""

from __future__ import annotations

import argparse
import io
import logging
import time
import zipfile
from datetime import datetime, timedelta

import pandas as pd

from ercot_common import ERCOTAuth, ERCOTAPIClient, OUT_DIR, require_env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# UPPERCASE EMIL — POST /download is case-sensitive (lowercase -> 405).
ARCHIVE = "https://api.ercot.com/api/public-reports/archive/NP3-561-CD"
DOWNLOAD = f"{ARCHIVE}/download"

LOOKBACK_DAYS = 8   # 8-day forecast posted before --from still covers --from deliveries
BATCH = 50          # POST /download caps at ~50 docIds (n>=100 -> HTTP 405)

COLUMN_RENAMES = {
    "DeliveryDate": "deliveryDate", "HourEnding": "hourEnding",
    "SystemTotal": "systemTotal", "DSTFlag": "DSTFlag",
}
OUTPUT_COLS = ["deliveryDate", "hourEnding", "systemTotal", "DSTFlag", "postedDatetime"]


# ----------------------------------------------------------------------
# Helpers (mirror 04_ercot_7d_load_fcast_by_wzn_endpoint_check.ipynb)
# ----------------------------------------------------------------------
def parse_csv(raw: bytes, posted) -> pd.DataFrame:
    """Parse one archive CSV -> 5-col frame, tag postedDatetime."""
    df = pd.read_csv(io.BytesIO(raw), dtype=str)
    df = df.rename(columns=COLUMN_RENAMES)[["deliveryDate", "hourEnding", "systemTotal", "DSTFlag"]].copy()
    df["deliveryDate"] = pd.to_datetime(df["deliveryDate"], format="%m/%d/%Y", errors="coerce").dt.strftime("%Y-%m-%d")
    df["systemTotal"] = pd.to_numeric(df["systemTotal"], errors="coerce")
    df["DSTFlag"] = df["DSTFlag"].str.strip().str.upper().map({"Y": True, "N": False}).astype("boolean")
    df["postedDatetime"] = posted
    return df


def list_docs(client: ERCOTAPIClient, ts_from: str, ts_to: str, page_size: int = 1000) -> dict[int, pd.Timestamp]:
    """Return {docId: postDatetime} across all pages of a postDatetime window."""
    docs: dict[int, pd.Timestamp] = {}
    page = 1
    while True:
        params = {"postDatetimeFrom": ts_from, "postDatetimeTo": ts_to, "page": page, "size": page_size}
        r = client._session.get(ARCHIVE, headers=client._headers(), params=params, timeout=(10, 60))
        if r.status_code == 429:
            log.warning("HTTP 429 listing docs (page %d) — waiting 30s ...", page)
            time.sleep(30)
            continue
        r.raise_for_status()
        b = r.json()
        for a in b.get("archives", []):
            docs[int(a["docId"])] = pd.to_datetime(a["postDatetime"])
        total_pages = int(b.get("_meta", {}).get("totalPages", 1))
        log.info("  list page %d/%d — %d docIds so far", page, total_pages, len(docs))
        if page >= total_pages:
            break
        page += 1
        time.sleep(1)
    return docs


def download_batch(client: ERCOTAPIClient, doc_ids: list[int]) -> bytes:
    """POST <=BATCH docIds -> ZIP bytes, with 429/token-refresh retries."""
    headers = {**client._headers(), "Content-Type": "application/json", "Accept": "application/zip"}
    for attempt in range(1, 6):
        r = client._session.post(DOWNLOAD, headers=headers, json={"docIds": doc_ids}, timeout=(10, 240))
        if r.status_code == 401:
            client._auth.force_refresh()
            headers = {**client._headers(), "Content-Type": "application/json", "Accept": "application/zip"}
            continue
        if r.status_code == 429:
            wait = 30 * attempt
            log.warning("HTTP 429 on batch download (attempt %d) — waiting %ds ...", attempt, wait)
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.content
    raise RuntimeError("Failed batch download after retries.")


def process_zip(zip_bytes: bytes, doc_map: dict[int, pd.Timestamp]) -> pd.DataFrame:
    """Outer ZIP -> inner ZIP -> CSV; tag postedDatetime via the entry's leading docId."""
    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as outer:
        for name in outer.namelist():
            try:
                docid = int(name.split(".", 1)[0])   # outer entry begins with docId
            except ValueError:
                docid = None
            posted = doc_map.get(docid)
            with zipfile.ZipFile(io.BytesIO(outer.read(name))) as inner:
                for cn in [n for n in inner.namelist() if n.lower().endswith(".csv")]:
                    frames.append(parse_csv(inner.read(cn), posted))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=OUTPUT_COLS)


def fetch_all(client: ERCOTAPIClient, doc_map: dict[int, pd.Timestamp]) -> pd.DataFrame:
    """Download every docId in chunks of BATCH, tag postedDatetime, concat."""
    ids, frames = sorted(doc_map), []
    n_batches = (len(ids) + BATCH - 1) // BATCH
    for bi, i in enumerate(range(0, len(ids), BATCH), start=1):
        frames.append(process_zip(download_batch(client, ids[i:i + BATCH]), doc_map))
        if bi == 1 or bi % 5 == 0 or bi == n_batches:
            log.info("  downloaded batch %d/%d", bi, n_batches)
        time.sleep(0.25)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=OUTPUT_COLS)


# ----------------------------------------------------------------------
# Extraction flow
# ----------------------------------------------------------------------
def _list_window(date_from: str, date_to: str) -> tuple[str, str]:
    start = datetime.strptime(date_from, "%Y-%m-%d") - timedelta(days=LOOKBACK_DAYS)
    return f"{start.strftime('%Y-%m-%d')}T00:00:00", f"{date_to}T23:59:59"


def _validate_ymd_range(date_from: str, date_to: str) -> None:
    fmt = "%Y-%m-%d"
    d_from = datetime.strptime(date_from, fmt)
    d_to = datetime.strptime(date_to, fmt)
    if d_from > d_to:
        raise ValueError(f"--from ({date_from}) must not be after --to ({date_to}).")


def trial(client: ERCOTAPIClient, date_from: str, date_to: str) -> None:
    log.info("=== TRIAL ===")
    ts_from, _ = _list_window(date_from, date_to)
    trial_to = (datetime.strptime(ts_from[:10], "%Y-%m-%d") + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S")
    doc_map = list_docs(client, ts_from, trial_to)
    if not doc_map:
        log.warning("No documents found for trial window %s -> %s.", ts_from, trial_to)
        return
    ids = dict(sorted(doc_map.items())[:2])
    df = fetch_all(client, ids)
    print("\n--- Trial result (first 8 rows) ---")
    print(f"Shape   : {df.shape}")
    print(f"Columns : {list(df.columns)}")
    print(f"Dtypes  :\n{df.dtypes}")
    print(df.head(8).to_string(index=False))
    print(f"\npostedDatetime values: {sorted(df['postedDatetime'].unique())}")
    print(f"deliveryDate range   : {df['deliveryDate'].min()} -> {df['deliveryDate'].max()}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "load_fcast_wzn_archive_trial.csv"
    df.to_csv(csv_path, index=False)
    log.info("Trial CSV saved -> %s", csv_path)


def full(client: ERCOTAPIClient, date_from: str, date_to: str) -> None:
    log.info("=== FULL FETCH (delivery %s -> %s) ===", date_from, date_to)
    start_tag, end_tag = date_from.replace("-", ""), date_to.replace("-", "")
    pq_path = OUT_DIR / f"load_fcast_wzn_archive_{start_tag}_{end_tag}.parquet"
    if pq_path.exists():
        log.error("%s exists — refusing to overwrite. Rename it or pick a new range.", pq_path)
        return

    ts_from, ts_to = _list_window(date_from, date_to)
    log.info("Listing postings in postDatetime window %s -> %s ...", ts_from, ts_to)
    doc_map = list_docs(client, ts_from, ts_to)
    if not doc_map:
        log.warning("No documents found — nothing to write.")
        return

    raw = fetch_all(client, doc_map)
    # Filter to requested delivery-date window (postings span 8 days), keep every posting.
    out = raw[(raw["deliveryDate"] >= date_from) & (raw["deliveryDate"] <= date_to)]
    out = out.drop_duplicates(subset=["deliveryDate", "hourEnding", "postedDatetime"])  # guard dup docs
    out = out[OUTPUT_COLS].sort_values(["deliveryDate", "hourEnding", "postedDatetime"]).reset_index(drop=True)
    if out.empty:
        log.warning("No delivery-window rows for %s -> %s.", date_from, date_to)
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_parquet(pq_path, index=False, compression="snappy")
    log.info("Wrote %d rows -> %s", len(out), pq_path)
    log.info("deliveryDate range     : %s -> %s", out["deliveryDate"].min(), out["deliveryDate"].max())
    log.info("distinct postings      : %d", out["postedDatetime"].nunique())
    log.info("distinct delivery-hours: %d", out.groupby(["deliveryDate", "hourEnding"]).ngroups)
    log.info("systemTotal nulls      : %d", int(out["systemTotal"].isna().sum()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill NP3-561-CD 7-day load forecast by weather zone (archive).")
    parser.add_argument("--auto", action="store_true", help="Skip confirmation; run full extract.")
    parser.add_argument("--trial-only", action="store_true", help="Run trial fetch only.")
    parser.add_argument("--from", dest="date_from", default="2023-08-01", help="Delivery start YYYY-MM-DD.")
    parser.add_argument("--to", dest="date_to", default="2023-08-31", help="Delivery end YYYY-MM-DD.")
    args = parser.parse_args()
    try:
        _validate_ymd_range(args.date_from, args.date_to)
    except ValueError as exc:
        parser.error(str(exc))

    auth = ERCOTAuth(require_env("ERCOT_USERNAME", log), require_env("ERCOT_PASSWORD", log), log)
    client = ERCOTAPIClient(auth, require_env("ERCOT_SUBSCRIPTION_KEY", log), log)

    trial(client, args.date_from, args.date_to)
    if args.trial_only:
        log.info("--trial-only set. Done.")
        return
    if not args.auto:
        if input(f"\nProceed with full extraction (delivery {args.date_from} -> {args.date_to})? [y/N] ").strip().lower() not in ("y", "yes"):
            log.info("Cancelled.")
            return
    full(client, args.date_from, args.date_to)


if __name__ == "__main__":
    main()
