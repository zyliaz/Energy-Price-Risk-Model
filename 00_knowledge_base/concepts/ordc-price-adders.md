---
title: ORDC Price Adders
type: concept
tags: [scarcity, pricing, ercot, core]
status: developing
sources: 2
updated: 2026-06-30
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

## Empirical findings so far
- Adder **activation (Boolean) by RTM price quantile** steepens sharply at higher quantiles;
  top-5-percentile tails increase **except RTRDP**, whose tail is non-monotonic.
- **Value distribution (log scale):** larger-adder bins have lower counts; `RTRDP`'s right
  tail is tilted by **Winter Storm Uri (Feb 2021)**.
- **PA > SPP cases:** PA can exceed SPP when local LMP < 0 (reliability-deployment
  suppression, or regional wind) — open hypothesis, validate with nodal LMP. See [[lmp-spp]].

## Legacy work to migrate
Parsing `src/transformation/parse_rtm_price_adders*.py`; notebooks `08_*` (pre-2025) and
`09_*` (new PA); load correlation `10_*`; open `10.1_[PENDING]_investigate_abnormal_PA`.

## Related
- [[rtc-b-asdc]] · [[lmp-spp]] · [[ancillary-services]] · [[price-volatility]] · [[energy-only-market]] · [[puct]]

## Sources
- [[sources/2026-06-30_ercot-market-concepts]] · [[sources/2026-06-30_data-and-eda-notes]]
