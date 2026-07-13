---
title: Data Sources, Mappings & EDA Notes
type: source
tags: [data, methods, eda, feature-engineering]
status: developing
date_ingested: 2026-06-30
source_kind: note
raw_path: chat upload (project notes, 2026-06-30)
updated: 2026-06-30
---

# Data Sources, Mappings & EDA Notes

The project's data plan and current empirical findings, provided as working notes.

## Data sources (authoritative list)
| # | Series | Report / source | Granularity | Notes |
|---|---|---|---|---|
| 1 | DAM price | report **13060** archive (DAM SPP) | hourly, by load zone | bulk zip |
| 2 | RTM price | report **13061** archive (RTM SCED SPP) | hourly, by load zone | bulk zip |
| 3 | Wind production | live API ("WPP by geography") | hourly, by weather zone | |
| 4 | Solar production | live API ("Solar PP by geography") | hourly | **new stream** |
| 5 | Actual load | **NP6-346-CD** archive (2021–Nov 2023) + live API (Dec 2023–) | by forecast zone | |
| 6 | Temperature | **GRIDMET** package | daily, per county | |
| 7a | NG — Henry Hub | EIA `rngwhhdd` | daily | corrected 2026-07-07 (was mislabeled "hourly"; raw `.xls` is a daily spot series, resampled monthly downstream) |
| 7b | NG — Citygate (S. TX) | EIA `ng_pri_sum_dcu_stx_m` | monthly | |
| 7c | NG — TX Electric Power Price | EIA (same as 7b) | monthly | |
| 8 | Price adders | **NP6-793-ER** | 15-min, system-wide | field sets differ pre/post Dec 2025 |
| 9 | Load forecast | ERCOT MTLF | hourly, by weather zone | forecast error 2022–2025; 2021 long-term; 2020 limited |
| 10 | Power outages | (TBD) | | open item |

**Price-adder fields by era** (report NP6-793-ER): 2014–Nov 2025 = `RTRSVPOR`, `RTRSVPOFF`,
`RTRDP`; Dec 2025+ = `RTRDPA`, `RTRDPRU`, `RTRDPRD`, `RTRDPRRS`, `RTRDPECRS`, `RTRDPNS`.
See [[ordc-price-adders]] and [[rtc-b-asdc]].

## Mapping references
- Wind/solar **region → county**: ERCOT "Wind and Solar Regions to County Mapping.xlsx" (2024-05).
- Load zone → county: from Victoria Farella.
- Load zone → plant-level generation (2021–2024): from Victoria Farella.
- ERCOT **load-zone shapefiles**.
See [[load-zones]].

## Feature engineering
- **Adder demand** = load forecast − actual load (available from 2021). See [[mid-term-load-forecast]].
- **CDD** = actual temp − 65°F threshold. See [[weather-hdd-cdd]].
- **Capacity factor** from wind/solar production (production → C.F.). See [[wind-power-production]].

## EDA findings (current)
- **NG prices:** TX power-producer, TX citygate, and Henry Hub are strongly correlated
  monthly **except for extreme deviations** (notably **Feb 2021 / Winter Storm Uri**) — a
  substantial source of ERCOT risk/volatility. Henry Hub vs RTM noted as "insurance." → [[natural-gas-prices]]
- **Price adders, pre-Dec-2025 schema:** adder activation (Boolean) vs RTM price quantile
  is smoothed but **steepens sharply at higher quantiles**; tails increase in the top 5
  percentile **except RTRDP**, whose tail is non-monotonic. Value distribution (log scale):
  larger-adder bins have lower counts, except RTRDP's right tail is tilted by Uri. → [[ordc-price-adders]]
- **Price adders, post-Dec-2025 schema:** same analyses (activation by quantile, log
  distribution) being rerun on new fields. → [[rtc-b-asdc]]
- **Load + prediction error vs RTM price:** time series (load & price); price vs actual
  load scatter; **log(price) vs load prediction error shows no strong correlation**. → [[load-and-demand]]
- **HDD/CDD vs load vs price:** Texas households mostly cool, little heating (transitioning
  to electric heat). Load ≈ population × (AC + heating). HDD: population-growth + heatwave
  driven; CDD: population driven. → [[weather-hdd-cdd]]

## Action items
- Run full wind & solar extraction script (resolve timeout issue). See [[ercot-data-products]].
- Collect LMP data to validate PA > SPP / negative-LMP hypothesis. See [[lmp-spp]].

## Affected wiki pages
[[ercot-data-products]], [[natural-gas-prices]], [[ordc-price-adders]], [[rtc-b-asdc]],
[[load-and-demand]], [[mid-term-load-forecast]], [[weather-hdd-cdd]],
[[wind-power-production]], [[load-zones]], [[feature-engineering]]

## Contradictions / caveats
- RTM price source is **report 13061 (SCED SPP by load zone)**, not the nodal
  **NP6-788-CD** used in legacy extraction jobs. Reconcile in [[ercot-data-products]].
