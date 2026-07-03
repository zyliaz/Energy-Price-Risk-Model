---
title: Weather (HDD / CDD)
type: concept
tags: [weather, demand-driver, ercot]
status: stub
sources: 1
updated: 2026-07-03
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

## Findings
- **(2026-07-01)** Total load vs temperature shows an **upward quadratic trend over the
  years** — total load is rising (HDD EDA). See [[load-and-demand]].
- **(2026-07-03)** Load ≈ **population × (AC + heating)**; Texas's ongoing population
  growth is named as the first-order driver behind rising load. Temp-vs-load is
  **U-shaped**, and the cooling (CDD) side of the curve rose **~50% from 2021 to 2022**.
  HDD/CDD vs load shows a strong correlation for nonzero points. See
  [[analysis/2026-07-03_empirical-findings-summary]].

## Related
- [[load-and-demand]] · [[price-volatility]] · [[feature-engineering]] · [[load-zones]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-07-01_research-meeting]] ·
  [[sources/2026-07-03_analysis-summary]]
