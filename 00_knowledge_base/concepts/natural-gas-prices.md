---
title: Natural Gas Prices
type: concept
tags: [fuel, marginal-cost, ercot]
status: developing
sources: 1
updated: 2026-07-07
---

# Natural Gas Prices

Gas is frequently the marginal generator in ERCOT, so gas spot prices — tracked here via
**Henry Hub** and **TX Citygate** (see [[eia]]; the Waha hub scraper was descoped 2026-07-03,
see [[extraction-scripts]]) — set the floor for power prices and are a fundamental (vs
scarcity) driver of [[price-volatility]].

## Series used ([[eia]])
- **Henry Hub** — hourly (`rngwhhdd`); national benchmark, used as "insurance" vs RTM.
- **TX Citygate (S. TX)** — monthly (`ng_pri_sum_dcu_stx_m`).
- **TX Electric Power Price** — monthly (same EIA page).

## Findings
- TX power-producer, citygate, and Henry Hub prices are **strongly correlated monthly
  except for extreme deviations** — most notably **Feb 2021 (Winter Storm Uri)**, which
  is itself a major source of ERCOT risk and volatility.
- **(2026-07-03)** A second deviation month is now flagged: **2023-08**. No ERCOT-specific
  event is logged in the wiki explaining it yet. See
  [[analysis/ng-hub-correlation-breaks-uri-aug2023]].

> ✅ Resolved 2026-07-03: [[notebook-catalog|01_ng_rtm_price_correlation]]'s rename no-op
> (flagged here as a contradiction earlier the same day) was fixed by the human and re-verified
> by fresh execution — the Henry-Hub-vs-RTM-price finding above is reproducible again.

## Notes
- Separate *fuel-cost* volatility (gas-driven) from *scarcity* volatility (adder-driven)
  when attributing price variance.

## Related
- [[eia]] · [[price-volatility]] · [[lmp-spp]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-06-30_ercot-market-concepts]] ·
  [[sources/2026-07-03_analysis-summary]]
