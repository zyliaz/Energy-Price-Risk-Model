---
title: Price adder stays below RTM SPP except in negative-price hours
type: analysis
tags: [pricing, scarcity, ordc, lmp-spp, ercot]
status: developing
notebook: 03_notebooks/02_analysis/07_pa_vs_spp.ipynb
date: 2026-07-23
updated: 2026-10-28
---

# Price adder stays below RTM SPP except in negative-price hours

**Question asked:** Is the RTM ORDC price **adder (PA)** always ≤ the RTM **settlement point
price (SPP)**? The adder is a component of the RTM SPP, so PA ≤ SPP should hold whenever the
underlying energy (system-lambda) component is ≥ 0.

**Method / data used:** `07_pa_vs_spp.ipynb`. Hourly adders (hour-ending) merged on the raw HE
timestamp — no shift — with the corrected system-wide RTM SPP. Pre-2025 PA uses
`adder_effective = RTRSVPOR + RTRDP` (the online ORDC adder embedded in the RTM price; `RTRSVPOFF`
is an offline-reserve adder **not** embedded in the online SPP, so it is excluded). Post-2025 uses
the summed RTC-B deployment adders. RTM SPP is the real 15-min RTM series aggregated to HE hourly
(`rtm_price_aggregated_2021_2025.csv`, corrected 2026-07-23 — see [[feature-engineering]]).

**Answer / finding:**
- **PA ≤ SPP is not universal, but holds ~99.9% of pre-2025 hours** (43,107/43,146 with
  `adder_effective`). All 39 exceptions sit at **near-zero or negative SPP** (85% have SPP < 0;
  exception SPP median −$1.84, max +$3.50). When the energy component is negative (oversupply /
  high renewables), the small standalone reserve adder exceeds the depressed total SPP. This is
  **economically valid, not a data artifact** — the adder is embedded in the SPP, so it can only
  exceed the total when the non-adder component is negative.
- Using `adder_sum` (which adds the offline `RTRSVPOFF`) produces 64 exceptions, including
  high-price hours — expected, because `RTRSVPOFF` is not part of the online SPP. `adder_effective`
  is the correct measure for the "embedded adder ≤ price" test.
- **Post-2025 (RTC-B regime) is different: PA ≤ SPP holds only ~96.2%** (7,482/7,775,
  2025-12-05 – 2026-10-24; 2026-10-28 rerun), 293 exceptions (58% at SPP < 0, but some at high
  SPP, up to $1,112 on 2026-01-28 HE8). The May-window figure (93.5%, 255 exceptions) used an
  SPP that kept only the first 15-min interval per hour; the rerun uses the hourly interval mean. The post-2025 `adder_sum` is a sum of
  ancillary-service-specific deployment adders (RTRDPRU/RD/RRS/ECRS/NS), not a single embedded
  energy adder, so its sum is not bounded by the energy SPP — exceptions here are not anomalous.
- **The earlier apparent PA>SPP problem was inflated by two now-fixed bugs:** comparing against
  **Day-Ahead** prices (178–220 exceptions) and a **1-hour HE/HS misalignment**. With corrected
  RTM prices + HE alignment, pre-2025 exceptions fall to 39 and are fully explained by
  negative-price hours.

**Citations:** `03_notebooks/02_analysis/07_pa_vs_spp.ipynb`,
`01_data/3_analysis/price_adders_analysis/pa_vs_spp/pa_gt_spp_exceptions_20261024.csv` (332 exception
hours, pre+post), [[ordc-price-adders]], [[lmp-spp]], [[rtc-b-asdc]], [[feature-engineering]].

## Related
- [[ordc-price-adders]] · [[lmp-spp]] · [[rtm-dam]] · [[rtc-b-asdc]] · [[price-volatility]]
- [[adder-activation-steepens-with-price]] · [[feature-engineering]]
