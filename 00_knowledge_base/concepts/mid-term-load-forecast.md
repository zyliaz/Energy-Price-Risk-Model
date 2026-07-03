---
title: Mid-Term Load Forecast
type: concept
tags: [demand, forecast, ercot]
status: developing
sources: 1
updated: 2026-07-03
---

# Mid-Term Load Forecast (MTLF)

ERCOT's mid-term load forecast and its error vs actual [[load-and-demand]]. Forecast
error is a volatility channel: under-forecast load → unexpected tightness → price spikes.

## Data coverage
Hourly, by weather zone. Forecast **error** available 2022–2025; 2021 long-term prediction;
2020 limited. Drives the **adder demand** feature (forecast − actual). See [[feature-engineering]].

**Alt forecast models (2026-07-03):** the raw MTLF xlsx sheets carry 7 additional model
columns beyond "Selected" (ERCOT's chosen forecast) — `A3, A6, E, E1, E2, E3, M`. Parsed by
a new script, [[extraction-scripts|parse_mid_term_load_forecast_models_parquet]], into
`01_data/1.2_raw_api/mid_term_load_forecast_models_20220201_20251201.parquet` (33,676 rows ×
82 cols: `datetime` + `{actual,selected,a3,a6,e,e1,e2,e3,m}_{zone}` for 9 zones). Built for
load-prediction feature/ensemble work, not the error diagnostic — no `Error` column here (see
base parser above for that). Known artifact: ~103 timestamps have a duplicate row where the
`ERCOT`-sheet total is populated but zone columns are NaN (or vice versa) — an intra-file
sheet-length mismatch inherited from the same outer-merge pattern as the base parser, not a
new bug. 76 nulls in one zone/month pairing (SCent, North) from a real source-data gap.

EDA'd in [[notebook-catalog|09_mtlf_models_eda]]: per-model error vs actual (all 7 alt
models x 9 zones), plus derived **ensemble mean/std/error** per zone (mean and spread of the
7 alt models, excluding ERCOT's own `Selected`). Finding: the ensemble mean's zone-sum-vs-
ERCOT-total validation diff (mean ~359 MW) is larger than `Selected`'s (mean ~253 MW) — each
zone's alt models are independently fit, so summing them is less additively consistent than
ERCOT's own system-level `Selected` forecast. ~0.5-1% of system load either way.

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
