---
title: Analysis Summary As of Today
type: source
tags: [meeting, analysis, empirical-findings]
status: developing
date_ingested: 2026-07-03
source_kind: note
raw_path: Notion — Meeting Notes & Insights ("Analysis Summary As of Today", 2026-07-03)
updated: 2026-07-03
---

# Analysis Summary As of Today — 2026-07-03

Self-authored progress note (not an advisor meeting) recapping EDA/analysis results
produced so far. Synced from the Notion Meeting Notes DB (`Related Area: analysis`).

## Notes
Five result clusters, roughly one per notebook group:

1. **Natural gas price (monthly resampled).** TX power-producer, TX citygate, and Henry
   Hub prices scatter tightly against each other **except for extreme deviations** —
   most notably **2021-02 (Winter Storm Uri)** and **2023-08**. Flags a new deviation
   month not previously logged. See [[natural-gas-prices]].
2. **Price adder — pre-Dec-2025 schema.** Activation (Boolean) by RTM price quantile is
   smoothed but steepens sharply at higher quantiles; top-5-percentile tails increase for
   most adders except **RTRDP**, which is non-monotonic. Value distributions (log scale)
   skew toward fewer counts in larger bins, with RTRDP's right tail tilted by Uri. Matches
   prior findings. See [[ordc-price-adders]].
3. **Price adder — post-Dec-2025 schema.** Same activation/distribution charts run on the
   new RTC+B/ASDC fields; no new deviation flagged here. See [[rtc-b-asdc]].
4. **Load + prediction error vs RTM price.** `log(price)` vs actual load, faceted by
   month, correlates more strongly in **months 1–2 and 5–10** (Jan–Feb, May–Oct) than the
   remaining months — a refinement of the prior "stronger in summer" framing. `log(price)`
   vs load-forecast-error shows no strong correlation (confirms prior finding). Suggests
   **subtracting solar/wind from load** so the residual is better explained by gas prices.
   Separately: prediction error vs load (color-coded by `log(price)`) shows **higher
   load+price hours generally over-predict load** (predicted > actual) — raises a question
   about whether MTLF timing relative to the day-ahead market allows generation to keep up.
   See [[load-and-demand]], [[mid-term-load-forecast]].
5. **HDD+CDD vs load vs price.** Texas load ≈ population × (AC + heating); population growth
   is a first-order load driver. HDD/CDD vs load shows a strong correlation for nonzero
   points, rising year over year with population. Temp vs load is **U-shaped**; load has
   risen substantially over the past 5 years, with the cooling (CDD) side of the curve up
   **~50% from 2021 to 2022**. See [[weather-hdd-cdd]].

## Insights
See per-topic notes above; filed as one finding-named note per notebook under `analysis/`.

## Action items
None — the note contains an instruction to file these results in the wiki (executed via
this source page + the concept-page and analysis-page updates below), not a task-tracker
action item. Nothing mirrored to Notion To-dos.

## Why it matters to the thesis
Adds one new tail-risk data point to the NG-correlation finding (2023-08), refines the
"summer" seasonality claim to specific months, and sharpens the MTLF over-prediction puzzle
with a directional pattern (over-prediction concentrated at high load+price). Population
growth is now named explicitly as the structural driver behind rising CDD-side load.

## Affected wiki pages
[[natural-gas-prices]], [[ordc-price-adders]], [[load-and-demand]],
[[mid-term-load-forecast]], [[weather-hdd-cdd]],
[[analysis/ng-hub-correlation-breaks-uri-aug2023]], [[analysis/adder-activation-steepens-with-price]], [[analysis/rtcb-activation-mirrors-ordc]], [[analysis/load-price-correlation-is-seasonal]], [[analysis/mtlf-overpredicts-at-high-load-price]], [[analysis/cooling-demand-rising-with-population]]
