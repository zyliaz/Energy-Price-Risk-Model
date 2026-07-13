---
title: Mid-Term Load Forecast
type: concept
tags: [demand, forecast, ercot]
status: developing
sources: 4
updated: 2026-07-10
---

# Mid-Term Load Forecast (MTLF)

ERCOT's mid-term load forecast and its error vs actual [[load-and-demand]]. Forecast
error is a volatility channel: under-forecast load → unexpected tightness → price spikes.

## Data coverage
Hourly, by weather zone. Forecast **error** available 2022–2025; 2021 long-term prediction;
2020 limited. Drives the **adder demand** feature (forecast − actual). See [[feature-engineering]].

**Alt forecast models (2026-07-03):** the raw MTLF xlsx sheets carry 7 additional model
columns beyond "Selected" (ERCOT's chosen forecast) — `A3, A6, E, E1, E2, E3, M`. **Model
headings (2026-07-07):** each is a distinct ERCOT load-prediction model built on a different
set of input weather forecasts; see ERCOT's [Board Education — Load Forecasting slides](https://www.ercot.com/files/docs/2024/06/11/7%20Board%20Education%20%E2%80%93%20Load%20Forecasting.pdf)
(the "E-" models are documented there). See [[sources/2026-07-07_research-update]]. Parsed by
a new script, [[extraction-scripts|parse_mid_term_load_forecast_models_parquet]], into
`01_data/1.2_raw_api/mid_term_load_forecast_models_20220201_20251201.parquet` (33,676 rows ×
82 cols: `datetime` + `{actual,selected,a3,a6,e,e1,e2,e3,m}_{zone}` for 9 zones). Built for
load-prediction feature/ensemble work, not the error diagnostic — no `Error` column here (see
base parser above for that). Known artifact: ~103 timestamps have a duplicate row where the
`ERCOT`-sheet total is populated but zone columns are NaN (or vice versa) — an intra-file
sheet-length mismatch inherited from the same outer-merge pattern as the base parser, not a
new bug. 76 nulls in one zone/month pairing (SCent, North) from a real source-data gap.

EDA'd in [[notebook-catalog|09_mtlf_models_eda]]: exports an ERCOT-total-only hourly table
(actual + selected + all 7 alt models, `Hourly_ERCOT_all_models_*.csv`). No derived
ensemble/error feature is currently computed — an ensemble-mean feature and a zone-sum-vs-
ERCOT-total validation finding existed briefly (2026-07-03–07-08) but were removed in an
uncommitted 2026-07-09 edit; see [[notebook-catalog]] drift note.

**Planned: short-horizon forecast product (2026-07-07).** ERCOT's live **Seven-Day Load
Forecast by Model and Weather Zone (NP3-565-CD)** publishes hourly per-model predictions from
the current day out 7 days, one report per hour. Decision: extract the 3-hour, 6-hour, and
day-ahead predictions specifically and recreate the forecast-error-vs-actual-load scatter at
those horizons (mirrors the existing MTLF-error work but at shorter, fixed lead times). Not
yet built — tracked as a Notion to-do ("real time load prediction 3, 6 hours + day ahead
pipeline"). See [[sources/2026-07-07_research-update]], [[ercot-data-products]].

## Findings
- **log(price) vs load prediction error: no strong correlation** — forecast error alone is
  a weak spike predictor. See [[load-and-demand]].
- **Over-prediction at high prices (2026-07-01):** forecast **over-prediction coincides
  with high prices** — the opposite of what an under-forecasting-drives-scarcity account
  would produce. See [[sources/2026-07-01_research-meeting]].
- **Sharpened (2026-07-03):** the over-prediction is concentrated at **high load + high
  price** hours specifically (predicted > actual).
  See [[analysis/mtlf-overpredicts-at-high-load-price]].

## Related
- [[load-and-demand]] · [[price-volatility]] · [[feature-engineering]] · [[rtm-dam]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-07-01_research-meeting]] ·
  [[sources/2026-07-03_analysis-summary]] · [[sources/2026-07-07_research-update]]
