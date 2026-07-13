---
title: Cooling side of the temp–load curve rose ~50% (2021→2022), tracking population
type: analysis
tags: [ercot, weather, load, structural-change]
status: developing
notebook: 03_notebooks/01_eda/08_hdd_eda.ipynb
date: 2026-07-03
updated: 2026-07-07
---

# Cooling side of the temp–load curve rose ~50% (2021→2022), tracking population

**Question asked:** How does temperature translate into ERCOT load, and is that
relationship stable over time?

**Method / data used:** `03_notebooks/01_eda/08_hdd_eda.ipynb` — daily HDD/CDD
(GRIDMET) merged with total load and RTM price, fit per year.

**Answer / finding:** Texas load ≈ population × (AC + heating): temp-vs-load is
**U-shaped**, and the cooling (**CDD**) side of the curve rose **~50% from 2021 to 2022**,
tracking population growth. HDD/CDD vs load correlates strongly for nonzero points.

**Citations:** [[weather-hdd-cdd]], [[load-and-demand]],
[[sources/2026-07-03_analysis-summary]], `03_notebooks/01_eda/08_hdd_eda.ipynb`,
`01_data/2_cleaned/.../Daily_HDD_rtm_load_2021_2025.csv`.

## Related
- [[weather-hdd-cdd]]
- [[load-price-correlation-is-seasonal]]
