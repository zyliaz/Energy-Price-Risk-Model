---
title: ERCOT Data Products
type: entity
tags: [data-source, api, ercot]
status: developing
sources: 0
updated: 2026-06-30
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
| NG — Henry Hub           | Spot                               | EIA `rngwhhdd`                                                | hourly                                                                | (to add — new scraper)                                |
| NG — Citygate / TX power | S. TX prices                       | EIA `ng_pri_sum_dcu_stx_m`                                    | monthly                                                               | (to add — new scraper)                                |
| MTLF                     | Mid-term load forecast             | Public API                                                    | hourly, by weather zone                                               | `parse_mid_term_load_forecast_parquet.py`             |
| DAM/RTM SPP (bulk)       | Excel report archives              | reports 13060 / 13061                                         | hourly, by LZ                                                         | `organize_lmp_parquet.py`, `organize_rtm_lmp_2026.py` |
| Price adders             | Reserve/adder prices               | **NP6-793-ER**                                                | 15-min, system-wide                                                   | `parse_rtm_price_adders*.py`                          |
|                          |                                    |                                                               |                                                                       |                                                       |

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

## Related
- [[ercot]] · [[rtm-dam]] · [[eia]] · [[ordc-price-adders]] · [[rtc-b-asdc]] · [[load-zones]]
- [[data-extraction-guide]] · [[analysis-workflow]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]]
