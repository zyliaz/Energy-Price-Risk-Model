---
title: Load–price correlation concentrates in months 1–2 and 5–10
type: analysis
tags: [ercot, load, pricing, seasonality]
status: developing
notebook: 03_notebooks/02_analysis/05_load_rtm_price_plot.ipynb
date: 2026-07-03
updated: 2026-07-05
---

# Load–price correlation concentrates in months 1–2 and 5–10

**Question asked:** When during the year does load actually move RTM prices?

**Method / data used:** `03_notebooks/02_analysis/05_load_rtm_price_plot.ipynb` —
`log(price)` vs load scatter, faceted by year/month, on `total_load.csv` +
`rtm_price_aggregated.csv`.

**Answer / finding:** `log(price)` vs load correlates more strongly in **months 1–2 and
5–10** than the rest of the year. This refines the earlier pooled "summer" claim to
specific months (winter peak + long cooling season).

**Citations:** [[load-and-demand]], [[sources/2026-07-03_analysis-summary]],
`03_notebooks/02_analysis/05_load_rtm_price_plot.ipynb`.

## Related
- [[load-and-demand]]
- [[cooling-demand-rising-with-population]]
