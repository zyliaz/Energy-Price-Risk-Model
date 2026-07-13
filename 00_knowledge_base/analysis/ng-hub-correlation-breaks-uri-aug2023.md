---
title: NG hub prices move together except Uri (2021-02) and Aug 2023
type: analysis
tags: [ercot, natural-gas, correlation, eda]
status: developing
notebook: 03_notebooks/01_eda/03_ng_price_correlation.ipynb
date: 2026-07-03
updated: 2026-07-05
---

# NG hub prices move together except Uri (2021-02) and Aug 2023

**Question asked:** How tightly do the three NG price benchmarks (Henry Hub, TX citygate,
TX electric-power) track each other monthly?

**Method / data used:** `03_notebooks/01_eda/03_ng_price_correlation.ipynb` — monthly
resample + `scatter_corr()` (Pearson/Spearman/Kendall) on the raw NG `.xls` series in
`01_data/1.3_raw_other/ng_price/`.

**Answer / finding:** The three benchmarks are strongly correlated at monthly resolution,
with exactly two deviation events: **2021-02 (Winter Storm Uri)** and **2023-08**. Uri is
explained; no ERCOT-specific event is logged in the wiki for Aug 2023 yet.

**Citations:** [[natural-gas-prices]], [[sources/2026-07-03_analysis-summary]],
`03_notebooks/01_eda/03_ng_price_correlation.ipynb`, `01_data/3_analysis/ng_price/ng_prices_monthly.csv`.

## Related
- [[natural-gas-prices]]
- [[load-price-correlation-is-seasonal]]
