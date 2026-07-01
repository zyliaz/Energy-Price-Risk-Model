---
title: ERCOT Market Concepts (note)
type: source
tags: [pricing, ordc, asdc, ancillary-services, lmp]
status: developing
date_ingested: 2026-06-30
source_kind: note
raw_path: uploads/ERCOT Market Concepts.pdf
external_sources: [EIA "Sources of Price Volatility in the ERCOT Market", Modo Energy, ERCOT education slides, NPRR1010]
updated: 2026-06-30
---

# ERCOT Market Concepts (note)

A working concept note (dated 2026-05-18) synthesizing ERCOT pricing mechanics from the
**EIA report "Sources of Price Volatility in the ERCOT Market," Modo Energy explainers,
and ERCOT education material**. Covers the pre- and post-Dec-2025 price-adder regimes.

## Key facts

**LMP / SPP decomposition.** `RTM price (SPP) = LMP + price adders (PA)`, where
`LMP = system lambda (energy) + transmission congestion + losses`. PA is added
**system-wide**; LMP is **locational**. SPP is an aggregation of LMP by geography
(resource node, load zone, trading hub). See [[lmp-spp]].

**Pre-2025-Dec adders (ORDC):**
- **RTORPA** — On-line reserve price adder from the [[ordc-price-adders|ORDC]]. Activates
  when (reserves − generation) < **7 GW**. Pre-2021-02: peaks at **$9000** when < 2000 MW;
  post-2021-02: peaks at **$5000** when < 3000 MW.
- **RTRDPA** — Reliability Deployment adder; out-of-market action when DAM generation is
  insufficient; can act as a price correction when system-wide LMP is suppressed < 0.

**Drivers of price volatility (per EIA report):** (1) energy cost, esp. natural gas;
(2) growth in peak demand; (3) availability of renewables (wind). See [[price-volatility]].

**Temporal/spatial variation:** North LZ has high mean & variance (congestion + high
demand); West LZ low (low demand). Online-reserve adders fire under **low-wind /
high-demand**; minimal adders on summer days even at high demand. See [[load-zones]].

**Post-2025-Dec regime (RTC+B / ASDC):** Real-Time Co-optimization with Batteries folds
ancillary services into the SCED/OCED optimization. **Price adders are no longer separate
LMP components** — scarcity value is co-optimized in. New reliability-deployment price
fields RTRDPRU/RD/RRS/ECRS/NS replace the old structure. ASDCs derive from the ORDC shape;
reserves fill in order (Non-Spin & ECRS exhausted before Reg-Up & RRS). See [[rtc-b-asdc]]
and [[ancillary-services]]. (Ref: NPRR1010 §6.6.1.7.)

**PA > SPP cases (open hypothesis):** When PA activated (>0) and SPP > 0 but LMP < 0 —
either (a) system-wide LMP suppressed by reliability deployments (RTRDPA as correction),
or (b) locational negative LMP from regional wind. To validate by collecting LMP data.

**DAM mechanics:** buyers typically purchase **80–90%** of next-day need in DAM for
certainty; the remainder is exposed to RTM. See [[rtm-dam]].

## Why it matters to the thesis
Gives the authoritative mechanism behind [[ordc-price-adders]] (with real thresholds/caps),
confirms the EIA-sourced volatility drivers behind [[00_overview]], and flags a structural
break (RTC+B) that segments the price history into pre/post-Dec-2025 regimes.

## Affected wiki pages
[[ordc-price-adders]], [[rtc-b-asdc]], [[ancillary-services]], [[lmp-spp]], [[rtm-dam]],
[[price-volatility]], [[load-zones]], [[energy-only-market]], [[00_overview]]

## Contradictions / caveats
- "RTORPA" (this note) vs "RTORPA/RTOLCAP" (earlier wiki guess) — adopt this note's naming.
- ORDC caps are PUCT parameters with effective dates (2021-02 change) — treat as
  structural breakpoints. See [[puct]].
