---
title: Empirical Findings Summary (as of 2026-07-03)
type: analysis
tags: [ercot, price-volatility, eda, summary]
status: developing
date: 2026-07-03
updated: 2026-07-03
---

# Empirical Findings Summary (as of 2026-07-03)

**Question asked:** What has the EDA/analysis notebook work shown so far across the five
driver clusters (NG prices, price adders, load+forecast error, weather)?

**Method / data used:** `03_notebooks/01_eda` (NG correlation, load, WPP, HDD) and
`03_notebooks/02_analysis` (price-adder activation, load–price correlation), summarized by
the human in [[sources/2026-07-03_analysis-summary]].

**Answer / finding:**
- **Natural gas:** TX power-producer, TX citygate, and Henry Hub prices are strongly
  correlated monthly except for two deviation events — **2021-02 (Uri)** and **2023-08**.
  See [[natural-gas-prices]].
- **Price adders (pre-Dec-2025):** activation by RTM price quantile steepens sharply at
  higher quantiles; RTRDP's tail is the one exception (non-monotonic). Post-Dec-2025
  RTC+B/ASDC fields show the same activation/distribution pattern. See
  [[ordc-price-adders]], [[rtc-b-asdc]].
- **Load & forecast error:** `log(price)` vs load correlates more strongly in months
  1–2 and 5–10 than the rest of the year (refines the earlier pooled "summer" claim to
  specific months). Forecast error alone still shows no strong correlation with price.
  Net-load (load − wind − solar) is suggested as a cleaner target for isolating the
  gas-price effect. See [[load-and-demand]].
- **MTLF puzzle sharpened:** at high load + high price, MTLF tends to **over-predict**
  load (predicted > actual) — counter-intuitive if scarcity were driven by
  under-forecasting. Open hypothesis: this depends on whether the mid-term forecast used
  for scheduling is set *before* the day-ahead market clears, in which case generation
  should be able to keep up and prices shouldn't spike — needs the MTLF-vs-DAM timing
  question resolved. See [[mid-term-load-forecast]].
- **Weather:** Texas load ≈ population × (AC + heating); temp-vs-load is U-shaped, and the
  cooling (CDD) side of the curve has risen **~50% from 2021 to 2022**, tracking population
  growth. See [[weather-hdd-cdd]].

**Citations:** [[sources/2026-07-03_analysis-summary]], [[natural-gas-prices]],
[[ordc-price-adders]], [[rtc-b-asdc]], [[load-and-demand]], [[mid-term-load-forecast]],
[[weather-hdd-cdd]], `03_notebooks/01_eda`, `03_notebooks/02_analysis`.

**Follow-ups:**
- What happened in **2023-08** that broke the NG-price correlation? (no ERCOT-specific
  event currently logged in the wiki — needs a source.)
- Resolve MTLF-vs-DAM timing to explain the over-prediction-at-high-price pattern.
- Build the solar/wind pipeline so load-minus-renewables can be tested against gas prices
  directly (tracked as an open action item from [[sources/2026-07-01_research-meeting]]).
