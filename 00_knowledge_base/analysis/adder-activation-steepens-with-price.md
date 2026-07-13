---
title: Pre-2025 adder activation steepens with RTM price quantile (RTRDP tail excepted)
type: analysis
tags: [ercot, scarcity, pricing, ordc]
status: developing
notebook: 03_notebooks/02_analysis/02_price_adder_activation.ipynb
date: 2026-07-03
updated: 2026-07-05
---

# Pre-2025 adder activation steepens with RTM price quantile (RTRDP tail excepted)

**Question asked:** How does ORDC-era (pre-Dec-2025) adder activation vary with the RTM
price level?

**Method / data used:** `03_notebooks/02_analysis/02_price_adder_activation.ipynb` — RTM
price binned into quantiles; per-bin activation % from binary `{col}_active` flags
(mean-of-binary, bounded [0,100]% — see the scaling-bug fix in [[notebook-catalog]]).

**Answer / finding:** Activation % rises sharply and monotonically at higher price
quantiles (top bin: ~85% Adder Sum activation). The one exception is **RTRDP's tail**,
which is non-monotonic.

**Citations:** [[ordc-price-adders]], [[sources/2026-07-03_analysis-summary]],
`03_notebooks/02_analysis/02_price_adder_activation.ipynb`,
`01_data/3_analysis/price_adders_analysis/price_adders_activation_analysis.csv`.

## Related
- [[ordc-price-adders]]
- [[rtcb-activation-mirrors-ordc]]
