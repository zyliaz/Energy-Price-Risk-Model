---
title: LMP / SPP Decomposition
type: concept
tags: [pricing, ercot, core]
status: developing
sources: 1
updated: 2026-06-30
---

# LMP / SPP Decomposition

How an ERCOT price is built up — the accounting identity behind all volatility work.

```
RTM price (SPP) = LMP + price adders (PA)          [pre-Dec-2025]
LMP             = system lambda (energy) + transmission congestion + losses
```

- **System lambda** — ERCOT-wide marginal energy cost, set by the next available unit's
  fuel type (gas, wind, nuclear). Driven by [[natural-gas-prices]].
- **Congestion** — locational; arises under transmission limits + high load. Drives
  spatial price spread (North vs West [[load-zones]]).
- **Losses** — locational.
- **Price adders (PA)** — added **system-wide** (not locational), from the
  [[ordc-price-adders|ORDC]]. Under [[rtc-b-asdc|RTC+B]] (Dec 2025+), PA is **no longer
  separate** — it is co-optimized into the LMP.
- **SPP** aggregates LMP over geography (resource node / load zone / trading hub); the
  aggregation differs by type. See [[load-zones]].

## Why the system-wide vs locational split matters
Because PA is system-wide but LMP is locational, **SPP can exceed LMP**, and PA can exceed
SPP even when local LMP is negative (e.g. regional wind pushing local LMP < 0). Open
hypothesis: validate the **PA > SPP / negative-LMP** cases by collecting nodal LMP data.

## Related
- [[ordc-price-adders]] · [[rtm-dam]] · [[load-zones]] · [[natural-gas-prices]] · [[rtc-b-asdc]]
