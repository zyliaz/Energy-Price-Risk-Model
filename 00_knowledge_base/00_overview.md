---
title: Overview & Thesis — Drivers of ERCOT Price Volatility
type: overview
tags: [ercot, price-volatility, thesis]
status: developing
updated: 2026-07-03
---

# Drivers of ERCOT Price Volatility

## Research question
What drives wholesale electricity **price volatility** in ERCOT? The goal is to
decompose volatility in real-time (RTM) and day-ahead (DAM) prices into contributions
from:

- **Load / demand** — total and net load, including increasingly variable
  **[[data-center-demand]]**.
- **Renewable supply** — **[[wind-power-production]]** (and solar) and its forecast error.
- **Fuel** — **[[natural-gas-prices]]** (Waha hub) as the marginal-cost setter.
- **Weather** — **[[weather-hdd-cdd]]** as an upstream driver of load.
- **Scarcity mechanisms** — **[[ordc-price-adders]]**, which inject large, nonlinear
  price spikes under tight reserves.

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
extreme events (Feb 2021 Uri), so tail risk is concentrated in scarcity/extreme conditions.

> ⚠️ Starting hypothesis, not a conclusion. Update as `03_notebooks/02_analysis` produces
> results, and log every revision.

> ✅ Resolved 2026-07-03: both halves of the "adder activation rises sharply in top price
> quantiles" evidence are now reproducible. [[notebook-catalog|02_price_adder_activation]]
> (pre-2025) had a deleted/broken data-load chain, fixed and re-verified by fresh execution;
> [[notebook-catalog|03_new_pa_activation]] (post-2025) was already clean. The Uri
> natural-gas-correlation caveat is likewise resolved — see [[natural-gas-prices]].
> ⚠️ **Regime break Dec 2025:** ORDC adders → co-optimized [[rtc-b-asdc|RTC+B/ASDC]].
> Analyze pre/post-Dec-2025 as separate regimes (price formation + data schema both change).

## Direction (2026-07-01 advisor meeting)
- **Stats model first**, aimed at **scenario identification**.
- Preferred modeling target is **net load = load − wind − solar** (add a renewable-generation
  pipeline), not raw load. See [[feature-engineering]], [[wind-power-production]].
- Seasonal structure matters: `log(price)` vs load correlates more strongly in **summer**
  (use monthly slices). See [[load-and-demand]].
- **Deliverable:** academic paper / white paper + conference poster + git repo.
- Source: [[sources/2026-07-01_research-meeting]].

## Scope
ERCOT-only. Earlier framing compared ERCOT (energy-only) to PJM (capacity market); that
comparison is now background context, not a primary axis. See the [[scope-and-history]]
note for why the topic narrowed.

## How the analysis is structured
- **Cleaning** → `03_notebooks/00_cleaning` (price, load, WPP, price-adder parsing).
- **EDA** → `03_notebooks/01_eda` (price, load, WPP, NG correlation, HDD).
- **Analysis** → `03_notebooks/02_analysis` (adder activation, load–price correlation).

## Open questions
- What share of RTM price variance is attributable to ORDC adders vs. fundamentals?
- How does wind forecast error translate into price spikes?
- Are price-adder dynamics changing post-2025 (new PA regime)?
- Does data-center load growth measurably raise baseline volatility yet?
- Does **net load** (load − wind − solar) model price better than raw load? (2026-07-01)
- Why does load-forecast **over-prediction coincide with high prices**? (seems backwards)
- How much stronger is the load–price relationship in **summer** vs other seasons?

## Related
- [[price-volatility]] · [[ordc-price-adders]] · [[rtc-b-asdc]] · [[lmp-spp]] · [[rtm-dam]]
- [[wind-power-production]] · [[natural-gas-prices]] · [[load-and-demand]] · [[energy-only-market]]
- [[ancillary-services]] · [[feature-engineering]]

## Sources
- [[sources/2026-06-30_ercot-market-concepts]] · [[sources/2026-06-30_data-and-eda-notes]]
