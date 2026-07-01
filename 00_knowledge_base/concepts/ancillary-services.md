---
title: Ancillary Services
type: concept
tags: [reserves, ercot, pricing]
status: developing
sources: 1
updated: 2026-06-30
---

# Ancillary Services

Reserve products ERCOT procures to maintain reliability. Under [[rtc-b-asdc|RTC+B]] (Dec
2025+) their demand curves (ASDCs) carry the scarcity value that ORDC adders used to add
to energy prices, so they are now central to [[price-volatility]].

## Products (Modo Energy explainer)
| Service | Purpose | Response | Procurement (approx.) |
|---|---|---|---|
| Reg-Up / Reg-Down | Continuously correct minor frequency deviations | ~5 s, pre-fault | ~190–880 MW |
| RRS (Responsive Reserve) | Arrest frequency deviations (PFR/UFR/FFR sub-types) | 0.25 s–1 min, post-fault | ~2,300–3,200 MW |
| ECRS (ERCOT Contingency Reserve) | Significant deviations / ramp coverage | ~10 min | ~900–3,000 MW |
| Non-Spin | Extra dispatchable capacity when RT reserves low | ~30 min, manual | ~1,900–3,400 MW |

## Ordering under ASDC
Reserve products fill capacity in order; **Non-Spin and ECRS are exhausted before Reg-Up
and RRS**. The ASDC shape derives from the ORDC. See [[rtc-b-asdc]].

## Related
- [[rtc-b-asdc]] · [[ordc-price-adders]] · [[price-volatility]]
