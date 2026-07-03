---
title: Feature Engineering
type: concept
tags: [methods, features]
status: developing
sources: 1
updated: 2026-06-30
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

## Related
- [[load-and-demand]] · [[weather-hdd-cdd]] · [[wind-power-production]] · [[price-volatility]]

## Sources
- [[sources/2026-07-01_research-meeting]]
