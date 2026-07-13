---
title: ERCOT Data Products
type: entity
tags: [data-source, api, ercot]
status: developing
sources: 0
updated: 2026-07-10
---

# ERCOT Data Products

Reference for the ERCOT datasets feeding this project and where they come from.
**Authoritative list** per [[sources/2026-06-30_data-and-eda-notes]].

| Product                  | What                               | Report / source                                               | Granularity                                                           | Extraction code                                       |
| ------------------------ | ---------------------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------- |
| Wind production          | WPP by geography (NP4-742-CD)      | live API                                                      | hourly, by **wind region** (6, not weather zone — see [[load-zones]]) | `ercot_wpp_by_geo.py`, `ercot_wpp_archive.py`         |
| Solar production         | Solar PP by geography (NP4-745-CD) | live API                                                      | hourly                                                                | `ercot_spp_by_geo.py`                                 |
| Actual load              | By forecast zone                   | **NP6-346-CD** archive (2021–Nov 2023) + live API (Dec 2023–) | by FZN                                                                | `ercot_load_by_fzn.py`, `ercot_load_archive.py`       |
| Temperature              | County temp                        | **GRIDMET**                                                   | daily, per county                                                     | (to add)                                              |
| NG — Henry Hub           | Spot                               | EIA `rngwhhdd`                                                | daily (corrected 2026-07-07; was mislabeled "hourly")                 | (to add — new scraper)                                |
| NG — Citygate / TX power | S. TX prices                       | EIA `ng_pri_sum_dcu_stx_m`                                    | monthly                                                               | (to add — new scraper)                                |
| MTLF                     | Mid-term load forecast             | Public API                                                    | hourly, by weather zone                                               | `parse_mid_term_load_forecast_parquet.py`             |
| DAM/RTM SPP (bulk)       | Excel report archives              | reports 13060 / 13061                                         | hourly, by LZ                                                         | `organize_lmp_parquet.py`, `organize_rtm_lmp_2026.py` |
| Price adders             | Reserve/adder prices               | **NP6-793-ER**                                                | 15-min, system-wide                                                   | `parse_rtm_price_adders*.py`                          |
| Renewable generation (wind+solar) | Combined hourly Wind+Solar output | manual bulk download: `IntGenbyFuel20{20-22}.xlsx` (fuel mix, 15-min) + **PG7-126-M** "Hourly Aggregated Wind and Solar Output" (2023–2025 portion; report ID confirmed 2026-07-07) | hourly, 2020-01-01–2026-01-01 (52,614 rows) | `hourly_solar_wind_generation_2021_2025.ipynb` → `2_cleaned/generation/hourly_solar_wind_generation_2020_2025.parquet` |
| Non-renewable capacity | Generation capacity by fuel type (gas-cc + gas-other only; coal/nuclear/diesel excluded — together ~25% of thermal capacity, but no coal/nuclear and only minimal diesel is planned per ERCOT's forecast) | ERCOT [Capacity Changes by Fuel Type Charts](https://www.ercot.com/files/docs/2026/06/03/Capacity-Changes-by-Fuel-Type-Charts_May_2026.xlsx) (May 2026), decided 2026-07-06, reconfirmed 2026-07-07 | yearly, 2020–2025 | manual → `2_cleaned/generation/ERCOT nonRE capacity 2020-2025.csv` |
| Seven-Day Load Forecast by Model & Weather Zone (planned) | Per-model hourly load prediction, current day → 7 days ahead | **NP3-565-CD**, live, hourly report cadence — identified 2026-07-07 | hourly, by weather zone, 7-day horizon | (to add — extract 3hr/6hr/day-ahead slices; tracked as Notion to-do "real time load prediction 3, 6 hours + day ahead pipeline") |

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
> A downstream WIP notebook, `06_metric_nonvariable_load_capacity` (see [[notebook-catalog]]),
> merges this renewable-gen series with load/price/capacity to compute the
> load-vs-firm-capacity metric proposed in [[sources/2026-07-06_weekly-meeting]]
> (`(load − renewable_gen) / non_re_capacity`). Notebook currently fails on a later, unrelated
> price-metric cell (incomplete SQL) — the capacity-ratio metric itself runs clean.

## Related
- [[ercot]] · [[rtm-dam]] · [[eia]] · [[ordc-price-adders]] · [[rtc-b-asdc]] · [[load-zones]]
- [[data-extraction-guide]] · [[analysis-workflow]] · [[notebook-catalog]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-07-06_weekly-meeting]] ·
  [[sources/2026-07-07_research-update]]
