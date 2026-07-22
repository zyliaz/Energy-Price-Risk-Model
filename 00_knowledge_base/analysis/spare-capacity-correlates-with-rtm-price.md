---
title: Spare-capacity metric correlates strongly with RTM price
type: analysis
tags: [ercot, capacity, price-volatility, scarcity, regression]
status: developing
notebook: 03_notebooks/02_analysis/06_spare_capacity.ipynb
date: 2026-07-14
updated: 2026-07-17
---

# Spare-capacity metric correlates strongly with RTM price

**Question asked:** Does a "spare capacity" ratio — how much load is squeezing
non-renewable firm capacity, net of renewable generation — explain RTM price levels?

**Method / data used:** `03_notebooks/02_analysis/06_spare_capacity.ipynb` (supersedes
the broken `06_metric_nonvariable_load_capacity.ipynb`, deleted 2026-07-14). Metric1 =
`(total_load − renewable_gen) / non_re_capacity`, built via DuckDB join of
`hourly_solar_wind_generation_2020_2025.parquet`, `total_load_20201231_20260526.csv`,
`ERCOT nonRE capacity 2020-2025.csv`, and `rtm_price_aggregated_2021_2025.csv`. Winter
Storm Uri points explicitly excluded (known outlier, not representative of general
conditions). Plotted vs `log(rtm_price)`: LOWESS fit faceted by year (2021–2025), and
scatter color-coded by natural-gas price (log scale) and by degree days
(`|avg_temp − 65°F|`).

**Answer / finding:**
- The spare-capacity metric correlates strongly with `log(rtm_price)` — confirmed
  visually across all 5 years (2021–2025) in `06_spare_capacity.ipynb` (verified passing).
- A follow-on OLS regression (`rtm_price ~ year + season + spare_capacity + ng_price +
  degree_days`) previously computed in `03_notebooks/03_model/01_regression.ipynb` gave
  R²=0.552, `spare_capacity` coefficient ≈ +115 (p<0.001), `ng_price` coefficient ≈ +6.3
  (p<0.001), `degree_days` coefficient ≈ −0.44 (p<0.001), `year` not significant
  (p=0.45); a separate sklearn linear-regression fit (same features) gave R²=0.40.
  **As of 2026-07-17 these numbers are historical, not currently reproducible**: the human
  edited `01_regression.ipynb` to remove its Random Forest cell (which had a metric bug),
  but the edit removed all modeling cells (OLS and sklearn `LinearRegression` included) —
  the notebook now only builds and exports the merged dataset
  (`01_data/4_model/ercot_regression_model_dataset.csv`), no model is fit. Treat the R²/
  coefficients above as provisional until a modeling notebook re-derives them. See
  [[notebook-catalog]].
- Higher natural-gas price is generally associated with higher `log(rtm_price)` at a
  given spare-capacity level.
- Higher degree days (hotter or colder relative to 65°F) push the spare-capacity
  metric closer to 1 (tighter conditions), consistent with summer/winter peak-load
  stress.
- Tail behavior (metric near 1) coincides with high summer load or elevated
  data-center-driven load.

**Citations:** [[feature-engineering]], [[notebook-catalog]],
[[sources/2026-07-13_weekly-meeting-spare-capacity]],
[[sources/2026-07-14_capacity-model-research-update]],
`03_notebooks/02_analysis/06_spare_capacity.ipynb` (verified),
`03_notebooks/03_model/01_regression.ipynb` (dataset-export only as of 2026-07-17;
regression numbers above are historical/not currently reproducible from this notebook).

## Related
- [[feature-engineering]]
- [[00_overview]]
- [[price-volatility]]
