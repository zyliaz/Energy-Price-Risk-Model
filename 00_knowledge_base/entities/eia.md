---
title: EIA
type: entity
tags: [data-source, natural-gas, federal]
status: stub
sources: 0
updated: 2026-07-07
---

# EIA (U.S. Energy Information Administration)

Federal source for energy data. In this project it supplies **natural-gas spot prices**
(Henry Hub `rngwhhdd`, hourly; TX Citygate `ng_pri_sum_dcu_stx_m`, monthly) used to test
fuel-cost correlation with ERCOT power prices.

## Use in this project
- Current series: Henry Hub + TX Citygate/Electric Power Price, both **(to add — new
  scraper)** per [[ercot-data-products]].
- Waha hub download (`eia_ng_waha_download.py`) **removed 2026-07-03** — legacy, out of
  scope for the current topic. See [[extraction-scripts]].
- Feeds [[natural-gas-prices]] analysis.

## Related
- [[natural-gas-prices]] · [[extraction-scripts]] · [[ercot-data-products]]
