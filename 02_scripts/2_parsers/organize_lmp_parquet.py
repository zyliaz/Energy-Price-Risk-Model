"""
ERCOT Historical LMP — Excel → Parquet Consolidator
====================================================
Reads ERCOT Day-Ahead (DAM) and Real-Time (RTM) settlement point price data
from their original Excel formats and writes consolidated parquet files.

Source data layout
------------------
DAM (report 13060, hourly):
    01_data/1.1_raw_bulk/ercot/DAM_2021_2026Feb/
        Historical DAM Load Zone and Hub Prices_YYYY/
            rpt.00013060.*.YYYYMMDD.*.DAMLZHBSPP_YYYY.zip   ← weekly snapshots
    Strategy: for each year, use the LATEST zip (most complete snapshot).
    Each zip contains one xlsx with 12 monthly sheets.

RTM (report 13061, 15-minute intervals):
    01_data/1.1_raw_bulk/ercot/RTM_2021_2026Mar/
        rpt.00013061.*.RTMLZHBSPP_YYYY.xlsx   ← one file per year, 12 sheets each

Output parquet files
--------------------
DAM  → 01_data/1.2_raw_api/dam_lzhb_spp.parquet
RTM  → 01_data/1.2_raw_api/rtm_lzhb_spp.parquet

Usage
-----
    python 02_scripts/1_scrapers/organize_lmp_parquet.py        # both
    python 02_scripts/1_scrapers/organize_lmp_parquet.py --dam  # DAM only
    python 02_scripts/1_scrapers/organize_lmp_parquet.py --rtm  # RTM only
"""

from __future__ import annotations

import argparse
import io
import logging
import re
import zipfile
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_BULK = PROJECT_ROOT / "01_data" / "1.1_raw_bulk" / "ercot"
RAW_API = PROJECT_ROOT / "01_data" / "1.2_raw_api"
DAM_DIR = RAW_BULK / "DAM_2021_2026Feb"
RTM_DIR = RAW_BULK / "RTM_2021_2026Mar"

YEARS = [2021, 2022, 2023, 2024, 2025]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_all_sheets(xlsx_bytes_or_path) -> pd.DataFrame:
    """Read every sheet from an xlsx file/bytes and return a single DataFrame."""
    xf = pd.ExcelFile(xlsx_bytes_or_path, engine="openpyxl")
    chunks = []
    for sheet in xf.sheet_names:
        df = xf.parse(sheet)
        if df.empty:
            continue
        chunks.append(df)
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()


def _parse_date(series: pd.Series) -> pd.Series:
    """Parse MM/DD/YYYY strings to datetime.date."""
    return pd.to_datetime(series, format="%m/%d/%Y").dt.date


def _parse_hour_ending(series: pd.Series) -> pd.Series:
    """Parse 'HH:00' string (ERCOT uses 01:00–24:00) to integer 1–24."""
    return series.str.split(":").str[0].astype(int)


# ---------------------------------------------------------------------------
# DAM
# ---------------------------------------------------------------------------

def _latest_dam_zip(year: int) -> Path:
    """
    Return the path of the most recently published zip for `year` inside the
    yearly sub-folder.  File names embed the publication date (YYYYMMDD) so a
    simple sort gives us the latest.  We filter to zips whose name ends in
    DAMLZHBSPP_{year}.zip to avoid picking up cross-year files.
    """
    folder = DAM_DIR / f"Historical DAM Load Zone and Hub Prices_{year}"
    pattern = re.compile(rf"DAMLZHBSPP_{year}\.zip$")
    candidates = sorted(p for p in folder.iterdir() if pattern.search(p.name))
    if not candidates:
        raise FileNotFoundError(f"No DAM zips found for {year} in {folder}")
    latest = candidates[-1]
    log.info("DAM %d — using %s", year, latest.name)
    return latest


def process_dam() -> None:
    log.info("=== DAM processing ===")
    all_chunks: list[pd.DataFrame] = []

    for year in YEARS:
        zip_path = _latest_dam_zip(year)

        with zipfile.ZipFile(zip_path) as outer:
            # The outer zip may contain another zip or the xlsx directly.
            xlsx_names = [n for n in outer.namelist() if n.endswith(".xlsx")]
            inner_zip_names = [n for n in outer.namelist() if n.endswith(".zip")]

            if xlsx_names:
                xlsx_bytes = io.BytesIO(outer.read(xlsx_names[0]))
            elif inner_zip_names:
                # Nested zip: open inner zip and find xlsx inside.
                inner_bytes = io.BytesIO(outer.read(inner_zip_names[0]))
                with zipfile.ZipFile(inner_bytes) as inner:
                    xlsx_names_inner = [n for n in inner.namelist() if n.endswith(".xlsx")]
                    xlsx_bytes = io.BytesIO(inner.read(xlsx_names_inner[0]))
            else:
                raise RuntimeError(f"No xlsx found in {zip_path}")

        raw = _read_all_sheets(xlsx_bytes)
        log.info("  %d  raw rows: %d", year, len(raw))

        if raw.empty:
            log.warning("  %d  empty — skipping", year)
            continue

        df = pd.DataFrame({
            "delivery_date":       _parse_date(raw["Delivery Date"]),
            "hour_ending":         _parse_hour_ending(raw["Hour Ending"]),
            "repeated_hour_flag":  raw["Repeated Hour Flag"].str.upper().eq("Y"),
            "settlement_point":    raw["Settlement Point"].str.strip(),
            "price":               raw["Settlement Point Price"].astype(float),
        })
        all_chunks.append(df)

    combined = pd.concat(all_chunks, ignore_index=True)
    combined = combined.drop_duplicates(
        subset=["delivery_date", "hour_ending", "settlement_point"]
    ).sort_values(["delivery_date", "hour_ending", "settlement_point"]).reset_index(drop=True)

    out_path = RAW_API / "dam_lzhb_spp.parquet"
    combined.to_parquet(out_path, index=False, compression="snappy")
    log.info(
        "DAM parquet written → %s  (%d rows, %d settlement points, %s – %s)",
        out_path, len(combined), combined["settlement_point"].nunique(),
        combined["delivery_date"].min(), combined["delivery_date"].max(),
    )


# ---------------------------------------------------------------------------
# RTM
# ---------------------------------------------------------------------------

def process_rtm() -> None:
    log.info("=== RTM processing ===")
    all_chunks: list[pd.DataFrame] = []

    for year in YEARS:
        xlsx_files = sorted(RTM_DIR.glob(f"*RTMLZHBSPP_{year}.xlsx"))
        if not xlsx_files:
            log.warning("RTM %d — no xlsx found, skipping", year)
            continue
        xlsx_path = xlsx_files[-1]
        log.info("RTM %d — reading %s", year, xlsx_path.name)

        raw = _read_all_sheets(xlsx_path)
        raw = raw.dropna(subset=["Delivery Date", "Delivery Hour", "Settlement Point Name"])
        log.info("  %d  raw rows: %d", year, len(raw))

        if raw.empty:
            log.warning("  %d  empty — skipping", year)
            continue

        df = pd.DataFrame({
            "delivery_date":         _parse_date(raw["Delivery Date"]),
            "hour_ending":           raw["Delivery Hour"].astype(int),
            "delivery_interval":     raw["Delivery Interval"].astype(int),
            "repeated_hour_flag":    raw["Repeated Hour Flag"].str.upper().eq("Y"),
            "settlement_point":      raw["Settlement Point Name"].str.strip(),
            "settlement_point_type": raw["Settlement Point Type"].str.strip(),
            "price":                 raw["Settlement Point Price"].astype(float),
        })
        all_chunks.append(df)

    combined = pd.concat(all_chunks, ignore_index=True)
    combined = combined.drop_duplicates(
        subset=["delivery_date", "hour_ending", "delivery_interval", "settlement_point"]
    ).sort_values(
        ["delivery_date", "hour_ending", "delivery_interval", "settlement_point"]
    ).reset_index(drop=True)

    out_path = RAW_API / "rtm_lzhb_spp.parquet"
    combined.to_parquet(out_path, index=False, compression="snappy")
    log.info(
        "RTM parquet written → %s  (%d rows, %d settlement points, %s – %s)",
        out_path, len(combined), combined["settlement_point"].nunique(),
        combined["delivery_date"].min(), combined["delivery_date"].max(),
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consolidate ERCOT DAM and RTM Excel data into parquet."
    )
    parser.add_argument("--dam", action="store_true", help="Process DAM only.")
    parser.add_argument("--rtm", action="store_true", help="Process RTM only.")
    args = parser.parse_args()

    run_dam = args.dam or (not args.dam and not args.rtm)
    run_rtm = args.rtm or (not args.dam and not args.rtm)

    if run_dam:
        process_dam()
    if run_rtm:
        process_rtm()


if __name__ == "__main__":
    main()
