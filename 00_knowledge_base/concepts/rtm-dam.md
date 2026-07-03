---
title: RTM & DAM
type: concept
tags: [market, pricing, ercot]
status: developing
sources: 0
updated: 2026-06-30
---

# RTM & DAM (Real-Time and Day-Ahead Markets)

ERCOT's two settlement markets.

- **DAM (Day-Ahead Market):** financially-binding hourly prices cleared the day before.
- **RTM (Real-Time Market):** physical balancing via **SCED** (~5-min dispatch),
  settled on 15-min intervals. Where scarcity [[ordc-price-adders]] show up most sharply.

## Prices
- **LMP** — Locational Marginal Price at nodes; **SPP** = LMP aggregated by geography.
  Decomposition (`SPP = LMP + adders`) in [[lmp-spp]]. Most analysis uses SPP by load zone.

## DAM mechanics
Buyers purchase ~**80–90%** of next-day need in DAM for price certainty; the remainder is
exposed to RTM (could be 0% — pure RT-market risk). RTM–DAM spread is itself a volatility
signal.

## Use in this project
- **Data:** DAM = report **13060**, RTM = report **13061** (SPP by load zone). Superseded
  nodal pulls used NP6-788-CD — see [[ercot-data-products]].
- ⚠️ **Gap:** the new repo has no RTM-vs-DAM comparison notebook (old `04_rtm_dam_price_eda`
  was dropped in migration, not renamed) — rebuild if that comparison is needed.

## Related
- [[price-volatility]] · [[lmp-spp]] · [[ordc-price-adders]] · [[load-zones]] · [[ercot]]

## Sources
- [[sources/2026-06-30_ercot-market-concepts]] · [[sources/2026-06-30_data-and-eda-notes]]
