"""
ERCOT RTM LMP Dec 2025 + 2026 — Excel → Parquet
=================================================
Produces a continuation parquet covering Dec 5 2025 through May 16 2026,
mirroring the date range of the RTM price adder continuation file.

Sources:
    01_data/1.1_raw_bulk/RTM_2021_2026Mar/
        rpt.00013061.….RTMLZHBSPP_2025.xlsx  ← Dec sheet only
        rpt.00013061.….RTMLZHBSPP_2026.xlsx  ← Jan–May sheets

Columns kept (user-selected):
    delivery_date, delivery_hour, repeated_hour_flag,
    settlement_point, price

Output:
    01_data/1.2_raw_api/rtm_lzhb_spp_20251205_20260516.parquet

Reuses helpers from organize_lmp_parquet.py — do not duplicate logic there.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).parent))
from organize_lmp_parquet import (  # noqa: E402
    RTM_DIR,
    RAW_API,
    _parse_date,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

OUT_PATH = RAW_API / "rtm_lzhb_spp_20251205_20260516.parquet"
START_DATE = pd.Timestamp("2025-12-05").date()

KEEP_COLS = ["Delivery Date", "Delivery Hour", "Repeated Hour Flag",
             "Settlement Point Name", "Settlement Point Price"]


def _read_sheets(path: Path, sheets: list[str]) -> pd.DataFrame:
    xf = pd.ExcelFile(path, engine="openpyxl")
    available = [s for s in sheets if s in xf.sheet_names]
    log.info("  %s: sheets %s", path.name, available)
    chunks = []
    for sheet in available:
        df = xf.parse(sheet, usecols=KEEP_COLS)
        df = df.dropna(subset=["Delivery Date", "Delivery Hour", "Settlement Point Name"])
        if not df.empty:
            chunks.append(df)
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()


def _normalise(raw: pd.DataFrame) -> pd.DataFrame:
    date = pd.to_datetime(raw["Delivery Date"], format="%m/%d/%Y")
    hour = raw["Delivery Hour"].astype(int)
    timestamp = date + pd.to_timedelta(hour - 1, unit="h")
    return pd.DataFrame({
        "timestamp":          timestamp,
        "delivery_date":      _parse_date(raw["Delivery Date"]),
        "delivery_hour":      hour,
        "repeated_hour_flag": raw["Repeated Hour Flag"].str.upper().eq("Y"),
        "settlement_point":   raw["Settlement Point Name"].str.strip(),
        "price":              raw["Settlement Point Price"].astype(float),
    })


def _pick(pattern: str) -> Path:
    files = [f for f in sorted(RTM_DIR.glob(pattern))
             if not f.name.startswith("~$")]
    assert files, f"No file matching {pattern} in {RTM_DIR}"
    return files[-1]


def process() -> None:
    # Dec 2025 from the 2025 annual file
    path_2025 = _pick("*RTMLZHBSPP_2025.xlsx")
    raw_2025 = _read_sheets(path_2025, ["Dec"])
    raw_2025 = raw_2025[pd.to_datetime(raw_2025["Delivery Date"], format="%m/%d/%Y").dt.date >= START_DATE]
    log.info("2025 Dec raw rows (from %s): %d", START_DATE, len(raw_2025))

    # Jan–May 2026 from the 2026 file
    path_2026 = _pick("*RTMLZHBSPP_2026.xlsx")
    raw_2026 = _read_sheets(path_2026, ["Jan", "Feb", "Mar", "Apr", "May"])
    log.info("2026 raw rows: %d", len(raw_2026))

    raw = pd.concat([raw_2025, raw_2026], ignore_index=True)
    df = _normalise(raw)

    before = len(df)
    df = df.drop_duplicates(
        subset=["delivery_date", "delivery_hour", "settlement_point"]
    ).sort_values(
        ["delivery_date", "delivery_hour", "settlement_point"]
    ).reset_index(drop=True)
    dropped = before - len(df)
    if dropped:
        log.info("Dropped %d duplicate rows", dropped)

    _validate(df)

    RAW_API.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df)
    pq.write_table(table, OUT_PATH, compression="snappy")
    log.info(
        "Written → %s  (%d rows, %d settlement points, %s – %s)",
        OUT_PATH, len(df), df["settlement_point"].nunique(),
        df["delivery_date"].min(), df["delivery_date"].max(),
    )


def _validate(df: pd.DataFrame) -> None:
    dt = (
        pd.to_datetime(df["delivery_date"].astype(str))
        + pd.to_timedelta(df["delivery_hour"] - 1, unit="h")
    )
    df = df.copy()
    df["_ts"] = dt

    ts_min, ts_max = dt.min(), dt.max()
    full_grid = pd.date_range(ts_min, ts_max, freq="h")

    gap_rows = []
    for sp in df["settlement_point"].unique():
        ts = df.loc[df["settlement_point"] == sp, "_ts"].sort_values()
        missing = full_grid.difference(ts)
        gap_rows.append({
            "settlement_point": sp,
            "expected":         len(full_grid),
            "actual":           len(ts),
            "missing":          len(missing),
            "missing_pct":      round(100 * len(missing) / len(full_grid), 2),
        })

    gap_df = pd.DataFrame(gap_rows).sort_values("missing", ascending=False)
    n_clean = (gap_df["missing"] == 0).sum()
    log.info(
        "Gap check: %d settlement points | %d clean | %d total missing intervals | "
        "date range %s – %s",
        len(gap_rows), n_clean, gap_df["missing"].sum(), ts_min, ts_max,
    )
    with_gaps = gap_df[gap_df["missing"] > 0]
    if not with_gaps.empty:
        log.info("Settlement points with gaps:")
        for _, row in with_gaps.iterrows():
            log.info("  %-30s  %d missing  (%.2f%%)",
                     row["settlement_point"], row["missing"], row["missing_pct"])

    n_dst = df["repeated_hour_flag"].sum()
    log.info("repeated_hour_flag=True rows: %d (DST fall-back, kept)", n_dst)


if __name__ == "__main__":
    process()
