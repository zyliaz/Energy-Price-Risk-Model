---
title: EIA
type: entity
tags: [data-source, natural-gas, federal]
status: stub
sources: 0
updated: 2026-06-30
---

# EIA (U.S. Energy Information Administration)

Federal source for energy data. In this project it supplies **natural-gas spot prices**
(Waha hub) used to test fuel-cost correlation with ERCOT power prices.

## Use in this project
- Waha NG spot download: `02_scripts/.../eia_ng_waha_download.py` (legacy
  `src/extraction/eia_ng_waha_download.py`).
- Feeds [[natural-gas-prices]] analysis (legacy notebooks `07_ng_price_correlation`,
  `07.1_ng_rtm_price_correlation`).

## Related
- [[natural-gas-prices]] · [[waha-hub]]
