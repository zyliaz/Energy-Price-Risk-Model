---
title: Load & Demand
type: concept
tags: [demand, ercot]
status: developing
sources: 1
updated: 2026-07-03
---

# Load & Demand

Electricity demand in ERCOT — total system load and load by forecast zone (FZN). The
primary fundamental pressure on prices; peaks and **net-load ramps** (load minus
[[wind-power-production]]) drive reserve scarcity and [[ordc-price-adders]].

## Data
- **Actual load by forecast zone:** `NP6-346-CD` archive (2021–Nov 2023) + live API
  (Dec 2023–present).

## Threads
- **Mid-term load forecast** and forecast error: [[mid-term-load-forecast]].
- **Adder demand** = load forecast − actual load (from 2021). See [[feature-engineering]].
- **Data-center growth** as a new, less weather-correlated demand source:
  [[data-center-demand]].
## Findings
- Time-series of load and RTM price tracked together; **price vs actual-load** scatter.
- **log(price) vs load prediction error shows no strong correlation** — forecast error
  alone is a weak predictor of price spikes (motivates the adder-centric thesis). See
  [[mid-term-load-forecast]].
- **Seasonality (2026-07-01):** `log(price)` vs load is **stronger in summer months** — use
  monthly slices, not a pooled fit (`05_load_rtm_price_plot`).
- **Refined (2026-07-03):** faceting by month shows the correlation is actually stronger in
  **months 1–2 and 5–10** (Jan–Feb, May–Oct), not just summer — narrows the monthly-slice
  claim above. Suggests **subtracting solar/wind from load** so the residual is better
  explained by [[natural-gas-prices|gas prices]]. See
  [[analysis/2026-07-03_empirical-findings-summary]].
- **Total load is rising** over the study window (load vs temp, quadratic fit over years —
  see [[weather-hdd-cdd]]).
- **Net load** (load − wind − solar) is the preferred modeling target going forward — see
  [[feature-engineering]], [[wind-power-production]].

## Related
- [[mid-term-load-forecast]] · [[data-center-demand]] · [[weather-hdd-cdd]] · [[price-volatility]] · [[feature-engineering]] · [[wind-power-production]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-07-01_research-meeting]] ·
  [[sources/2026-07-03_analysis-summary]]
