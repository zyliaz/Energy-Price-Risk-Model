"""
ERCOT Public API — Seven-Day Load Forecast (NP3-565-CD), day-ahead slice
========================================================================
Endpoint : GET https://api.ercot.com/api/public-reports/np3-565-cd/lf_by_model_weather_zone
Auth     : Azure AD B2C ROPC flow → id_token (Bearer) + Ocp-Apim-Subscription-Key

Purpose
-------
Pull, for each operating day D, the forecasts for D that were posted on D-1
BEFORE the DAM close (10:00 CT), keeping only the in-use model. The latest
qualifying posting per hour is the "day-ahead forecast" used to study
over-prediction vs DAM prices.

Raw rows are one per (postedDatetime x deliveryDate x hourEnding) with weather
zone columns + systemTotal + inUseFlag. We filter server-side on
deliveryDate/postedDatetime ranges; inUseFlag filtering is attempted
server-side and falls back to client-side (field names verified via --discover).

Usage
-----
    set -a && source .env && set +a
    python 02_scripts/1_scrapers/ercot_mtlf_day_ahead.py --discover    # print endpoint fields, no pull
    python 02_scripts/1_scrapers/ercot_mtlf_day_ahead.py --trial-only  # 1 day trial (CSV)
    python 02_scripts/1_scrapers/ercot_mtlf_day_ahead.py --auto        # full extract

Outputs
-------
Trial (CSV)   : 01_data/1.2_raw_api/mtlf_day_ahead_trial.csv
Full (Parquet): 01_data/1.2_raw_api/mtlf_day_ahead_YYYYMMDD_YYYYMMDD.parquet
                (all qualifying postings kept, with postedDatetime — select
                 latest-per-hour downstream)
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import date, datetime, timedelta

import pandas as pd
import requests

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

PRODUCT_URL = "https://api.ercot.com/api/public-reports/np3-565-cd"
ENDPOINT = f"{PRODUCT_URL}/lf_by_model_weather_zone"
DAM_CLOSE = "10:00:00"  # CT — postings at/after this are not day-ahead-market relevant
SLEEP = 1.0  # per data-extraction-guide: on 429s raise the sleep (0.5-1s), not the timeout


def discover(client: ERCOTAPIClient) -> None:
    """EMIL self-describing check: product artifacts + endpoint field list."""
    for url in (PRODUCT_URL, ENDPOINT):
        rows, meta = [], {}
        try:
            resp = requests.get(url, headers=client._headers(), timeout=(10, 60))
            body = resp.json()
            print(f"\n=== {url} (HTTP {resp.status_code}) ===")
            if "fields" in body:
                for f in body["fields"]:
                    print(f"  {f.get('name'):24s} {f.get('dataType', ''):12s} "
                          f"hasRange={f.get('hasRange')} searchable={f.get('searchable')}")
                print(f"  _meta: {body.get('_meta')}")
            else:
                print(json.dumps(body, indent=1)[:2000])
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR: {exc}")


class MTLFDayAheadExtractor:
    def __init__(self, client: ERCOTAPIClient) -> None:
        self._client = client
        self._in_use_param_ok: bool | None = None

    def _fetch_day(self, day: str, page_size: int = 1000) -> pd.DataFrame:
        """All postings for operating day `day` posted on day-1 before DAM close."""
        d = datetime.strptime(day, "%Y-%m-%d").date()
        prev = d - timedelta(days=1)
        params = {
            "deliveryDateFrom": day,
            "deliveryDateTo": day,
            "postedDatetimeFrom": f"{prev}T00:00:00",
            "postedDatetimeTo": f"{prev}T{DAM_CLOSE}",
        }
        # try server-side in-use filter once; fall back silently
        if self._in_use_param_ok is not False:
            try:
                rows, meta = self._client.fetch_page(
                    ENDPOINT, params={**params, "inUseFlag": "true"}, page=1, size=page_size
                )
                if rows:
                    self._in_use_param_ok = True
                    return self._paginate_rest(params | {"inUseFlag": "true"}, rows, meta, page_size)
                self._in_use_param_ok = False
            except Exception:  # noqa: BLE001
                self._in_use_param_ok = False
        rows, meta = self._client.fetch_page(ENDPOINT, params=params, page=1, size=page_size)
        return self._paginate_rest(params, rows, meta, page_size)

    def _paginate_rest(self, params, rows, meta, page_size) -> pd.DataFrame:
        frames = [pd.DataFrame(rows)]
        total_pages = int(meta.get("totalPages", 1))
        for page in range(2, total_pages + 1):
            rows, _ = self._client.fetch_page(ENDPOINT, params=params, page=page, size=page_size)
            frames.append(pd.DataFrame(rows))
            time.sleep(SLEEP)
        df = pd.concat(frames, ignore_index=True)
        # client-side in-use filter if a flag column exists and wasn't applied server-side
        flag_cols = [c for c in df.columns if c.lower() in ("inuseflag", "inuse")]
        if flag_cols and self._in_use_param_ok is not True:
            col = flag_cols[0]
            df = df[df[col].astype(str).str.upper().isin(("TRUE", "Y", "1"))]
        return df

    def trial(self, day: str) -> None:
        log.info("=== TRIAL: operating day %s ===", day)
        df = self._fetch_day(day)
        print(f"Shape: {df.shape}")
        print(df.head(30).to_string(index=False))
        if not df.empty and "postedDatetime" in df.columns:
            print("\nDistinct postings:", sorted(df["postedDatetime"].unique()))
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / "mtlf_day_ahead_trial.csv"
        df.to_csv(path, index=False)
        log.info("Trial CSV saved -> %s", path)

    def full(self, date_from: str, date_to: str) -> None:
        start = datetime.strptime(date_from, "%Y-%m-%d").date()
        end = datetime.strptime(date_to, "%Y-%m-%d").date()
        tag = f"{date_from.replace('-', '')}_{date_to.replace('-', '')}"
        path = OUT_DIR / f"mtlf_day_ahead_{tag}.parquet"
        if path.exists():
            log.error("%s exists — pick a new range (e.g. resume with --from <last date + 1>) "
                      "and concatenate downstream; refusing to overwrite.", path)
            return
        writer = ParquetChunkWriter(path)
        empty_days = []
        try:
            d = start
            failed_days = []
            while d <= end:
                day = d.strftime("%Y-%m-%d")
                df = None
                for attempt in range(1, 4):  # outer per-day retry on top of ercot_common's
                    try:
                        df = self._fetch_day(day)
                        break
                    except Exception as exc:  # noqa: BLE001
                        log.warning("%s failed (outer attempt %d/3): %s — cooling down 60s", day, attempt, exc)
                        time.sleep(60)
                if df is None:
                    failed_days.append(day)
                    log.error("%s skipped after 3 outer attempts.", day)
                elif df.empty:
                    empty_days.append(day)
                else:
                    writer.write(df)
                if d.day == 1 or d == start:
                    log.info("%s: %s rows (running total %d)", day, "-" if df is None else len(df), writer.rows_written)
                d += timedelta(days=1)
                time.sleep(SLEEP)
            if failed_days:
                log.error("FAILED DAYS (re-pull these): %s", ",".join(failed_days))
        finally:
            writer.close()
        log.info("Done. %d rows -> %s", writer.rows_written, path)
        if empty_days:
            log.warning("%d empty days, first/last: %s / %s", len(empty_days), empty_days[0], empty_days[-1])


def main() -> None:
    parser = argparse.ArgumentParser(description="NP3-565-CD day-ahead in-use forecast extractor.")
    parser.add_argument("--discover", action="store_true", help="Print endpoint field metadata and exit.")
    parser.add_argument("--trial-only", action="store_true")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--trial-day", default="2025-08-20")
    parser.add_argument("--from", dest="date_from", default="2022-02-01")
    parser.add_argument("--to", dest="date_to", default="2025-11-30")
    args = parser.parse_args()

    auth = ERCOTAuth(require_env("ERCOT_USERNAME", log), require_env("ERCOT_PASSWORD", log), log)
    client = ERCOTAPIClient(auth, require_env("ERCOT_SUBSCRIPTION_KEY", log), log)
    ex = MTLFDayAheadExtractor(client)

    if args.discover:
        discover(client)
        return
    ex.trial(args.trial_day)
    if args.trial_only:
        return
    if not args.auto:
        if input(f"\nProceed with full extraction {args.date_from} -> {args.date_to}? [y/N] ").lower() != "y":
            return
    ex.full(args.date_from, args.date_to)


if __name__ == "__main__":
    main()
