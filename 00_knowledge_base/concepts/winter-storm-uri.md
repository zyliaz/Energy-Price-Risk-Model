---
title: Winter Storm Uri (Feb 2021)
type: concept
tags: [scarcity, weather, event, ercot]
status: stub
sources: 0
updated: 2026-07-13
---

# Winter Storm Uri (Feb 2021)

**Date range: 2021-02-13 → 2021-02-17** (storm over Texas); **ERCOT emergency
conditions ran ~2021-02-14 → 2021-02-19**, with EEA3 declared early on **Feb 15**
and firm load shed through **Feb 18**. The canonical extreme-scarcity event in the
study period — an outlier that dominates the right tail of every
[[price-volatility]] measure and must be handled explicitly (keep/flag/winsorize)
in any pre-2025 analysis.

## What happened
- Extreme cold ([[weather-hdd-cdd]]) drove record winter demand while
  simultaneously forcing out roughly half of generation capacity (gas supply
  freeze-offs dominated; wind icing contributed — [[wind-power-production]]).
- RTM prices were held at the then-**$9,000/MWh cap for ~4 consecutive days**
  (Feb 15–19), partly by [[puct]] order during load shed — see
  [[ordc-price-adders]].
- Texas gas spot prices spiked by orders of magnitude, breaking the normal
  hub correlation — the **2021-02 deviation** in
  [[analysis/ng-hub-correlation-breaks-uri-aug2023]] ([[natural-gas-prices]]).

## Why it matters here
- Stress-tests the [[energy-only-market]] design; in its aftermath PUCT cut the
  offer cap $9,000 → $5,000/MWh, the structural breakpoint noted in
  [[ordc-price-adders]].
- Tilts `RTRDP`'s right tail in the adder value distribution
  ([[analysis/adder-activation-steepens-with-price]]).

## Related
- [[price-volatility]] · [[ordc-price-adders]] · [[natural-gas-prices]] ·
  [[weather-hdd-cdd]] · [[energy-only-market]] · [[puct]]

## Sources
- Public record (FERC/NERC & ERCOT post-event reports); no dedicated source page
  ingested yet. Wiki evidence: [[analysis/ng-hub-correlation-breaks-uri-aug2023]].
