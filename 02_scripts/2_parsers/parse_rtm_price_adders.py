"""
Parse ERCOT RTM Price Adder Excel files into a single 15-min time-series parquet.

Sources:
  - 6 annual files (2020-2025): schema has RTRSVPOR, RTRSVPOFF, RTRDP
  - 1 continuation file (HIST Dec 2025): schema has RTRDPA, RTRDPRU, RTRDPRD, RTRDPRRS, RTRDPECRS, RTRDPNS

Overlapping timestamps (Dec 2025 appears in both sources) are merged into a
single row with all 9 price columns populated from their respective sources.

Output: 01_data/1.2_raw_api/rtm_price_adders_15min_20200101_20251231.parquet
"""

import os
import glob
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = str(PROJECT_ROOT / "01_data/1.1_raw_bulk/RTM Price Adders 2021-2025")
OUT_PATH = str(PROJECT_ROOT / "01_data/1.2_raw_api/rtm_price_adders_15min_20200101_20251231.parquet")

ANNUAL_PRICE_COLS = ["RTRSVPOR", "RTRSVPOFF", "RTRDP"]
HIST_PRICE_COLS = ["RTRDPA", "RTRDPRU", "RTRDPRD", "RTRDPRRS", "RTRDPECRS", "RTRDPNS"]
ALL_PRICE_COLS = ANNUAL_PRICE_COLS + HIST_PRICE_COLS

HEADER_ROW = 8  # 0-indexed; rows 0-7 are title/blank

ANNUAL_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def build_timestamp(df: pd.DataFrame) -> pd.Series:
    """Construct a datetime from DeliveryDate + DeliveryHour + DeliveryInterval."""
    date = pd.to_datetime(df["DeliveryDate"])
    return (
        date
        + pd.to_timedelta(df["DeliveryHour"].astype(int) - 1, unit="h")
        + pd.to_timedelta((df["DeliveryInterval"].astype(int) - 1) * 15, unit="min")
    )


def read_sheet(path: str, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet, header=HEADER_ROW)
    df.columns = df.columns.str.strip()
    # Drop completely empty rows (some sheets have trailing blanks)
    df = df.dropna(how="all")
    return df


def parse_annual_files() -> pd.DataFrame:
    pattern = os.path.join(RAW_DIR, "*RTM_ORDC_REL_DPLY_PRC_15MINT_*.xlsx")
    files = sorted(glob.glob(pattern))
    print(f"Found {len(files)} annual files")

    chunks = []
    for path in files:
        fname = os.path.basename(path)
        print(f"  Reading {fname} ...", flush=True)
        for sheet in ANNUAL_MONTHS:
            df = read_sheet(path, sheet)
            if df.empty:
                continue
            ts = build_timestamp(df)
            out = pd.DataFrame({"timestamp": ts})
            out["RepeatedHourFlag"] = df["RepeatedHourFlag"].values
            for col in ANNUAL_PRICE_COLS:
                out[col] = df[col].values if col in df.columns else pd.NA
            for col in HIST_PRICE_COLS:
                out[col] = pd.NA
            chunks.append(out)

    return pd.concat(chunks, ignore_index=True)


def parse_hist_file() -> pd.DataFrame:
    pattern = os.path.join(RAW_DIR, "*HIST_RT15MPRICEADDER_*.xlsx")
    files = glob.glob(pattern)
    assert len(files) == 1, f"Expected 1 HIST file, found {len(files)}"
    path = files[0]
    print(f"  Reading {os.path.basename(path)} (Dec sheet) ...", flush=True)

    df = read_sheet(path, "Dec")
    ts = build_timestamp(df)
    out = pd.DataFrame({"timestamp": ts})
    out["RepeatedHourFlag"] = df["RepeatedHourFlag"].values
    for col in ANNUAL_PRICE_COLS:
        out[col] = pd.NA
    for col in HIST_PRICE_COLS:
        out[col] = df[col].values if col in df.columns else pd.NA
    return out


def merge_and_dedup(annual: pd.DataFrame, hist: pd.DataFrame) -> pd.DataFrame:
    """
    Combine annual + HIST frames. For any duplicate timestamp, fill all 9 price
    columns from whichever source has a non-null value.
    """
    combined = pd.concat([annual, hist], ignore_index=True)

    # For each price column, groupby timestamp and take first non-NaN value
    def first_valid(s):
        valid = s.dropna()
        return valid.iloc[0] if len(valid) > 0 else pd.NA

    # Use a more efficient approach: sort so annual rows come first (they cover
    # Jan-Nov), then HIST rows (Dec). For the overlap window, annual has the
    # 3 old cols and HIST has the 6 new cols, so we need to merge per column.
    combined = combined.set_index("timestamp")
    merged = combined.groupby("timestamp").agg(
        {col: first_valid for col in ["RepeatedHourFlag"] + ALL_PRICE_COLS}
    )
    merged = merged.sort_index().reset_index()
    return merged


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    annual = parse_annual_files()
    hist = parse_hist_file()

    print("Merging and deduplicating ...", flush=True)
    df = merge_and_dedup(annual, hist)

    # Sanity checks
    n_dups = df["timestamp"].duplicated().sum()
    assert n_dups == 0, f"Found {n_dups} duplicate timestamps after merge"

    print(f"\nRows:       {len(df):,}")
    print(f"Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")
    print(f"Duplicates: {n_dups}")
    print("\nNull counts per price column:")
    for col in ALL_PRICE_COLS:
        null_n = df[col].isna().sum()
        print(f"  {col:12s}: {null_n:,} nulls ({100*null_n/len(df):.1f}%)")

    table = pa.Table.from_pandas(df)
    pq.write_table(table, OUT_PATH, compression="snappy")
    print(f"\nWritten → {OUT_PATH}")


if __name__ == "__main__":
    main()
