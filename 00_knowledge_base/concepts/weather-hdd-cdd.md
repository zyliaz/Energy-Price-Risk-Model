---
title: Weather (HDD / CDD)
type: concept
tags: [weather, demand-driver, ercot]
status: stub
sources: 0
updated: 2026-06-30
---

# Weather — HDD / CDD

Heating and Cooling Degree Days summarize temperature as a load driver. Extreme weather
(winter storms, summer heat) is the upstream cause of most ERCOT scarcity events, linking
weather → [[load-and-demand]] → reserves → [[ordc-price-adders]] → [[price-volatility]].

## Definitions & data
- **CDD** = actual temp − 65°F; **HDD** = 65°F − actual temp. See [[feature-engineering]].
- Source: **GRIDMET** package, daily, aggregated **per county** (mapped to zones via
  [[load-zones]]).

## Texas-specific insight
- Texas households mostly **cool**, with little heating (transitioning to electric heat).
- Load ≈ population × (AC + heating).
- **CDD is population-driven**; **HDD is population-growth + heatwave driven**. As heating
  electrifies, HDD's load impact is rising.

## Legacy work
- HDD EDA: `11_[IN PROGRESS]_HDD_eda`.

## Related
- [[load-and-demand]] · [[price-volatility]] · [[feature-engineering]] · [[load-zones]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]]
