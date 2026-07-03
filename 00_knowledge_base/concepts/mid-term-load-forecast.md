---
title: Mid-Term Load Forecast
type: concept
tags: [demand, forecast, ercot]
status: stub
sources: 1
updated: 2026-07-03
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
- ⚠️ **Puzzle (2026-07-01):** forecast **over-prediction coincides with high prices**, which
  is counter-intuitive (over-forecast should imply slack, not scarcity). Flagged to
  investigate. See [[sources/2026-07-01_research-meeting]].
- **Sharpened (2026-07-03):** the over-prediction is concentrated at **high load + high
  price** hours specifically (predicted > actual). Open hypothesis: depends on whether MTLF
  is finalized **before** the day-ahead market clears — if so, generation should be able to
  keep up and prices shouldn't spike, so the MTLF-vs-DAM timing needs to be checked against
  ERCOT's forecast schema. See [[analysis/2026-07-03_empirical-findings-summary]].

## Related
- [[load-and-demand]] · [[price-volatility]] · [[feature-engineering]] · [[rtm-dam]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-07-01_research-meeting]] ·
  [[sources/2026-07-03_analysis-summary]]
