---
title: Weather (HDD / CDD)
type: concept
tags: [weather, demand-driver, ercot]
status: developing
sources: 4
updated: 2026-10-28
---

# Weather — HDD / CDD

Heating and Cooling Degree Days summarize temperature as a load driver. Extreme weather
(winter storms, summer heat) is the upstream cause of most ERCOT scarcity events, linking
weather → [[load-and-demand]] → reserves → [[ordc-price-adders]] → [[price-volatility]].

## Definitions & data
- **CDD** = actual temp − 65°F; **HDD** = 65°F − actual temp. See [[feature-engineering]].
- **Two temperature sources now in the repo, used by different notebooks (2026-07-24):**
  - **GRIDMET** — daily, aggregated **per county** (mapped to zones via [[load-zones]]).
    Output: `01_data/2_cleaned/weather/Texas_2020_2025_daily_HDD_CDD.parquet`. Still the
    sole input to `08_hdd_eda` (single-source weather EDA); that notebook also derives
    `Texas daily average temp HDD CDD 2020-2025.csv` from it by daily resampling.
  - **ERA5** (Copernicus Climate Data Store reanalysis) — **hourly**, Texas-statewide mean
    (grid cells masked to the TX state boundary, not per-county). Added 2026-07-21 per
    [[sources/2026-07-20_meeting-notes]]: the modeling work needs hourly, not daily,
    degree-days. Pipeline: `02_scripts/1_scrapers/era5_ercot_temp_2021-2025.py` +
    `03_notebooks/00_check/02_era5_ercot_temp.ipynb`. Output:
    `01_data/2_cleaned/weather/Texas_hourly_temp_2021_2025.csv` (`datetime, tx_temp`
    in °F). Verified 2026-07-24: 43,824 rows, full hourly coverage 2021-01-01–2025-12-31,
    0 nulls/dupes, temp range 7–104°F. Used directly (not via a daily HDD/CDD file) by
    `06_spare_capacity` and `01_regression_data` — `degree_days = ABS(tx_temp − 65)`
    computed inline. Requires CDS credentials (`CDS_API_URL`/`CDS_API_KEY` in `.env`);
    raw `.nc` files already downloaded for 2021–2025, so re-running the script/notebook
    with those files present does **not** re-hit the live API (existing-file skip check
    in the `.py`, but **not** in the notebook's cell 4 "test cell" — don't re-run that cell
    blind). See [[data-extraction-guide]] pitfall #15, [[ercot-data-products]].
  - **Current state (verified 2026-10-28):** the cleaned ERA5 files are **CPT hour-ending**
    (scraper rewritten 2026-07-29 as `era5_ercot_temp.py`; see [[extraction-scripts]]):
    mean temp peaks at hour 16–17 and troughs at hour 8. The consuming notebooks
    (`06_spare_capacity`, `01_regression_data`, `01.1_model_data_v2`) no longer convert.
    Coverage: `Texas_hourly_temp_2021_2025.csv` + `Texas_hourly_temp_20260101_20261021.csv`;
    RTC+B-window file `Texas_hourly_temp_20251205_20261021.csv` (7,703 h). Sep–Oct 2026 are
    preliminary ERA5T. Details: [[notebook-catalog]] (`02_era5_ercot_temp`).

> ✅ **CONTRADICTION / data-integrity bug, found and fixed 2026-07-24:** ERA5's raw
> `Texas_hourly_temp_2021_2025.csv` `datetime` column is **UTC**, not the project's
> hour-ending **Central Time** convention (see [[feature-engineering]] "Datetime
> convention"). Confirmed via its diurnal profile: mean temp peaked at raw hour 21 and
> troughed at raw hour 11–12 — a ~6 h shift from the expected local peak (~15–17h) and
> trough (~5–7h), consistent with an unconverted UTC label. **Fix applied at the
> consumption layer, not the scraper** (the raw ERA5 pull is correct as ERA5 data — UTC is
> its native convention; the human asked that the already-scraped raw/cleaned files not be
> touched): `06_spare_capacity.ipynb` and `01_regression_data.ipynb` now convert
> `df_temp['datetime']` from UTC → `America/Chicago` (tz-aware, then made naive) immediately
> after loading `Texas_hourly_temp_2021_2025.csv` and before joining, averaging the one
> repeated local hour/year from fall-back DST. Re-verified via fresh `nbconvert --execute`,
> both **PASS 2026-07-24**. Resulting `degree_days`↔`rtm_price` correlation: 0.184 overall
> (was computed against misaligned hours before); `degree_days`↔`spare_capacity`: 0.579 —
> consistent with the 2026-07-20 meeting note's observation that both are driven by load.
> `era5_ercot_temp_2021-2025.py` and its check notebook (`00_check/02_era5_ercot_temp`) are
> **unchanged** — the raw/cleaned ERA5 files stay UTC as originally scraped; only the two
> consuming notebooks apply the conversion. See [[sources/2026-07-20_meeting-notes]],
> [[feature-engineering]].
> **Superseded 2026-07-29:** the scraper rewrite moved the UTC→CPT conversion into the
> pipeline, and the consumption-layer conversions were removed. The 2026-07-24 description above
> is history only; the current state is in the ERA5 bullet above.

## Texas-specific insight
- Texas households mostly **cool**, with little heating (transitioning to electric heat).
- Load ≈ population × (AC + heating).
- **CDD is population-driven**; **HDD is population-growth + heatwave driven**. As heating
  electrifies, HDD's load impact is rising.

## Findings
- **(2026-07-01)** Total load vs temperature shows an **upward quadratic trend over the
  years** — total load is rising (HDD EDA). See [[load-and-demand]].
- **(2026-07-03)** Load ≈ **population × (AC + heating)**; Texas's ongoing population
  growth is named as the first-order driver behind rising load. Temp-vs-load is
  **U-shaped**, and the cooling (CDD) side of the curve rose **~50% from 2021 to 2022**.
  HDD/CDD vs load shows a strong correlation for nonzero points. See
  [[analysis/cooling-demand-rising-with-population]].

## Related
- [[load-and-demand]] · [[price-volatility]] · [[feature-engineering]] · [[load-zones]] ·
  [[ercot-data-products]] · [[notebook-catalog]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-07-01_research-meeting]] ·
  [[sources/2026-07-03_analysis-summary]] · [[sources/2026-07-20_meeting-notes]]
