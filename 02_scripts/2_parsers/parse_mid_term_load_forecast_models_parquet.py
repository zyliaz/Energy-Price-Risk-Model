"""Parse ERCOT Mid-Term Load Forecast Metrics xlsx files — all forecast models.

Variant of `parse_mid_term_load_forecast_parquet.py` for **load-prediction feature
engineering**: instead of just Actual/Selected/Error, this pulls every alternate
ERCOT forecast-model column so they can be used as predictors (or an ensemble)
rather than only the Hourly Error diagnostic.

Source:  01_data/1.1_raw_bulk/Load Forcast/Mid_Term_Load_Forecast_Metrics_*.xlsx
Output:  01_data/1.2_raw_api/mid_term_load_forecast_models_<min>_<max>.parquet

Each xlsx file covers one calendar month.  Each sheet is one of 8 ERCOT weather
zones (Coast, East, FarWest, NCent, North, SCent, South, West) plus a system-wide
ERCOT total.

Column layout (confirmed via inspection — consistent across all 46 files/sheets,
first 10 columns only; everything past column 9 is a monthly error-stat block
we intentionally don't touch):
  Index 0: HE        — timestamp "01FEB2022:01:00:00"
  Index 1: Actual     — actual load
  Index 2: Selected   — ERCOT's chosen forecast (same as the base parser's "Selected")
  Index 3: A3         — alt forecast model
  Index 4: A6         — alt forecast model
  Index 5: E          — alt forecast model
  Index 6: E1         — alt forecast model
  Index 7: E2         — alt forecast model
  Index 8: E3         — alt forecast model
  Index 9: M          — alt forecast model

Timestamp parsing:
  Raw HE cell: "01FEB2022:01:00:00"
  `df["datetime"] = pd.to_datetime(df['HE'], format="%d%b%Y:%H:%M:%S")`

No error columns are computed here (that's the base parser's job) — this is a
wide feature table: one row per datetime, one column per (zone, model).
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

# Columns pulled from each sheet, in xlsx order (index 0-9). "Actual"/"Selected" match
# the base parser's naming; A3/A6/E/E1/E2/E3/M are the extra alt-forecast-model columns.
MODEL_COLS = ["Actual", "Selected", "A3", "A6", "E", "E1", "E2", "E3", "M"]

HE_PATTERN = re.compile(r"^\d{2}[A-Z]{3}\d{4}:\d{2}:\d{2}:\d{2}$")


def parse_sheet(xf: pd.ExcelFile, sheet: str) -> pd.DataFrame:
    """Extract (datetime, Actual, Selected, A3, A6, E, E1, E2, E3, M) from one sheet."""

    # usecols=range(10) → HE (timestamp) + Actual + Selected + 7 alt-model columns
    df = xf.parse(sheet, header=0, usecols=list(range(10)))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names ("Selected " etc.)

    # Keep only data rows (header/footer rows have non-timestamp HE values)
    df = df.dropna(subset=["HE"]).copy()
    df["HE"] = df["HE"].astype(str)
    df = df[df["HE"].apply(lambda v: bool(HE_PATTERN.match(v)))].copy()

    if df.empty:
        return pd.DataFrame(columns=["datetime", *MODEL_COLS])

    df["datetime"] = pd.to_datetime(df["HE"], format="%d%b%Y:%H:%M:%S")

    missing_cols = [c for c in MODEL_COLS if c not in df.columns]
    if missing_cols:
        log.warning("    Sheet missing expected model columns: %s", missing_cols)
        for c in missing_cols:
            df[c] = pd.NA

    return df[["datetime", *MODEL_COLS]].reset_index(drop=True)


def parse_file(path: Path) -> pd.DataFrame | None:
    """Parse all sheets from one xlsx file, return wide DataFrame or None on failure."""
    log.info("Parsing %s", path.name)
    try:
        xf = pd.ExcelFile(path, engine="openpyxl")
    except Exception as exc:
        log.error("  Could not open %s: %s", path.name, exc)
        return None

    available = set(xf.sheet_names)
    missing = [s for s in ZONE_SHEETS if s not in available]
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
        rename_map = {c: f"{c.lower()}_{sheet}" for c in MODEL_COLS}
        df_sheet = df_sheet.rename(columns=rename_map)
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
    out_path = OUT_DIR / f"mid_term_load_forecast_models_{min_tag}_{max_tag}.parquet"

    pq.write_table(
        pa.Table.from_pandas(combined, preserve_index=False),
        out_path,
        compression="snappy",
    )
    log.info("Written → %s (%d rows, %d cols)", out_path, len(combined), len(combined.columns))


if __name__ == "__main__":
    main()
