---
title: Mid-Term Load Forecast
type: concept
tags: [demand, forecast, ercot]
status: stub
sources: 0
updated: 2026-06-30
---

# Mid-Term Load Forecast (MTLF)

ERCOT's mid-term load forecast and its error vs actual [[load-and-demand]]. Forecast
error is a volatility channel: under-forecast load → unexpected tightness → price spikes.

## Data coverage
Hourly, by weather zone. Forecast **error** available 2022–2025; 2021 long-term prediction;
2020 limited. Drives the **adder demand** feature (forecast − actual). See [[feature-engineering]].

## Findings
- **log(price) vs load prediction error: no strong correlation** — forecast error alone is
  a weak spike predictor. See [[load-and-demand]].

## Legacy work
- EDA: `06_mid_term_load_forecast_eda`.
- Forecast ↔ RTM correlation: `06.1_[IN PROCESS]_load_forecast_rtm_coorelation`.
- Parsing: `src/extraction/parse_mid_term_load_forecast_parquet.py`.

## Related
- [[load-and-demand]] · [[price-volatility]] · [[feature-engineering]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]]
