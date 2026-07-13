---
title: MTLF over-predicts load exactly when load and price are high
type: analysis
tags: [ercot, forecast, load, puzzle]
status: developing
notebook: 03_notebooks/02_analysis/00_load_forecast_rtm_correlation_wip.ipynb
date: 2026-07-03
updated: 2026-07-05
---

# MTLF over-predicts load exactly when load and price are high

**Question asked:** Does load-forecast error explain RTM price spikes?

**Method / data used:**
`03_notebooks/02_analysis/00_load_forecast_rtm_correlation_wip.ipynb` — MTLF
actual/forecast/error merged with RTM price (`Hourly ERCOT system load and prediction.csv`
+ `rtm_price_aggregated.csv`).

**Answer / finding:**
- Forecast error **alone shows no strong correlation** with price.
- At **high load + high price**, MTLF tends to **over-predict** load
  (predicted > actual) — the opposite of what an under-forecasting-drives-scarcity
  account would produce.

**Citations:** [[mid-term-load-forecast]], [[load-and-demand]],
[[sources/2026-07-03_analysis-summary]],
`03_notebooks/02_analysis/00_load_forecast_rtm_correlation_wip.ipynb`.

## Related
- [[mid-term-load-forecast]]
- [[load-price-correlation-is-seasonal]]
