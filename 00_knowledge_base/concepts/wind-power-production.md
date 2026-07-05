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

> **Priority (2026-07-01):** build the **solar + wind generation pipeline** so modeling can
> use **net load = load − wind − solar** (expected to model price better than raw load).
> See [[sources/2026-07-01_research-meeting]], [[extraction-scripts]].

## Data & mapping
- Wind/solar production: live API, hourly, by **wind/solar region** (6 wind / 7 solar —
  *not* the 8 MTLF weather zones; corrected 2026-07-03, see [[load-zones]]).
- Region → county mapping: ERCOT "Wind and Solar Regions to County Mapping.xlsx" (2024-05).
  See [[load-zones]].
- **Action item:** run full wind & solar extraction (resolve timeout issue).

## Open gap
⚠️ The new repo has **no WPP EDA notebook** — old `05_wpp_eda` was dropped during migration,
not renamed/kept. Extraction scripts (`ercot_wpp_by_geo.py`, `ercot_wpp_archive.py`) exist
and run; the EDA/distribution step needs to be rebuilt. See [[extraction-scripts]].

## Related
- [[load-and-demand]] · [[price-volatility]] · [[ordc-price-adders]] · [[feature-engineering]] · [[load-zones]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-07-01_research-meeting]]
