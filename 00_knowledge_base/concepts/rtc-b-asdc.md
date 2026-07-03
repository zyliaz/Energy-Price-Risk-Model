---
title: RTC+B / ASDC (Dec 2025 regime)
type: concept
tags: [scarcity, pricing, regime-change, ercot, core]
status: developing
sources: 2
updated: 2026-06-30
---

# RTC+B / ASDC — the Dec 2025 regime change

A structural break in ERCOT pricing effective **December 2025**: **Real-Time
Co-optimization with Batteries (RTC+B)** replaces the standalone [[ordc-price-adders|ORDC]]
adder mechanism. This segments the price history into **pre-Dec-2025** and **post-Dec-2025**
periods that must be analyzed separately.

## What changed
- **Energy and ancillary services are co-optimized** in SCED/OCED simultaneously
  (previously dispatched separately, with adders bolted on via reserve pricing).
- **Price adders are no longer separate components of the LMP** — scarcity value is
  already factored into the co-optimized [[lmp-spp|LMP]]. (Diagram: "Under RTC" vs
  "Currently" in the source note.)
- Scarcity is now priced through **Ancillary Service Demand Curves (ASDCs)**, derived from
  the ORDC shape. Reserve products fill capacity in order — **Non-Spin & ECRS are exhausted
  before Reg-Up & RRS**. See [[ancillary-services]].

## New data fields (report NP6-793-ER, Dec 2025+)
Reliability-deployment prices per product: `RTRDPRU` (Reg-Up), `RTRDPRD` (Reg-Down),
`RTRDPRRS` (Responsive Reserve), `RTRDPECRS` (ERCOT Contingency Reserve), `RTRDPNS`
(Non-Spin), plus `RTRDPA`. These replace the pre-2025 `RTRSVPOR` / `RTRSVPOFF` / `RTRDP`.

## Empirical findings
- **(2026-07-03)** `RTRDPNS` (Non-Spin) is active in **100% of hours** across the full
  post-2025 window analyzed (Dec 2025–May 2026, 0 zero-hours out of 3,911) — every other
  reserve product has a normal zero-rate (3–84%). Confirmed (human) to be a genuine
  characteristic of the regime, not a data artifact: consistent with Non-Spin being
  exhausted first in the reserve fill order (see "What changed" above), so it prices in
  nearly every interval. See [[notebook-catalog|03_new_pa_activation]].

## Why it matters
Any volatility model spanning the boundary must treat Dec 2025 as a regime break — the
price-formation mechanism, the data schema, and the meaning of "price adder" all change.
Comparisons of adder behavior pre/post must be like-for-like.

## Reference
NPRR1010 §6.6.1.7 (RTC project); ERCOT "RTC + B Overview" slides. Via
[[sources/2026-06-30_ercot-market-concepts]].

## Related
- [[ordc-price-adders]] · [[ancillary-services]] · [[lmp-spp]] · [[price-volatility]] · [[energy-only-market]]
