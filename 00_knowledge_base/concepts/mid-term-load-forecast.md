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
- ⚠️ **Puzzle (2026-07-01):** forecast **over-prediction coincides with high prices**, which
  is counter-intuitive (over-forecast should imply slack, not scarcity). Flagged to
  investigate. See [[sources/2026-07-01_research-meeting]].

## Related
- [[load-and-demand]] · [[price-volatility]] · [[feature-engineering]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-07-01_research-meeting]]
