---
title: Overview & Thesis — Drivers of ERCOT Price Volatility
type: overview
tags: [ercot, price-volatility, thesis]
status: developing
updated: 2026-07-17
---

# Drivers of ERCOT Price Volatility

## Research question
What drives wholesale electricity **price volatility** in ERCOT? The goal is to
decompose volatility in real-time (RTM) and day-ahead (DAM) prices into contributions from:

- **Load / demand** — total and net load.
- **Renewable supply** — **[[wind-power-production]]** (and solar) and its forecast error.
- **Fuel** — **[[natural-gas-prices]]** as the marginal-cost setter.
- **Weather** — **[[weather-hdd-cdd]]** as an upstream driver of load.
- **Scarcity mechanisms** — **[[ordc-price-adders]]**, which inject large, nonlinear price spikes under tight reserves.

## Working thesis (evolving — v1.1, 2026-06-30)
ERCOT's **[[energy-only-market]]** design concentrates fixed-cost recovery into a small
number of high-price scarcity hours. As a result, ERCOT price volatility is dominated
less by smooth fuel/load variation and more by **discrete scarcity-adder activations** that
fire when operating reserves fall — conditions made more frequent by high net-load ramps
(wind drop-offs + demand peaks). The empirical work tests how much of observed RTM price
variance is explained by adders vs. underlying load/wind/gas fundamentals.

Early evidence consistent with this: **log(price) vs load-forecast-error shows no strong
correlation** (fundamentals alone don't explain spikes), while **adder activation rises
sharply in the top price quantiles**. Natural-gas series correlate tightly *except* during
extreme events (Feb 2021 Uri, and a second flagged deviation in Aug 2023), so tail risk is
concentrated in scarcity/extreme conditions. See [[natural-gas-prices]].

> ⚠️ Starting hypothesis, not a conclusion. Update as `03_notebooks/02_analysis` produces
> results, and log every revision.

> ✅ Resolved 2026-07-03: both halves of the "adder activation rises sharply in top price
> quantiles" evidence are now reproducible. [[notebook-catalog|02_price_adder_activation]]
> (pre-2025) had a deleted/broken data-load chain, fixed and re-verified by fresh execution;
> [[notebook-catalog|03_new_pa_activation]] (post-2025) was already clean. The Uri
> natural-gas-correlation caveat is likewise resolved — see [[natural-gas-prices]].
> ⚠️ **Regime break Dec 2025:** ORDC adders → co-optimized [[rtc-b-asdc|RTC+B/ASDC]].
> Analyze pre/post-Dec-2025 as separate regimes (price formation + data schema both change).

**New quantitative support (2026-07-14):** a "spare capacity" metric —
`(load − renewable_gen) / non_re_capacity`, i.e. how hard load is squeezing non-renewable
firm capacity net of renewables — correlates strongly with `log(price)` (Uri excluded) and,
combined with natural-gas price and degree-days in an OLS regression, explains a majority of
RTM price variance (R²=0.552; spare-capacity and NG-price coefficients both significant,
p<0.001). This is the most direct evidence so far that tightening capacity margins, not
smooth fundamentals, drive price levels — see
[[analysis/spare-capacity-correlates-with-rtm-price]], [[feature-engineering]]. The
regression itself (`03_notebooks/03_model/01_regression.ipynb`) was edited 2026-07-17 to
remove its modeling cells (now a dataset-export step only, pending the next modeling pass) —
treat the R² and coefficients as historical/provisional, not currently reproducible from the
notebook as saved. See [[notebook-catalog]].

## Direction (2026-07-01 advisor meeting)
- **Stats model first**, aimed at **scenario identification**.
- Preferred modeling target is **net load = load − wind − solar**, not raw load. A combined
  wind+solar generation series now exists (2026-07-10) but no notebook has computed net load
  from it yet. See [[feature-engineering]], [[wind-power-production]].
- Seasonal structure matters: `log(price)` vs load correlates more strongly in **summer**
  (use monthly slices). See [[load-and-demand]]. Refined 2026-07-03: strongest specifically
  in **months 1–2 and 5–10**, not a clean summer/winter split.
- **Deliverable:** academic paper / white paper + conference poster + git repo.
- Source: [[sources/2026-07-01_research-meeting]].

## Scope
ERCOT-only. Earlier framing compared ERCOT (energy-only) to PJM (capacity market); that
comparison is now background context, not a primary axis. See the [[scope-and-history]]
note for why the topic narrowed.

## How the analysis is structured
- **Pre-scraper checks** → `03_notebooks/00_check` (endpoint/schema review before building an extractor).
- **Cleaning + EDA** → `03_notebooks/01_eda` (single-source: price, load, WPP, NG correlation, HDD).
- **Analysis** → `03_notebooks/02_analysis` (multi-source: adder activation, load–price correlation, spare-capacity metric).
- **Modeling** → `03_notebooks/03_model` (added 2026-07-14, adopted into CLAUDE.md §2
  2026-07-17: statistical/ML modeling on top of `02_analysis` outputs, e.g. regressing RTM
  price on the spare-capacity metric).

## Related
- [[price-volatility]] · [[ordc-price-adders]] · [[rtc-b-asdc]] · [[lmp-spp]] · [[rtm-dam]]
- [[wind-power-production]] · [[natural-gas-prices]] · [[load-and-demand]] · [[energy-only-market]]
- [[ancillary-services]] · [[feature-engineering]]

## Sources
- [[sources/2026-06-30_ercot-market-concepts]] · [[sources/2026-06-30_data-and-eda-notes]] ·
  [[sources/2026-07-03_analysis-summary]] · [[sources/2026-07-13_weekly-meeting-spare-capacity]] ·
  [[sources/2026-07-14_capacity-model-research-update]]
