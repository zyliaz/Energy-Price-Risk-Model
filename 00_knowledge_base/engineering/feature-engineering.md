---
title: Feature Engineering
type: engineering
tags: [methods, features]
status: developing
sources: 1
updated: 2026-07-10
---

# Feature Engineering

Derived variables used in the volatility analysis. Keep definitions here so notebooks stay
consistent.

| Feature | Definition | Notes |
|---|---|---|
| **Adder demand** | load forecast − actual load | Available from 2021. Proxy for unexpected tightness. See [[mid-term-load-forecast]]. |
| **CDD** | actual temp − 65°F (cooling threshold) | Dominant in Texas (cooling load). See [[weather-hdd-cdd]]. |
| **HDD** | 65°F − actual temp (heating threshold) | Smaller in TX; rising as heating electrifies. |
| **Capacity factor (C.F.)** | wind/solar production ÷ capacity | From production series. See [[wind-power-production]]. |
| **Net load** | load − (wind + solar) | **Preferred modeling target (2026-07-01)** — expected to model price better than raw load. Combined wind+solar series now exists ([[ercot-data-products]]) but no notebook has computed net load from it yet. |

## Open / to-add
- Price-volatility target definition (see [[price-volatility]]) — rolling std, spike flags.
- Region/zone aggregation using mappings in [[load-zones]].
- **Alt-forecast-model columns (2026-07-03):** 7 alt MTLF models (A3/A6/E/E1/E2/E3/M) parsed
  per zone as raw load-prediction columns — see [[mid-term-load-forecast]]. EDA'd in
  `09_mtlf_models_eda`, exported ERCOT-only as `Hourly_ERCOT_all_models_*.csv` (actual +
  selected + all 7 models, no derived feature). An ensemble-mean feature was computed briefly
  (2026-07-03–07-08) then removed in an uncommitted 2026-07-09 edit — see [[notebook-catalog]]
  drift note. Not currently used downstream in any `02_analysis` notebook.
- **Load-vs-firm-capacity ratio (in development, 2026-07-10):** `(load − renewable_gen) /
  non_re_capacity`, proposed in [[sources/2026-07-06_weekly-meeting]] as a stakeholder price-
  incentive metric. Computed in `06_metric_nonvariable_load_capacity` — the ratio cell itself
  runs clean; the notebook is not yet stable end-to-end (see [[notebook-catalog]]). No finding
  filed yet — WIP. ⚠️ Caveat (2026-07-07): `non_re_capacity` covers gas-CC + gas-other only —
  coal/nuclear/diesel (~25% of thermal capacity) are excluded, so the ratio undercounts total
  firm capacity. See [[sources/2026-07-07_research-update]].

## Related
- [[load-and-demand]] · [[weather-hdd-cdd]] · [[wind-power-production]] · [[price-volatility]]

## Sources
- [[sources/2026-07-01_research-meeting]] · [[sources/2026-07-07_research-update]]
