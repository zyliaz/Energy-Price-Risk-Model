---
title: ERCOT
type: entity
tags: [market, iso, texas]
status: developing
sources: 0
updated: 2026-06-30
---

# ERCOT (Electric Reliability Council of Texas)

The independent system operator for ~90% of Texas load. Operates an **energy-only**
wholesale market (no centralized capacity market), making scarcity pricing the primary
mechanism for resource-adequacy signals — see [[energy-only-market]].

## Why it matters here
ERCOT's design routes fixed-cost recovery through a few high-price scarcity hours,
which makes [[ordc-price-adders]] a dominant source of [[price-volatility]]. It is also
a wind-heavy grid, so [[wind-power-production]] variability strongly shapes net load.

## Market structure (quick map)
- **DAM** (day-ahead) and **RTM** (real-time, ~5-min SCED) — see [[rtm-dam]].
- Prices expressed as **LMP** (nodal) and **SPP** (settlement-point) — see [[load-zones]].
- Scarcity via the **ORDC** — see [[ordc-price-adders]].

## Data delivery
ERCOT publishes via the **Public API / EMIL** (report IDs like NP6-788-CD for RTM LMP).
Extraction code: `02_scripts/1_api_extraction`. See [[ercot-data-products]].

## Related
- [[energy-only-market]] · [[rtm-dam]] · [[ordc-price-adders]] · [[load-zones]]
