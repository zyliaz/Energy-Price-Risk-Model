"""
Parse ERCOT RTM Price Adder HIST Excel files (2025 + 2026) into a single
15-min time-series parquet.

Sources (HIST schema only — 6 price columns):
  - rpt…20260101…HIST_RT15MPRICEADDER_2025.xlsx  (2025 data)
  - rpt…20260517…HIST_RT15MPRICEADDER_2026.xlsx  (2026 data through ~May)

Output: 01_data/1.2_raw_api/rtm_price_adders_15min_20250105_20260517.parquet
"""

import os
import glob
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR  = str(PROJECT_ROOT / "01_data/1.1_raw_bulk/ercot/RTM Price Adders 2021-2025")
OUT_PATH = str(PROJECT_ROOT / "01_data/1.2_raw_api/rtm_price_adders_15min_20250105_20260517.parquet")

HIST_PRICE_COLS = ["RTRDPA", "RTRDPRU", "RTRDPRD", "RTRDPRRS", "RTRDPECRS", "RTRDPNS"]

HEADER_ROW = 8  # rows 0-7 are title/blank

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
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
    df = df.dropna(how="all")
    return df


def parse_hist_files() -> pd.DataFrame:
    # Exclude Excel lock files (~$...)
    file_2025 = [f for f in glob.glob(os.path.join(RAW_DIR, "*20260101*HIST_RT15MPRICEADDER*.xlsx"))
                 if not os.path.basename(f).startswith("~$")]
    file_2026 = [f for f in glob.glob(os.path.join(RAW_DIR, "*20260517*HIST_RT15MPRICEADDER*.xlsx"))
                 if not os.path.basename(f).startswith("~$")]
    assert len(file_2025) == 1, f"Expected 1 file matching *20260101*HIST*, found {len(file_2025)}"
    assert len(file_2026) == 1, f"Expected 1 file matching *20260517*HIST*, found {len(file_2026)}"

    chunks = []
    for path in [file_2025[0], file_2026[0]]:
        xl = pd.ExcelFile(path)
        available = [s for s in xl.sheet_names if s in MONTH_NAMES]
        print(f"  {os.path.basename(path)}: sheets {available}", flush=True)
        for sheet in available:
            df = read_sheet(path, sheet)
            if df.empty:
                continue
            ts = build_timestamp(df)
            out = pd.DataFrame({
                "timestamp":       ts,
                "RepeatedHourFlag": df["RepeatedHourFlag"].values,
            })
            for col in HIST_PRICE_COLS:
                out[col] = df[col].values if col in df.columns else pd.NA
            chunks.append(out)

    return pd.concat(chunks, ignore_index=True)


def merge_and_dedup(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate: for any repeated timestamp keep first non-NaN value per column."""
    def first_valid(s):
        valid = s.dropna()
        return valid.iloc[0] if len(valid) > 0 else pd.NA

    df = df.set_index("timestamp")
    merged = df.groupby("timestamp").agg(
        {col: first_valid for col in ["RepeatedHourFlag"] + HIST_PRICE_COLS}
    )
    return merged.sort_index().reset_index()


def validate_timeseries(df: pd.DataFrame) -> None:
    ts = df["timestamp"]

    assert ts.is_monotonic_increasing, "Timestamps are not monotonically increasing after sort"

    n_dups = ts.duplicated().sum()
    assert n_dups == 0, f"Found {n_dups} duplicate timestamps after dedup"

    expected = pd.date_range(start=ts.min(), end=ts.max(), freq="15min")
    missing  = expected.difference(ts)
    pct      = 100 * len(missing) / len(expected)
    print(f"\nTime-series validation:")
    print(f"  Expected intervals : {len(expected):,}")
    print(f"  Actual rows        : {len(df):,}")
    print(f"  Missing intervals  : {len(missing):,}  ({pct:.2f}%)")

    n_dst = (df["RepeatedHourFlag"] == True).sum()  # noqa: E712
    print(f"  RepeatedHourFlag=T : {n_dst:,}  (DST fall-back rows, kept)")


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    print("Reading HIST files ...", flush=True)
    raw = parse_hist_files()
    print(f"  Raw rows before dedup: {len(raw):,}", flush=True)

    print("Merging and deduplicating ...", flush=True)
    df = merge_and_dedup(raw)

    validate_timeseries(df)

    print(f"\nRows:       {len(df):,}")
    print(f"Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")
    print("\nNull counts per price column:")
    for col in HIST_PRICE_COLS:
        n = df[col].isna().sum()
        print(f"  {col:12s}: {n:,} nulls ({100*n/len(df):.1f}%)")

    table = pa.Table.from_pandas(df)
    pq.write_table(table, OUT_PATH, compression="snappy")
    print(f"\nWritten → {OUT_PATH}")


if __name__ == "__main__":
    main()
