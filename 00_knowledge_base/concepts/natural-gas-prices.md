---
title: Natural Gas Prices
type: concept
tags: [fuel, marginal-cost, ercot]
status: developing
sources: 0
updated: 2026-06-30
---

# Natural Gas Prices

Gas is frequently the marginal generator in ERCOT, so gas spot prices — especially at the
**[[waha-hub]]** — set the floor for power prices and are a fundamental (vs scarcity)
driver of [[price-volatility]].

## Series used ([[eia]])
- **Henry Hub** — hourly (`rngwhhdd`); national benchmark, used as "insurance" vs RTM.
- **TX Citygate (S. TX)** — monthly (`ng_pri_sum_dcu_stx_m`).
- **TX Electric Power Price** — monthly (same EIA page).
- **[[waha-hub|Waha]]** — West Texas hub. ⚠️ Old `eia_ng_waha_download.py` **removed**
  (legacy, out of scope); a Henry Hub / citygate scraper is a to-build item. See [[extraction-scripts]].

## Findings
- TX power-producer, citygate, and Henry Hub prices are **strongly correlated monthly
  except for extreme deviations** — most notably **Feb 2021 (Winter Storm Uri)**, which
  is itself a major source of ERCOT risk and volatility.
- Legacy: `07_ng_price_correlation`, `07.1_ng_rtm_price_correlation`.

## Notes
- Separate *fuel-cost* volatility (gas-driven) from *scarcity* volatility (adder-driven)
  when attributing price variance.

## Related
- [[waha-hub]] · [[eia]] · [[price-volatility]] · [[lmp-spp]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-06-30_ercot-market-concepts]]
