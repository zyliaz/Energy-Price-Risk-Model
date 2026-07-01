---
title: Load & Demand
type: concept
tags: [demand, ercot]
status: developing
sources: 0
updated: 2026-06-30
---

# Load & Demand

Electricity demand in ERCOT — total system load and load by forecast zone (FZN). The
primary fundamental pressure on prices; peaks and **net-load ramps** (load minus
[[wind-power-production]]) drive reserve scarcity and [[ordc-price-adders]].

## Data
- **Actual load by forecast zone:** `NP6-346-CD` archive (2021–Nov 2023) + live API
  (Dec 2023–present). Legacy `02_ercot_load_eda`, `ercot_load_by_fzn.py`, `ercot_load_archive.py`.

## Threads
- **Mid-term load forecast** and forecast error: [[mid-term-load-forecast]].
- **Adder demand** = load forecast − actual load (from 2021). See [[feature-engineering]].
- **Data-center growth** as a new, less weather-correlated demand source:
  [[data-center-demand]].
- Load × RTM price relationship: legacy `10.0_load_rtm_price_plot`.

## Findings
- Time-series of load and RTM price tracked together; **price vs actual-load** scatter.
- **log(price) vs load prediction error shows no strong correlation** — forecast error
  alone is a weak predictor of price spikes (motivates the adder-centric thesis). See
  [[mid-term-load-forecast]].

## Related
- [[mid-term-load-forecast]] · [[data-center-demand]] · [[weather-hdd-cdd]] · [[price-volatility]] · [[feature-engineering]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]]
