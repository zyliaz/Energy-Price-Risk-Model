"""Parse ERCOT Mid-Term Load Forecast Metrics xlsx files — Hourly Error column.

Source:  01_data/1.1_raw_bulk/Load Forcast/Mid_Term_Load_Forecast_Metrics_*.xlsx
Output:  01_data/1.2_raw_api/mid_term_load_forecast_<min>_<max>.parquet

Each xlsx file covers one calendar month.  Each sheet is one of 8 ERCOT weather
zones (Coast, East, FarWest, NCent, North, SCent, South, West) plus a system-wide
ERCOT total.

We extract 'Actual' and 'Selected' (forecast) columns and widen the result to one row per
(datetime) with one column per zone.

Column layout (confirmed via inspection — consistent across all files/sheets):
  Index  0: HE            — timestamp "01FEB2022:01:00:00"
  Index  1: Actual        — actual load
  Index  2: Selected      — Forecast load

Timestamp parsing:
  Raw HE cell: "01FEB2022:01:00:00"
  `df["datetime"] = pd.to_datetime(df['HE'], format="%d%b%Y:%H:%M:%S")`

Error calculation:
    Forecast column - Actual column
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "01_data" / "1.1_raw_bulk" / "Load Forcast"
OUT_DIR = PROJECT_ROOT / "01_data" / "1.2_raw_api"

# Sheet → output column suffix (prefix = "forecast")
ZONE_SHEETS = ["Coast", "East", "FarWest", "NCent", "North", "SCent", "South", "West", "ERCOT"]

HE_PATTERN = re.compile(r"^\d{2}[A-Z]{3}\d{4}:\d{2}:\d{2}:\d{2}$")


def parse_sheet(xf: pd.ExcelFile, sheet: str) -> pd.DataFrame:
    """Extract (datetime, actual, selected) from one sheet."""
    
    # usecols=[0, 1, 2] → HE (timestamp), Actual and Selected (forecast)
    df = xf.parse(sheet, header=0, usecols=[0, 1, 2])
    df.columns = df.columns.str.strip()  # Strip whitespace from column names

    # Keep only data rows (header/footer rows have non-timestamp HE values)
    df = df.dropna(subset=["HE"]).copy()
    df["HE"] = df["HE"].astype(str)
    df = df[df["HE"].apply(lambda v: bool(HE_PATTERN.match(v)))].copy()

    if df.empty:
        return pd.DataFrame(columns=["datetime", "Actual", "Selected", "Error"])

    df["datetime"] = pd.to_datetime(df['HE'], format="%d%b%Y:%H:%M:%S")
    df['Error'] = df['Selected'] - df['Actual']

    return df[["datetime", "Actual", "Selected", "Error"]].reset_index(drop=True)


def parse_file(path: Path) -> pd.DataFrame | None:
    """Parse all sheets from one xlsx file, return wide DataFrame or None on failure."""
    log.info("Parsing %s", path.name)
    try:
        xf = pd.ExcelFile(path, engine="openpyxl")
    except Exception as exc:
        log.error("  Could not open %s: %s", path.name, exc)
        return None

    available = set(xf.sheet_names)
    missing   = [s for s in ZONE_SHEETS if s not in available]
    if missing:
        log.warning("  Missing sheets in %s: %s", path.name, missing)

    wide: pd.DataFrame | None = None
    for sheet in ZONE_SHEETS:
        if sheet not in available:
            continue
        df_sheet = parse_sheet(xf, sheet)
        if df_sheet.empty:
            log.warning("  Sheet '%s' produced 0 rows — skipping", sheet)
            continue
        fcst_name = f"forecast_{sheet}"
        actual_name = f"actual_{sheet}"
        error_name = f"error_{sheet}"
        df_sheet = df_sheet.rename(columns={"Actual": actual_name, "Selected": fcst_name, "Error": error_name})
        if wide is None:
            wide = df_sheet
        else:
            wide = wide.merge(df_sheet, on=["datetime"], how="outer")

    return wide


def main() -> None:
    xlsx_files = sorted(RAW_DIR.glob("Mid_Term_Load_Forecast_Metrics_*.xlsx"))
    if not xlsx_files:
        log.error("No xlsx files found in %s", RAW_DIR)
        log.error("Expected files like: Mid_Term_Load_Forecast_Metrics_February_2022.xlsx")
        sys.exit(1)

    log.info("Found %d xlsx file(s) in %s", len(xlsx_files), RAW_DIR)

    chunks: list[pd.DataFrame] = []
    for path in xlsx_files:
        df = parse_file(path)
        if df is not None and not df.empty:
            chunks.append(df)
        else:
            log.warning("  Skipping %s (empty or parse error)", path.name)

    if not chunks:
        log.error("No data parsed from any file — aborting.")
        sys.exit(1)

    combined = pd.concat(chunks, ignore_index=True)

    # Sort by datetime
    combined = (
        combined
        .sort_values(["datetime"])
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # Sanity checks
    min_dt = combined["datetime"].min()
    max_dt = combined["datetime"].max()

    # Write output
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    min_tag = min_dt.strftime("%Y%m%d")
    max_tag = max_dt.strftime("%Y%m%d")
    out_path = OUT_DIR / f"mid_term_load_forecast_{min_tag}_{max_tag}.parquet"

    pq.write_table(
        pa.Table.from_pandas(combined, preserve_index=False),
        out_path,
        compression="snappy",
    )
    log.info("Written → %s", out_path)


if __name__ == "__main__":
    main()
