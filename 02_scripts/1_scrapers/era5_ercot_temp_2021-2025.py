import os
import requests
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

# Texas geo box
# North, West, South, East
AREA = [37, -107, 25.5, -93]

# years parameter
START_YEAR = 2021
END_YEAR = 2025

# call ERA5 for all years
load_dotenv()
CDS_API_URL = os.environ["CDS_API_URL"]
CDS_API_KEY = os.environ["CDS_API_KEY"]  # https://cds.climate.copernicus.eu/profile
client = cdsapi.Client(url=CDS_API_URL, key=CDS_API_KEY)

# loop through the year to select TX grid and 
for year in range(START_YEAR, END_YEAR + 1):

    out_nc = os.path.join(OUTPUT_DIR,f"era5_texas_t2m_hourly_{year}.nc")

    if os.path.exists(out_nc) and os.path.getsize(out_nc) > 0:
        print(f"Skipping {year}: already downloaded")
        continue

    client.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": ["reanalysis"],
            "variable": ["2m_temperature"],
            "year": [str(year)],
            "month": [f"{month:02d}" for month in range(1, 13)],
            "day": [f"{day:02d}" for day in range(1, 32)],
            "time": [f"{hour:02d}:00" for hour in range(24)],
            "area": AREA,
            "data_format": "netcdf",
            "download_format": "unarchived",
        },
        out_nc,
    )
    print(f"Saved: {out_nc}")

# mask with TX boundary
def get_texas_mean(year):
    nc_path = os.path.join(OUTPUT_DIR, f"era5_texas_t2m_hourly_{year}.nc")
    ds = xr.open_dataset(nc_path)

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

    # take average
    t2m_hourly_mean = ds_texas["t2m"].mean(dim=["latitude", "longitude"])

    t2m_hourly_mean_df = t2m_hourly_mean.to_dataframe(name="t2m_mean_K").reset_index()
    t2m_hourly_mean_df["t2m_mean_F"] = round((t2m_hourly_mean_df["t2m_mean_K"] - 273.15) * 9 / 5 + 32, 0)

    df = t2m_hourly_mean_df.filter(['valid_time', 't2m_mean_F'])
    df = df.rename(columns={'valid_time' : 'datetime', 't2m_mean_F': 'tx_temp'})
    return df

# mask and take average
df = pd.DataFrame()
for year in range(START_YEAR, END_YEAR + 1):
    df_year = get_texas_mean(year)
    df = pd.concat([df, df_year], ignore_index=True)


# validation
def validate_temp_df(df, start_year=START_YEAR, end_year=END_YEAR,
                     temp_col="tx_temp", dt_col="datetime",
                     min_f=-20, max_f=130, raise_on_fail=True):
    """
    Validate the assembled Texas hourly temperature dataframe.
    Checks: schema, NaNs, duplicate timestamps, missing hourly intervals,
    and out-of-range temperatures. Returns a dict report; optionally raises.
    """
    report = {"passed": True, "errors": [], "warnings": [], "stats": {}}

    def fail(msg):
        report["passed"] = False
        report["errors"].append(msg)

    # 0. schema
    for col in (dt_col, temp_col):
        if col not in df.columns:
            fail(f"Missing required column: {col}")
    if not report["passed"]:
        if raise_on_fail:
            raise ValueError(f"Validation failed: {report['errors']}")
        return report

    # normalize datetime
    df = df.copy()
    df[dt_col] = pd.to_datetime(df[dt_col], utc=True, errors="coerce")

    # 1. NaN checks
    n_bad_dt = df[dt_col].isna().sum()
    if n_bad_dt:
        fail(f"{n_bad_dt} unparseable/NaN datetimes")

    n_nan_temp = df[temp_col].isna().sum()
    nan_frac = n_nan_temp / max(len(df), 1)
    report["stats"]["nan_temp_frac"] = round(nan_frac, 4)
    if nan_frac > 0.01:  # >1% NaN usually means mask/grid misalignment
        fail(f"{n_nan_temp} NaN temps ({nan_frac:.2%}) — check Texas mask alignment")

    # 2. duplicate timestamps (year-boundary concat bug)
    n_dupes = df[dt_col].duplicated().sum()
    if n_dupes:
        fail(f"{n_dupes} duplicate timestamps")

    # 3. missing hourly intervals (per full expected range)
    expected = pd.date_range(
        start=f"{start_year}-01-01 00:00",
        end=f"{end_year}-12-31 23:00",
        freq="h", tz="UTC",
    )
    present = set(df[dt_col].dropna())
    missing = sorted(set(expected) - present)
    report["stats"]["expected_hours"] = len(expected)
    report["stats"]["actual_hours"] = len(present)
    report["stats"]["missing_hours"] = len(missing)
    if missing:
        fail(f"{len(missing)} missing hourly intervals "
             f"(first few: {missing[:3]})")

    # 4. out-of-range temps (catches K->F / masking errors)
    valid_temp = df[temp_col].dropna()
    oob = valid_temp[(valid_temp < min_f) | (valid_temp > max_f)]
    if len(oob):
        fail(f"{len(oob)} temps outside [{min_f}, {max_f}]°F "
             f"(min={valid_temp.min()}, max={valid_temp.max()})")
    report["stats"]["temp_min"] = float(valid_temp.min()) if len(valid_temp) else None
    report["stats"]["temp_max"] = float(valid_temp.max()) if len(valid_temp) else None

    # summary
    print(f"[validation] passed={report['passed']} | "
          f"rows={len(df)} | missing={len(missing)} | "
          f"dupes={n_dupes} | nan_temp={n_nan_temp} | oob={len(oob)}")
    for e in report["errors"]:
        print(f"  ERROR: {e}")

    if not report["passed"] and raise_on_fail:
        raise ValueError(f"Validation failed: {report['errors']}")
    return report

validate_temp_df(df)

# sort by datetime and export
df_sorted = df.sort_values(by='datetime', ascending=False)
df_sorted.to_csv(os.path.join(CLEANED_DIR, f'Texas_hourly_temp_2021_2025.csv'), index=False)