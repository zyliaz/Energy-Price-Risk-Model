---
title: Energy-Only Market
type: concept
tags: [market-design, ercot]
status: developing
sources: 0
updated: 2026-06-30
---

# Energy-Only Market

A market design (ERCOT's) where generators recover **all** costs — including fixed/capital
costs — through energy and ancillary-service revenues, with **no separate capacity
payments**. Resource adequacy relies on prices rising high enough during scarcity to
incentivize investment ("missing money" solved via scarcity rents).

## Implication for volatility
Because there is no capacity payment, fixed-cost recovery concentrates into a few
extreme-price scarcity hours, engineered largely through [[ordc-price-adders]]. This is
*why* ERCOT prices are structurally more volatile/spiky than capacity-market grids — the
central premise of this research. See [[00_overview]].

## Regime note (Dec 2025)
Under [[rtc-b-asdc|RTC+B]], scarcity rents shift from standalone ORDC energy adders to
co-optimized ancillary-service prices ([[ancillary-services]]). The energy-only *principle*
(scarcity funds fixed costs) is unchanged; the *mechanism* changes.

## Contrast (background only)
PJM uses a capacity market (RPM auctions) that pays for availability, smoothing energy-price
spikes. Retained here only as background; not a primary analysis axis.

## Related
- [[ordc-price-adders]] · [[price-volatility]] · [[ercot]] · [[puct]]
