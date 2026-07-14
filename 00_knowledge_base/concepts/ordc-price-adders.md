---
title: ORDC Price Adders
type: concept
tags: [scarcity, pricing, ercot, core]
status: developing
sources: 3
updated: 2026-07-05
---

# ORDC Price Adders

The **Operating Reserve Demand Curve (ORDC)** administratively adds a price **adder** to
ERCOT energy prices as operating reserves tighten (adder ≈ LOLP × VOLL). This was ERCOT's
core scarcity-pricing mechanism through **Nov 2025**; from Dec 2025 it is superseded by
co-optimized [[rtc-b-asdc|RTC+B / ASDC]]. It remains the suspected dominant driver of
historical [[price-volatility]].

## Mechanism (pre-Dec-2025)
- **RTORPA** — On-line Reserve Price Adder from the ORDC. **Activates when
  (reserves − generation) < 7 GW.**
  - Before 2021-02: peaks at **$9,000/MWh** when reserves < 2,000 MW.
  - After 2021-02: peaks at **$5,000/MWh** when reserves < 3,000 MW (PUCT cap change —
    a structural breakpoint, see [[puct]]).
- **RTRDPA** — Reliability Deployment Adder; out-of-market action when DAM generation is
  insufficient. Can act as a price **correction** when system-wide LMP is suppressed < 0.

Adders are added **system-wide** (vs locational LMP) — see [[lmp-spp]]. They convert
tight-reserve moments (often **low [[wind-power-production|wind]] + high
[[load-and-demand|demand]]**) into extreme, nonlinear price spikes.

## Data fields (report NP6-793-ER, 15-min, system-wide)
- **2014 – Nov 2025:** `RTRSVPOR`, `RTRSVPOFF`, `RTRDP`.
- **Dec 2025+:** `RTRDPA`, `RTRDPRU`, `RTRDPRD`, `RTRDPRRS`, `RTRDPECRS`, `RTRDPNS` — see
  [[rtc-b-asdc]].
- **Exact cutover (measured from raw 15-min data, `01_data/1.2_raw_api/
  rtm_price_adders_15min_20200101_20251231.parquet`, 2026-07-03):** old-schema fields
  (`RTRSVPOR`/`RTRSVPOFF`/`RTRDP`) last carry a nonzero value at **2025-12-04 20:45:00**;
  new-schema fields (`RTRDPA`/etc.) first carry a nonzero value at **2025-12-05 00:00:00**.
  This is the exact **RTC+B go-live boundary** the codebase splits pre/post datasets on
  (e.g. `04_price_adder_rtm_load_correlation` filters `datetime <= '2025-12-04'` vs
  `>= '2025-12-05'`) — treat 2025-12-05 00:00 as the hard schema-change timestamp, and never
  merge pre/post dataframes across it without re-deriving a common adder definition.

## Empirical findings so far
- Adder **activation (Boolean) by RTM price quantile** steepens sharply at higher quantiles;
  top-5-percentile tails increase **except RTRDP**, whose tail is non-monotonic.
- **Value distribution (log scale):** larger-adder bins have lower counts; `RTRDP`'s right
  tail is tilted by **[[winter-storm-uri|Winter Storm Uri]] (Feb 2021)**.

> **(2026-07-03)** Reproduced on both schemas: pre-Dec-2025 activation/tail behavior as above,
> and the post-Dec-2025 RTC+B/ASDC fields ([[rtc-b-asdc]]) show the same activation-by-quantile
> pattern with no new deviation flagged. See [[analysis/adder-activation-steepens-with-price]] and [[analysis/rtcb-activation-mirrors-ordc]].

## Related
- [[rtc-b-asdc]] · [[lmp-spp]] · [[ancillary-services]] · [[price-volatility]] · [[energy-only-market]] · [[puct]]

## Sources
- [[sources/2026-06-30_ercot-market-concepts]] · [[sources/2026-06-30_data-and-eda-notes]] ·
  [[sources/2026-07-03_analysis-summary]]
