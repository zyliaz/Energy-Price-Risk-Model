"""
ERCOT Archive API — Hourly Resource Outage Capacity, full range (NP3-233-CD)
============================================================================
Endpoint : GET  https://api.ercot.com/api/public-reports/archive/np3-233-cd
           POST https://api.ercot.com/api/public-reports/archive/NP3-233-CD/download
Auth     : Azure AD B2C ROPC flow → id_token (Bearer) + Ocp-Apim-Subscription-Key

The archive covers 2021-01-01 → present (verified 2026-09-24), so this one script
replaces the archive (2021–2023) + live (Dec 2023+) split. ALL hourly postings are
stored (no dedup); 1-hour-ahead selection happens downstream.

Archive CSV formats (verified 2026-09-24):
  early 2021 (168 rows): Date, HourEnding, TotalResourceMW, TotalIRRMW, TotalNewEquipResourceMW
  mid-2021+  (168/192) : Date, HourEnding, Total{Resource,IRR,NewEquipResource}MWZone{South,North,West,Houston}
Both carry `Date` as MM/DD/YYYY and `HourEnding` as zero-padded "01".."24".

Output schema (one row per posting × operating hour):
    postedDatetime                         string   (archive doc metadata; not in the CSV)
    operatingDate                          string   YYYY-MM-DD
    hourEnding                             int64    1–24
    total{Resource,IRR,NewEquipResource}MWZone{South,North,West,Houston}
                                           float64  (null in the system-wide era)
    totalResourceMW / totalIRRMW / totalNewEquipResourceMW
                                           float64  (given in system-wide era; zone sum otherwise)

Robustness: each month is written to its own part file (atomic tmp → rename) only when
every batch in that month succeeds. Re-running skips finished months, so a SLURM
timeout or a 429 streak costs at most one month. Parts are combined at the end.

Local copy of the job script in 04_jobs/outage_cap_archive_full_sep24/. Credentials are
read from the repo-root .env (ERCOT_USERNAME / ERCOT_PASSWORD / ERCOT_SUBSCRIPTION_KEY);
never hardcode them here. Output defaults to 01_data/1.2_raw_api/outage/.

Usage
-----
    python 02_scripts/1_scrapers/ercot_outage_cap_archive_full.py --from 2024-01-01 --to 2024-12-31
"""

from __future__ import annotations

import argparse
import calendar
import io
import logging
import sys
import time
import zipfile
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from dotenv import load_dotenv

from ercot_common import (
    BACKOFF_BASE,
    CONNECT_TIMEOUT,
    OUT_DIR,
    PROJECT_ROOT,
    READ_TIMEOUT,
    ERCOTAPIClient,
    ERCOTAuth,
    require_env,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

LIST_ENDPOINT = "https://api.ercot.com/api/public-reports/archive/np3-233-cd"
DOWNLOAD_ENDPOINT = "https://api.ercot.com/api/public-reports/archive/NP3-233-CD/download"

MAX_ATTEMPTS = 6
BATCH_ROUNDS = 3
ROUND_WAIT_SEC = 120

ZONES = ["South", "North", "West", "Houston"]
METRICS = ["Resource", "IRR", "NewEquipResource"]
ZONE_COLS = [f"total{m}MWZone{z}" for m in METRICS for z in ZONES]
TOTAL_COLS = [f"total{m}MW" for m in METRICS]

SCHEMA = pa.schema(
    [("postedDatetime", pa.string()), ("operatingDate", pa.string()), ("hourEnding", pa.int64())]
    + [(c, pa.float64()) for c in ZONE_COLS]
    + [(c, pa.float64()) for c in TOTAL_COLS]
)
OUTPUT_COLS = SCHEMA.names


def _month_boundaries(date_from: str, date_to: str) -> list[tuple[str, str]]:
    start = date.fromisoformat(date_from)
    end = date.fromisoformat(date_to)
    out: list[tuple[str, str]] = []
    cur = start.replace(day=1)
    while cur <= end:
        m_end = min(cur.replace(day=calendar.monthrange(cur.year, cur.month)[1]), end)
        out.append((max(cur, start).isoformat(), m_end.isoformat()))
        cur = date(cur.year + (cur.month == 12), cur.month % 12 + 1, 1)
    return out


def _lower_first(name: str) -> str:
    return name[0].lower() + name[1:]


def parse_outage_csv(raw: bytes, posted_datetime: str) -> pd.DataFrame | None:
    df = None
    for encoding in ("utf-8", "latin-1"):
        try:
            df = pd.read_csv(io.BytesIO(raw), dtype=str, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    if df is None or df.empty:
        return None

    df.columns = [_lower_first(c.strip()) for c in df.columns]
    if "date" not in df.columns or "hourEnding" not in df.columns:
        raise ValueError(f"Unexpected CSV columns: {list(df.columns)}")

    out = pd.DataFrame({
        "postedDatetime": posted_datetime,
        "operatingDate": pd.to_datetime(df["date"], format="%m/%d/%Y").dt.strftime("%Y-%m-%d"),
        "hourEnding": pd.to_numeric(df["hourEnding"]).astype("int64"),
    })
    for c in ZONE_COLS:
        out[c] = pd.to_numeric(df[c], errors="coerce") if c in df.columns else float("nan")

    system_wide = "totalResourceMW" in df.columns
    for m in METRICS:
        total = f"total{m}MW"
        if system_wide:
            out[total] = pd.to_numeric(df[total], errors="coerce") if total in df.columns else float("nan")
        else:
            out[total] = out[[f"total{m}MWZone{z}" for z in ZONES]].sum(axis=1, min_count=1)
    return out[OUTPUT_COLS]


class OutageCapArchiveFull:
    def __init__(self, client: ERCOTAPIClient, out_dir: Path, batch_size: int) -> None:
        self._client = client
        self._batch_size = batch_size
        self.parts_dir = out_dir / "outage_cap_archive_parts"
        self.out_dir = out_dir

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                resp = self._client._session.request(
                    method, url, headers={**self._client._headers(), **kwargs.pop("extra_headers", {})},
                    **kwargs,
                )
            except (requests.ConnectionError, requests.Timeout) as exc:
                wait = BACKOFF_BASE ** attempt
                log.warning("Network error (attempt %d/%d): %s — retry in %ds", attempt, MAX_ATTEMPTS, exc, wait)
                time.sleep(wait)
                continue
            if resp.status_code == 401:
                self._client._auth.force_refresh()
                time.sleep(BACKOFF_BASE ** attempt)
                continue
            if resp.status_code == 429:
                wait = 30 * attempt
                log.warning("HTTP 429 (attempt %d/%d) — retry in %ds", attempt, MAX_ATTEMPTS, wait)
                time.sleep(wait)
                continue
            if resp.status_code >= 500:
                wait = BACKOFF_BASE ** attempt
                log.warning("HTTP %s (attempt %d/%d) — retry in %ds", resp.status_code, attempt, MAX_ATTEMPTS, wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        raise RuntimeError(f"{method} {url} failed after {MAX_ATTEMPTS} attempts")

    def list_docs(self, m_from: str, m_to: str) -> dict[int, str]:
        docs: dict[int, str] = {}
        page = 1
        while True:
            resp = self._request(
                "GET", LIST_ENDPOINT,
                params={"postDatetimeFrom": f"{m_from}T00:00:00", "postDatetimeTo": f"{m_to}T23:59:59",
                        "page": page, "size": 1000},
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT * 3),
            )
            body = resp.json()
            for arch in body.get("archives", []):
                if arch.get("docId") is not None:
                    docs[int(arch["docId"])] = arch.get("postDatetime", "")
            if page >= int(body.get("_meta", {}).get("totalPages", 1)):
                return docs
            page += 1
            time.sleep(1)

    def download_batch(self, doc_ids: list[int], id_to_posted: dict[int, str]) -> pd.DataFrame:
        resp = self._request(
            "POST", DOWNLOAD_ENDPOINT,
            json={"docIds": doc_ids},
            extra_headers={"Content-Type": "application/json", "Accept": "application/zip"},
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT * 4),
        )
        frames: list[pd.DataFrame] = []
        seen: set[int] = set()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as outer:
            for name in outer.namelist():
                doc_id = int(name.split(".")[0])
                seen.add(doc_id)
                with zipfile.ZipFile(io.BytesIO(outer.read(name))) as inner:
                    for csv_name in inner.namelist():
                        if csv_name.lower().endswith(".csv"):
                            df = parse_outage_csv(inner.read(csv_name), id_to_posted[doc_id])
                            if df is not None:
                                frames.append(df)
        missing = set(doc_ids) - seen
        if missing:
            raise RuntimeError(f"{len(missing)} docIds missing from ZIP (e.g. {sorted(missing)[:3]})")
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=OUTPUT_COLS)

    def fetch_month(self, m_from: str, m_to: str) -> bool:
        part = self.parts_dir / f"{m_from.replace('-', '')}_{m_to.replace('-', '')}.parquet"
        if part.exists():
            log.info("Month %s → %s: part exists, skipping.", m_from, m_to)
            return True

        docs = self.list_docs(m_from, m_to)
        log.info("Month %s → %s: %d docs", m_from, m_to, len(docs))
        if not docs:
            log.error("  No docs listed — month NOT written.")
            return False

        doc_ids = sorted(docs)
        pending = [doc_ids[i : i + self._batch_size] for i in range(0, len(doc_ids), self._batch_size)]
        frames: list[pd.DataFrame] = []
        for rnd in range(1, BATCH_ROUNDS + 1):
            failed: list[list[int]] = []
            for i, batch in enumerate(pending, 1):
                try:
                    frames.append(self.download_batch(batch, docs))
                except Exception as exc:
                    log.warning("  Round %d batch %d/%d failed: %s", rnd, i, len(pending), exc)
                    failed.append(batch)
                time.sleep(1.5)
            if not failed:
                break
            pending = failed
            if rnd < BATCH_ROUNDS:
                log.warning("  %d batches failed; retrying in %ds ...", len(failed), ROUND_WAIT_SEC)
                time.sleep(ROUND_WAIT_SEC)
        else:
            log.error("  %d batches still failing — month NOT written (rerun to resume).", len(pending))
            return False

        df = pd.concat(frames, ignore_index=True)
        n_posted = df["postedDatetime"].nunique()
        if n_posted != len(docs):
            log.error("  %d postings parsed vs %d docs listed — month NOT written.", n_posted, len(docs))
            return False

        self.parts_dir.mkdir(parents=True, exist_ok=True)
        tmp = part.with_suffix(".tmp")
        pq.write_table(pa.Table.from_pandas(df[OUTPUT_COLS], schema=SCHEMA, preserve_index=False),
                       tmp, compression="snappy")
        tmp.rename(part)
        log.info("  Wrote %d rows → %s", len(df), part.name)
        return True

    def combine(self, months: list[tuple[str, str]], date_from: str, date_to: str) -> Path:
        out_path = self.out_dir / f"outage_cap_archive_{date_from.replace('-', '')}_{date_to.replace('-', '')}.parquet"
        tmp = out_path.with_suffix(".tmp")
        total = 0
        with pq.ParquetWriter(tmp, SCHEMA, compression="snappy") as writer:
            for m_from, m_to in months:
                part = self.parts_dir / f"{m_from.replace('-', '')}_{m_to.replace('-', '')}.parquet"
                table = pq.read_table(part, schema=SCHEMA)
                writer.write_table(table)
                total += table.num_rows
        tmp.rename(out_path)
        check = pq.read_metadata(out_path).num_rows
        if check != total:
            raise RuntimeError(f"Combined file has {check} rows, expected {total}")
        log.info("Combined %d months, %d rows → %s", len(months), total, out_path)
        return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Full-range NP3-233-CD archive extract.")
    parser.add_argument("--from", dest="date_from", default="2021-01-01")
    parser.add_argument("--to", dest="date_to", default=date.today().isoformat())
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR / "outage")
    args = parser.parse_args()
    load_dotenv(PROJECT_ROOT / ".env")
    if datetime.fromisoformat(args.date_from) > datetime.fromisoformat(args.date_to):
        parser.error("--from must not be after --to")

    auth = ERCOTAuth(require_env("ERCOT_USERNAME", log), require_env("ERCOT_PASSWORD", log), log)
    client = ERCOTAPIClient(auth, require_env("ERCOT_SUBSCRIPTION_KEY", log), log)
    extractor = OutageCapArchiveFull(client, args.out_dir, args.batch_size)

    months = _month_boundaries(args.date_from, args.date_to)
    log.info("=== NP3-233-CD archive %s → %s: %d months ===", args.date_from, args.date_to, len(months))
    failed = []
    for m in months:
        if not extractor.fetch_month(*m):
            failed.append(m)
        time.sleep(5)

    if failed:
        log.error("%d months incomplete: %s — rerun the same command to resume.", len(failed), failed)
        sys.exit(1)
    extractor.combine(months, args.date_from, args.date_to)


if __name__ == "__main__":
    main()
