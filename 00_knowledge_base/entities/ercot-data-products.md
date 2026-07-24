---
title: ERCOT Data Products
type: entity
tags: [data-source, api, ercot]
status: developing
sources: 0
updated: 2026-07-24
---

# ERCOT Data Products

Reference for the ERCOT datasets feeding this project and where they come from.
**Authoritative list** per [[sources/2026-06-30_data-and-eda-notes]].

| Product                  | What                               | Report / source                                               | Granularity                                                           | Extraction code                                       |
| ------------------------ | ---------------------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------- |
| Wind production          | WPP by geography (NP4-742-CD)      | live API                                                      | hourly, by **wind region** (6, not weather zone — see [[load-zones]]) | `ercot_wpp_by_geo.py`, `ercot_wpp_archive.py`         |
| Solar production         | Solar PP by geography (NP4-745-CD) | live API                                                      | hourly                                                                | `ercot_spp_by_geo.py`                                 |
| Actual load              | By forecast zone                   | **NP6-346-CD** archive (2021–Nov 2023) + live API (Dec 2023–) | by FZN                                                                | `ercot_load_by_fzn.py`, `ercot_load_archive.py`       |
| Temperature              | County temp (daily, legacy)        | **GRIDMET**                                                   | daily, per county                                                     | none — pre-existing `2_cleaned` parquet only, no scraper in repo |
| Temperature (hourly)     | Texas-statewide mean temp          | **ERA5** (Copernicus CDS reanalysis) — added 2026-07-21 per [[sources/2026-07-20_meeting-notes]] | hourly, Texas-statewide (masked to state boundary, not per-county) | `era5_ercot_temp_2021-2025.py`, checked via `00_check/02_era5_ercot_temp.ipynb` |
| NG — Henry Hub           | Spot                               | EIA `rngwhhdd`                                                | daily (corrected 2026-07-07; was mislabeled "hourly")                 | (to add — new scraper)                                |
| NG — Citygate / TX power | S. TX prices                       | EIA `ng_pri_sum_dcu_stx_m`                                    | monthly                                                               | (to add — new scraper)                                |
| MTLF                     | Mid-term load forecast             | Public API                                                    | hourly, by weather zone                                               | `parse_mid_term_load_forecast_parquet.py`             |
| DAM/RTM SPP (bulk)       | Excel report archives              | reports 13060 / 13061                                         | hourly, by LZ                                                         | `organize_lmp_parquet.py`, `organize_rtm_lmp_2026.py` |
| Price adders             | Reserve/adder prices               | **NP6-793-ER**                                                | 15-min, system-wide                                                   | `parse_rtm_price_adders*.py`                          |
| Renewable generation (wind+solar) | Combined hourly Wind+Solar output | manual bulk download: `IntGenbyFuel20{20-22}.xlsx` (fuel mix, 15-min) + **PG7-126-M** "Hourly Aggregated Wind and Solar Output" (2023–2025 portion; report ID confirmed 2026-07-07) | hourly, 2020-01-01–2026-01-01 (52,614 rows) | `hourly_solar_wind_generation_2021_2025.ipynb` → `2_cleaned/generation/hourly_solar_wind_generation_2020_2025.parquet` |
| Non-renewable capacity | Generation capacity by fuel type (gas-cc + gas-other only; coal/nuclear/diesel excluded — together ~25% of thermal capacity, but no coal/nuclear and only minimal diesel is planned per ERCOT's forecast) | ERCOT [Capacity Changes by Fuel Type Charts](https://www.ercot.com/files/docs/2026/06/03/Capacity-Changes-by-Fuel-Type-Charts_May_2026.xlsx) (May 2026), decided 2026-07-06, reconfirmed 2026-07-07 | yearly, 2020–2025 | manual → `2_cleaned/generation/ERCOT nonRE capacity 2020-2025.csv` |
| Seven-Day Load Forecast by Model & Weather Zone | Per-model hourly load prediction, current day → 7 days ahead; day-ahead slice kept before DAM close | **NP3-565-CD**, live, hourly report cadence — identified 2026-07-07, extractor built 2026-07-14 | hourly, by weather zone, 7-day horizon (day-ahead slice extracted) | `ercot_mtlf_day_ahead.py` — trial pull only so far (`mtlf_day_ahead_trial.csv`); full extract not yet run |
| Seven-Day Load Forecast by Weather Zone | The **single official** hourly forecast (current day → 7 days ahead), 8 weather zones + `systemTotal`; **no** per-model/`inUseFlag` columns (that's the 565 variant above) | **NP3-561-CD** (Report Type ID 12312), **archive** (live returns 0 for 2023 — short rolling window) — added 2026-07-22 | hourly, by weather zone, 8-day snapshot reposted ~hourly | `ercot_7d_load_fcast_wzn_archive.py` — every posting kept, `postedDatetime` injected; **Aug 2023 run** → `01_data/1.2_raw_api/load_fcast_wzn_archive_20230801_20230831.parquet` (142,776 rows) |

The NP3-561-CD Aug-2023 pull was EDA'd 2026-07-24 in `02_analysis/00.0_load_fcast_wzn_aug2023`
— fills the "visual-check EDA notebook intentionally left for the human" gap noted when the
pipeline was built (2026-07-22). See [[mid-term-load-forecast]], [[notebook-catalog]].

Script architecture & behavior: [[extraction-scripts]].

> ⚠️ CONTRADICTION (resolved): legacy extraction used nodal **NP6-788-CD** for RTM LMP
> (`04_jobs/lmp_np6788cd*`, `organize_*lmp*.py`). The current data plan uses **report 13061
> (RTM SCED SPP by load zone)** instead. Keep NP6-788-CD nodal pulls only for the
> [[lmp-spp]] PA-vs-SPP validation; use 13060/13061 for zonal price/volatility series.

Access via ERCOT **Public API / EMIL** + bulk archive zips; shared helpers in
`ercot_common.py`. Large pulls run as batch jobs under `04_jobs/`. Mapping references in
[[load-zones]].

Extraction mechanics (auth, pitfalls, timeouts, EMIL, SLURM): [[data-extraction-guide]].
Pipeline from here to findings: [[analysis-workflow]].

> **Resolved 2026-07-10:** the 2026-07-06 raw drop (`01_data/1.1_raw_bulk/WindSolar Hourly Agg/`)
> now has a parser — see the "Renewable generation" row above. Output is a **system-wide,
> coarser-granularity** series (hourly, 2020–2026), distinct from the live by-geo wind/solar
> API pipeline already covered above and in [[wind-power-production]] (does not replace it).
>
> **Resolved 2026-07-17:** the downstream notebook that merges this renewable-gen series with
> load/price/capacity to compute the load-vs-firm-capacity ("spare capacity") metric
> (`(load − renewable_gen) / non_re_capacity`, [[sources/2026-07-06_weekly-meeting]]) is now
> `06_spare_capacity` (the earlier `06_metric_nonvariable_load_capacity`, broken on an
> incomplete-SQL cell, was deleted 2026-07-14 and replaced). The metric runs clean and
> correlates strongly with `log(rtm_price)` — see
> [[analysis/spare-capacity-correlates-with-rtm-price]], [[notebook-catalog]].

## Related
- [[ercot]] · [[rtm-dam]] · [[eia]] · [[ordc-price-adders]] · [[rtc-b-asdc]] · [[load-zones]]
- [[data-extraction-guide]] · [[analysis-workflow]] · [[notebook-catalog]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-07-06_weekly-meeting]] ·
  [[sources/2026-07-07_research-update]] · [[sources/2026-07-13_weekly-meeting-spare-capacity]]
