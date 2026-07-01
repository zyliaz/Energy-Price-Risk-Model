---
title: Notebook Catalog (architecture)
type: concept
tags: [methods, notebooks, reference]
status: developing
sources: 0
updated: 2026-06-30
---

# Notebook Catalog (architecture)

What each **kept** notebook does and how `03_notebooks/` is organized. Companion to
[[extraction-scripts]] (the scripts) and [[analysis-workflow]] (the pipeline). Reflects the
16 notebooks in the new repo (legacy `00_emil`/`03`/`04`/`05` and helpers dropped — see
[[repo-migration-map]]).

## Grouping
- **`00_check/`** — prelim API inspection before writing an extractor.
- **`01_eda/`** — single-source: clean/aggregate one dataset, then its distribution/tail.
- **`02_analysis/`** — multi-source: merge datasets and study interactions.

Adder work is **mirrored across two regimes** (pre-2025 ORDC vs post-2025 [[rtc-b-asdc|RTC+B]]):
cleaning (`04`/`06` eda), distribution (`05`/`07` eda), activation (`02`/`03` analysis).

## Cross-cutting patterns
- **Load/clean:** DuckDB reads parquet + does SQL aggregation; cleaned CSVs written to
  `01_data/2_cleaned/`. (00, 01, 02, 04, 06 in `01_eda`.)
- **Correlation toolkit:** inline `scatter_corr()` — Pearson (OLS), Spearman (rank),
  Kendall (Theil-Sen) + p-values on one scatter. (NG notebooks.)
- **Activation analysis:** bin RTM price into quantiles → adder activation % (boolean) per
  bin → plot the top-N percentiles. (`02`/`03` analysis.)
- **Distribution:** seaborn, log-scale value distributions. (`05`/`07` eda.)
- **Merge:** pandas `merge` on datetime to align sources; intermediate merged CSVs saved
  for reuse. (`02_analysis`.)

## Reusable entry template
```markdown
### NN_slug   [stage · status]
- **Purpose:** one line.
- **In:** files/parquet. **Out:** csv/parquet/figures.
- **Methods:** duckdb · resample · quantile bins · scatter_corr · …
- **Wiki:** [[concept]]
```

---

## 00_check
### 00_emil_api_check   [check · stable]
- **Purpose:** ERCOT EMIL two-phase API probe — Phase 1 learn (fields/types/range), Phase 2
  targeted extract. Only `PRODUCT` required. Run before building a new scraper.
- **In:** Public API (live). **Out:** none. **Methods:** requests. **Wiki:** [[data-extraction-guide]]

## 01_eda — single-source clean + explore
### 00_rtm_price_eda   [eda · stable]
- **Purpose:** Clean & aggregate RTM SPP; produce the canonical RTM price series.
- **In:** `dam_lzhb_spp_2021_2025.parquet` (1.2_raw_api). **Out:** `ercot_rtm_prices_by_settlement_2021_2025.csv`,
  `rtm_price_aggregated_2021_2025.csv` (2_cleaned/rtm_price). **Methods:** duckdb, groupby. **Wiki:** [[rtm-dam]], [[price-volatility]]

### 01_load_eda   [eda · stable]
- **Purpose:** Actual-load EDA; North-zone time series.
- **In:** `load_fzn_...parquet` (1.2). **Out:** `load_by_LZ_...parquet`, `total_load_...csv` (2_cleaned/load).
- **Methods:** duckdb, rolling. **Wiki:** [[load-and-demand]]

### 02_mtlf_eda   [eda · stable]
- **Purpose:** Mid-term load forecast across 8 weather zones + system total (actual/forecast/error).
- **In:** `mid_term_load_forecast_...parquet` (2_cleaned/load/forecast). **Out:** WZ actual/error CSVs +
  `Hourly ERCOT system load and prediction`. **Methods:** duckdb, groupby. **Wiki:** [[mid-term-load-forecast]]

### 03_ng_price_correlation   [eda · stable]
- **Purpose:** NG-internal correlation (Henry Hub / citygate / electric-power), monthly.
- **In:** raw NG `.xls` (Henry Hub, citygate, electric power). **Out:** `ng_prices_monthly.csv`.
- **Methods:** resample, scatter_corr (pearson/spearman/kendall). **Wiki:** [[natural-gas-prices]]
- ⚠️ Inputs are the raw NG `.xls` **left in the old repo** (not copied) — see Issues.

### 04_price_adders_pre2025_cleaning   [eda · stable]
- **Purpose:** Clean pre-2025 adders → 15-min, hourly, and binary-activation series.
- **In:** `rtm_price_adders_15min_20200101_20251231.parquet` (1.2). **Out:** `price_adders_{15min,hourly,binary}_...csv`
  (2_cleaned/price_adders). **Methods:** duckdb aggregate. **Wiki:** [[ordc-price-adders]]

### 05_price_adder_distribution   [eda · stable]
- **Purpose:** Pre-2025 adder value distribution (log scale).
- **In:** `price_adders_numerical_analysis.csv`, `rtm_price_adders_hourly.csv`. **Out:** figures.
- **Methods:** seaborn. **Wiki:** [[ordc-price-adders]]

### 06_new_pa_cleaning   [eda · stable]
- **Purpose:** Validate & aggregate post-2025 (RTC+B) ancillary adders (`RTRDPA/RU/RD/RRS/ECRS/NS`).
- **In:** `rtm_price_adders_15min_20251205_20260517.parquet` (1.2). **Out:** `post_202512_price_adders_hourly.csv` + `_binary.csv`.
- **Methods:** duckdb. **Wiki:** [[rtc-b-asdc]]

### 07_new_pa_distribution   [eda · stable]
- **Purpose:** Post-2025 adder value distribution.
- **In:** `post_202512_price_adders_hourly.csv`, `rtm_price_mean_...csv`. **Out:** figures.
- **Methods:** seaborn, OLS. **Wiki:** [[rtc-b-asdc]]

### 08_hdd_eda_wip   [eda · wip]
- **Purpose:** Texas HDD/CDD vs load (and price) over the year.
- **In:** `total_load.csv`, `rtm_price_aggregated.csv`, `Texas_..._daily_HDD_CDD.parquet` (2_cleaned).
- **Out:** `Daily_HDD_rtm_load_2021_2025.csv`. **Methods:** merge, resample. **Wiki:** [[weather-hdd-cdd]]

## 02_analysis — multi-source interactions
### 00_load_forecast_rtm_correlation_wip   [analysis · wip]
- **Purpose:** Load-forecast error vs RTM price. Finding: **log(price) vs forecast error → weak**.
- **In:** `Hourly ERCOT system load and prediction.csv`, `rtm_price_aggregated.csv`.
- **Methods:** merge, resample, scatter. **Wiki:** [[mid-term-load-forecast]], [[load-and-demand]]

### 01_ng_rtm_price_correlation   [analysis · stable]
- **Purpose:** NG vs RTM price, incl. dedicated **Feb-2021 (Uri)** analysis.
- **In:** `ng_prices_monthly.csv`, `rtm_price_aggregated.csv`. **Methods:** resample, scatter_corr. **Wiki:** [[natural-gas-prices]], [[price-volatility]]

### 02_price_adder_activation   [analysis · stable]
- **Purpose:** Pre-2025 adder activation % by RTM price quantile.
- **In:** `price_adders_hourly.csv`, `rtm_price_aggregated.csv`. **Out:** `price_adders_activation_analysis.csv`.
- **Methods:** quantile bins, groupby, merge. **Wiki:** [[ordc-price-adders]]

### 03_new_pa_activation   [analysis · stable]
- **Purpose:** Post-2025 ancillary-adder activation by price quantile.
- **In:** `post_202512_price_adders_hourly_binary.csv`, `rtm_lzhb_spp_20251205_20260516.parquet` (1.2).
- **Out:** `rtm_price_mean_...csv`, activation csv. **Methods:** quantile bins. **Wiki:** [[rtc-b-asdc]]

### 04_price_adder_rtm_load_correlation   [analysis · stable]
- **Purpose:** Adder ↔ RTM ↔ load correlations, **both regimes** (largest notebook, 27 cells).
- **In:** `pre_2025_rtm_price.csv`, `price_adders_numerical_analysis.csv`, `post_202512_price_adders_hourly.csv`,
  `ercot_LZ_load_hourly.parquet`. **Out:** `pre2025_merged_data.csv`, `adder_abnormal_pre2025_no_uri.csv`.
- **Methods:** merge, corr, scatter. **Wiki:** [[ordc-price-adders]], [[load-and-demand]]

### 05_load_rtm_price_plot   [analysis · stable]
- **Purpose:** RTM price vs load, faceted by year.
- **In:** `total_load.csv`, `rtm_price_aggregated.csv` (2_cleaned). **Methods:** groupby, merge, scatter. **Wiki:** [[load-and-demand]], [[price-volatility]]

### 06_investigate_abnormal_pa_wip   [analysis · wip]
- **Purpose:** Cases where **adders > RTM** (abnormal hours by month; RTM by LZ) — the PA-vs-SPP / negative-LMP probe.
- **In:** adder hourly, `rtm_price_aggregated.csv`, `ercot_rtm_prices_by_settlement.csv`, `total_load.csv`.
- **Out:** `merged_data.csv`. **Methods:** merge, groupby, scatter. **Wiki:** [[lmp-spp]], [[ordc-price-adders]]

---

## Issues to reconcile
- **Mixed path conventions.** Some notebooks already use new paths (`01_data/2_cleaned/…` in
  `02_mtlf`, `08_hdd`, `05_load_rtm_price_plot`); others still read bare filenames or old
  `data/…`. Standardize on `01_data/{1.2_raw_api,2_cleaned,3_analysis}` — pending patch
  ([[repo-migration-map]]).
- **NG inputs not copied.** `03_ng_price_correlation` reads raw NG `.xls` files that were left
  in the old repo (figures/raw excluded from the copy), and the Waha scraper was removed. NG
  data provenance needs a decision — see [[natural-gas-prices]], [[extraction-scripts]].
- **eda↔analysis file coupling.** A few intermediates (e.g. `price_adders_numerical_analysis.csv`,
  `rtm_price_adders_hourly.csv`) are produced in one notebook and consumed in another; keep
  the producer/consumer order in mind when re-running.

## Related
- [[extraction-scripts]] · [[analysis-workflow]] · [[data-extraction-guide]] · [[repo-migration-map]]
