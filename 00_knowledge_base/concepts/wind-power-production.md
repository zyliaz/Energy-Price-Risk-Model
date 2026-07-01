---
title: Wind Power Production (WPP)
type: concept
tags: [renewables, supply, ercot]
status: developing
sources: 0
updated: 2026-06-30
---

# Wind Power Production (WPP)

Actual and forecast wind output in ERCOT. As a high-penetration variable resource, wind
shapes **net load** (load minus wind/solar) and its ramps, which in turn drive reserve
tightness and [[ordc-price-adders]].

## Why it matters
- Sudden wind drop-offs raise net load → tighten reserves → trigger scarcity adders.
- **Forecast error** (actual vs forecast WPP) is itself a volatility source worth isolating.
- Geographic distribution (by zone) matters for congestion/[[load-zones]].

## Solar
Solar production is a parallel live-API stream ("Solar PP by geography"), hourly. Wind +
solar together define **net load**. Both convert to **capacity factor** as features
(see [[feature-engineering]]).

## Data & mapping
- Wind/solar production: live API, hourly, by **weather zone**.
- Region → county mapping: ERCOT "Wind and Solar Regions to County Mapping.xlsx" (2024-05).
  See [[load-zones]].
- **Action item:** run full wind & solar extraction (resolve timeout issue).

## Legacy work
- EDA: `05_ercot_wpp_eda`.
- Extraction: `src/extraction/ercot_wpp_by_geo.py`, `ercot_wpp_archive.py`
  (jobs `wpp_spp_geo_apr18`, `wpp_archive_apr21`).

## Related
- [[load-and-demand]] · [[price-volatility]] · [[ordc-price-adders]] · [[feature-engineering]] · [[load-zones]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]]
