---
title: RTC+B adder activation mirrors ORDC pattern; Non-Spin is always on
type: analysis
tags: [ercot, scarcity, rtc-b, regime-change]
status: developing
notebook: 03_notebooks/02_analysis/03_new_pa_activation.ipynb
date: 2026-07-03
updated: 2026-07-05
---

# RTC+B adder activation mirrors ORDC pattern; Non-Spin is always on

**Question asked:** Do the post-Dec-2025 RTC+B/ASDC ancillary adders behave like the old
ORDC adders?

**Method / data used:** `03_notebooks/02_analysis/03_new_pa_activation.ipynb` — same
quantile-bin activation method as the pre-2025 notebook, on genuinely binarized inputs
(binarized upstream in `06_new_pa_cleaning`; audited clean of the pre-2025 scaling bug).

**Answer / finding:**
- The RTC+B fields reproduce the **same activation-by-quantile pattern** as the ORDC-era
  adders — no new deviation flagged. See [[adder-activation-steepens-with-price]].
- ✅ Confirmed (human, 2026-07-03): **`RTRDPNS` is active in 100% of hours** (0 zero-hours
  of 3,911, Dec-2025–May-2026). Every other adder has a real zero-rate (`RTRDPA` 84%,
  `RTRDPRU` 8%, `RTRDPRD` 3%, `RTRDPRRS` 4%, `RTRDPECRS` 4%). Genuine system
  characteristic — Non-Spin is exhausted first in the reserve fill order, so it prices in
  nearly every interval — not a parsing artifact.

**Citations:** [[rtc-b-asdc]], [[ordc-price-adders]], [[sources/2026-07-03_analysis-summary]],
`03_notebooks/02_analysis/03_new_pa_activation.ipynb`.

## Related
- [[rtc-b-asdc]]
- [[adder-activation-steepens-with-price]]
