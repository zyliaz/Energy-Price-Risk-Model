---
title: Overview & Thesis — Drivers of ERCOT Price Volatility
type: overview
tags: [ercot, price-volatility, thesis, simulation]
status: developing
updated: 2026-07-24
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
- **Resource outages** — planned and forced generation outages (**NP3-233-CD**); a direct,
  hourly measure of supply unavailability that tightens effective spare capacity. See
  [[ercot-data-products]].

**Extended goal (2026-07-20, [[sources/2026-07-20_meeting-notes]]):** once the decomposition
model is fit, use it for **scenario simulation** — evaluating hypothetical futures (e.g.
sustained high natural-gas prices, shrinking spare thermal capacity, more frequent heat waves;
see [[sources/2026-07-14_capacity-model-research-update]]). This reframes `CLAUDE.md`'s
research-question line (working-tree edit as of 2026-07-24: "Model price with variables, then
simulate with artificial scenarios") as a restatement of the same goal, not a scope change —
decomposition is still the mechanism, simulation is the stated end use. Practically, this
means driver variables that are themselves correlated with each other (e.g. `degree_days` and
`spare_capacity`, both driven by load — see [[feature-engineering]]) need their effects
**isolated**, not just included additively, before the model can be used to hold one factor
fixed and vary another. Not yet implemented in the current regression (`mod1` in
`03_notebooks/03_model/ERCOT regression.Rmd`).

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
[[analysis/spare-capacity-correlates-with-rtm-price]], [[feature-engineering]].

> **⭐ Metric v2 (2026-09-17) — resolves Uri exclusion:** v1 excluded Winter Storm Uri
> because load curtailment broke the load→price pattern (load dropped while prices were at the
> $9,000 cap). Adding hourly **resource outage capacity** (NP3-233-CD) to the denominator
> fixes this: `spare_capacity_v2 = (load − renewable_gen) / (thermal_capacity − outage_MW)`.
> During Uri, ~half of generation was offline, so the denominator collapses even harder than
> load dropped — the metric spikes correctly, maintaining a consistent relationship with price
> across all periods including extreme events. This means the full 2021–present dataset can
> now be modeled without excluding Uri. See [[feature-engineering]]. That
R²=0.552 figure is from a Python OLS pass that predates a 2026-07-17 edit removing all
modeling cells from the notebook (now `01_regression_data.ipynb`, dataset-export only) —
treat it as historical/provisional. **Update (2026-07-21–24):** modeling moved to a companion
R script (`ERCOT regression.Rmd`, formula `rtm_price ~ spare_capacity + ng_price +
degree_days + factor(year) + factor(season) + time_of_day`) with two new predictors
(`time_of_day`) and an hourly (not daily) degree-days feed; **not independently run this
session** (no R runtime available), so its results aren't yet confirmed. ✅ **Fixed
2026-07-24:** the hourly degree-days feed (ERA5) is natively UTC-timestamped and was being
joined without timezone conversion against the Central-time RTM/load series. Fixed at the
point of use in `06_spare_capacity.ipynb`/`01_regression_data.ipynb` (convert to
`America/Chicago` right after loading, before the join) — the ERA5 scraper/cleaned files
stay UTC, unchanged, per the human's instruction not to re-touch already-scraped data.
Resulting correlations: `degree_days`↔`rtm_price` 0.184, `degree_days`↔`spare_capacity` 0.579.
The historical R²=0.552 figure predates both this fix and the `time_of_day` addition, so a
fresh model run (Python or R) is still needed for a current number. See [[weather-hdd-cdd]],
[[feature-engineering]], [[notebook-catalog]].

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
- [[ancillary-services]] · [[feature-engineering]] · [[weather-hdd-cdd]]

## Sources
- [[sources/2026-06-30_ercot-market-concepts]] · [[sources/2026-06-30_data-and-eda-notes]] ·
  [[sources/2026-07-03_analysis-summary]] · [[sources/2026-07-13_weekly-meeting-spare-capacity]] ·
  [[sources/2026-07-14_capacity-model-research-update]] · [[sources/2026-07-20_meeting-notes]]
