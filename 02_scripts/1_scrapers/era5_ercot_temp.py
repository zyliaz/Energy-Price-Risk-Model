import os
import cdsapi
import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr
from dotenv import load_dotenv

## CHANGE DIRECTORY
OUTPUT_DIR = "../../01_data/1.2_raw_api/era5_hourly_temp"
os.makedirs(OUTPUT_DIR, exist_ok=True)

GEO_DIR = "../../01_data/1.3_raw_other/mapping/texas_state_boundary.geojson"

CLEANED_DIR = "../../01_data/2_cleaned/weather"
os.makedirs(CLEANED_DIR, exist_ok=True)

# texas boundary
texas_gdf = gpd.read_file(GEO_DIR).to_crs("EPSG:4326")
texas_boundary = texas_gdf.union_all()

# Texas geo box — North, West, South, East
AREA = [37, -107, 25.5, -93]

# ---------- parameters ----------
START_YEAR = 2021
END_YEAR = 2025

# 1. Define desired range in Central Prevailing Time (CPT = America/Chicago)
CPT = "America/Chicago"
start_cpt = pd.Timestamp(f"{START_YEAR}-01-01 00:00", tz=CPT)
end_cpt   = pd.Timestamp(f"{END_YEAR}-12-31 23:00",  tz=CPT)

start_utc = start_cpt.tz_convert("UTC")
end_utc   = end_cpt.tz_convert("UTC")

print(f"CPT range: {start_cpt} → {end_cpt}")
print(f"UTC range: {start_utc} → {end_utc}")

# ---------- CDS client ----------
load_dotenv()
CDS_API_URL = os.environ["CDS_API_URL"]
CDS_API_KEY = os.environ["CDS_API_KEY"]
client = cdsapi.Client(url=CDS_API_URL, key=CDS_API_KEY)


def retrieve_if_missing(client, request, out_path):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        print(f"Skipping (already exists): {out_path}")
        return
    client.retrieve("reanalysis-era5-single-levels", request, out_path)
    print(f"Saved: {out_path}")


# ---------- 2. Download ----------
# Full UTC calendar years
nc_paths = []
for year in range(START_YEAR, END_YEAR + 1):
    out_nc = os.path.join(OUTPUT_DIR, f"era5_texas_t2m_hourly_{year}.nc")
    retrieve_if_missing(client, {
        "product_type": ["reanalysis"],
        "variable": ["2m_temperature"],
        "year": [str(year)],
        "month": [f"{m:02d}" for m in range(1, 13)],
        "day": [f"{d:02d}" for d in range(1, 32)],
        "time": [f"{h:02d}:00" for h in range(24)],
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }, out_nc)
    nc_paths.append(out_nc)

# Boundary hours: tail-end UTC hours that spill past END_YEAR
# e.g. CPT 2025-12-31 23:00 = UTC 2026-01-01 05:00
if end_utc.year > END_YEAR:
    boundary_nc = os.path.join(
        OUTPUT_DIR,
        f"era5_texas_t2m_hourly_{end_utc.year}_boundary.nc",
    )
    retrieve_if_missing(client, {
        "product_type": ["reanalysis"],
        "variable": ["2m_temperature"],
        "year": [str(end_utc.year)],
        "month": [f"{end_utc.month:02d}"],
        "day": [f"{end_utc.day:02d}"],
        "time": [f"{h:02d}:00" for h in range(end_utc.hour + 1)],
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }, boundary_nc)
    nc_paths.append(boundary_nc)


# ---------- 3. Mask to Texas, average, convert UTC → CPT ----------
def get_texas_mean(nc_paths, start_cpt=None, end_cpt=None):
    if isinstance(nc_paths, str):
        nc_paths = [nc_paths]

    ds = xr.concat([xr.open_dataset(p) for p in nc_paths], dim="valid_time")

    lon2d, lat2d = np.meshgrid(ds["longitude"].values, ds["latitude"].values)
    grid_points = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(lon2d.ravel(), lat2d.ravel()),
        crs="EPSG:4326",
    )
    in_texas = grid_points.within(texas_boundary).values.reshape(lat2d.shape)

    texas_mask = xr.DataArray(
        in_texas,
        dims=("latitude", "longitude"),
        coords={"latitude": ds["latitude"], "longitude": ds["longitude"]},
    )
    
    ds_texas = ds.where(texas_mask)

    t2m_hourly_mean = ds_texas["t2m"].mean(dim=["latitude", "longitude"])

    t2m_hourly_mean_df = t2m_hourly_mean.to_dataframe(name="t2m_mean_K").reset_index()
    t2m_hourly_mean_df["t2m_mean_F"] = (t2m_hourly_mean_df["t2m_mean_K"] - 273.15) * 9 / 5 + 32

    df = t2m_hourly_mean_df.filter(['valid_time', 't2m_mean_F'])

    # Convert UTC valid_time -> CPT, shift +1h to hour-ending to match ERCOT,
    # then drop tz for merge.
    valid_time_cpt = (
        pd.to_datetime(df['valid_time'], utc=True)
          .dt.tz_convert(CPT)
        + pd.Timedelta(hours=1)
    )
    df['valid_time'] = valid_time_cpt.dt.tz_localize(None)

    # Trim to exact CPT window (already hour-ending)
    if start_cpt is not None and end_cpt is not None:
        he_start = start_cpt + pd.Timedelta(hours=1)
        he_end   = end_cpt   + pd.Timedelta(hours=1)
        mask = (valid_time_cpt >= he_start) & (valid_time_cpt <= he_end)
        df = df[mask.values].reset_index(drop=True)

    # DST fall-back: two UTC hours collapse to the same naive CPT hour;
    # average them so the output has one unique row per local hour.
    df = df.groupby("valid_time", as_index=False)["t2m_mean_F"].mean()

    df = df.rename(columns={'valid_time': 'datetime', 't2m_mean_F': 'tx_temp'})
    return df

df = get_texas_mean(nc_paths, start_cpt=start_cpt, end_cpt=end_cpt)
print(df.head())

# ---------- 4. Validation ----------
def validate_temp_df(df, start_cpt, end_cpt,
                     temp_col="tx_temp", dt_col="datetime",
                     min_f=-20, max_f=130, raise_on_fail=True):
    report = {"passed": True, "errors": [], "stats": {}}

    def fail(msg):
        report["passed"] = False
        report["errors"].append(msg)

    for col in (dt_col, temp_col):
        if col not in df.columns:
            fail(f"Missing required column: {col}")
    if not report["passed"]:
        if raise_on_fail:
            raise ValueError(f"Validation failed: {report['errors']}")
        return report

    df = df.copy()
    df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")

    # NaN checks
    n_bad_dt = df[dt_col].isna().sum()
    if n_bad_dt:
        fail(f"{n_bad_dt} unparseable/NaN datetimes")

    n_nan_temp = df[temp_col].isna().sum()
    nan_frac = n_nan_temp / max(len(df), 1)
    report["stats"]["nan_temp_frac"] = round(nan_frac, 4)
    if nan_frac > 0.01:
        fail(f"{n_nan_temp} NaN temps ({nan_frac:.2%}) — check Texas mask alignment")

    # duplicate timestamps
    n_dupes = df[dt_col].duplicated().sum()
    if n_dupes:
        fail(f"{n_dupes} duplicate timestamps")

    # missing hourly intervals — build expected range as tz-aware CPT
    # shifted +1h for hour-ending (naturally skips nonexistent spring-forward
    # hours), then strip tz
    he_start = start_cpt + pd.Timedelta(hours=1)
    he_end   = end_cpt   + pd.Timedelta(hours=1)
    expected = pd.date_range(
        start=he_start, end=he_end, freq="h",
    ).tz_localize(None)
    present = set(df[dt_col].dropna())
    missing = sorted(set(expected) - present)
    report["stats"]["expected_hours"] = len(expected)
    report["stats"]["actual_hours"] = len(present)
    report["stats"]["missing_hours"] = len(missing)
    if missing:
        fail(f"{len(missing)} missing hourly intervals "
             f"(first few: {missing[:3]})")

    # out-of-range temps
    valid_temp = df[temp_col].dropna()
    oob = valid_temp[(valid_temp < min_f) | (valid_temp > max_f)]
    if len(oob):
        fail(f"{len(oob)} temps outside [{min_f}, {max_f}]°F "
             f"(min={valid_temp.min()}, max={valid_temp.max()})")
    report["stats"]["temp_min"] = float(valid_temp.min()) if len(valid_temp) else None
    report["stats"]["temp_max"] = float(valid_temp.max()) if len(valid_temp) else None

    print(f"[validation] passed={report['passed']} | "
          f"rows={len(df)} | missing={len(missing)} | "
          f"dupes={n_dupes} | nan_temp={n_nan_temp} | oob={len(oob)}")
    for e in report["errors"]:
        print(f"  ERROR: {e}")

    if not report["passed"] and raise_on_fail:
        raise ValueError(f"Validation failed: {report['errors']}")
    return report


validate_temp_df(df, start_cpt, end_cpt)

# ---------- 5. Export ----------
df.to_csv(
    os.path.join(CLEANED_DIR, "Texas_hourly_temp_2021_2025.csv"),
    index=False,
)
print(f"Exported {len(df)} rows to {CLEANED_DIR}")
