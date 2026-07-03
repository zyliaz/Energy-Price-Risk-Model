---
title: Feature Engineering
type: concept
tags: [methods, features]
status: developing
sources: 1
updated: 2026-07-03
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
| **Net load** | load − (wind + solar) | **Preferred modeling target (2026-07-01)** — expected to model price better than raw load. Needs a solar+wind pipeline. |

## Open / to-add
- Price-volatility target definition (see [[price-volatility]]) — rolling std, spike flags.
- Region/zone aggregation using mappings in [[load-zones]].
- **Alt-forecast-model ensemble (2026-07-03):** 7 alt MTLF models (A3/A6/E/E1/E2/E3/M) now
  available per zone as load-prediction features — see [[mid-term-load-forecast]]. EDA'd in
  `09_mtlf_models_eda` → reduced to a single ERCOT-only ensemble-mean feature,
  `model_ensemble_features_ERCOT_*.csv` (per-model error and ensemble std/error dropped
  entirely per human instruction, deferred until needed). Not yet used downstream in any
  `02_analysis` notebook — candidate: ensemble mean vs ERCOT's own "Selected" as a
  forecast-disagreement signal (uncertainty/std feature would need to be reintroduced first).

## Related
- [[load-and-demand]] · [[weather-hdd-cdd]] · [[wind-power-production]] · [[price-volatility]]

## Sources
- [[sources/2026-07-01_research-meeting]]
