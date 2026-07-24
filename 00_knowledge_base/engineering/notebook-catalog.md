---
title: Notebook Catalog (architecture)
type: engineering
tags: [methods, notebooks, reference]
status: developing
sources: 0
updated: 2026-07-24
---

# Notebook Catalog (architecture)

What each **kept** notebook does and how `03_notebooks/` is organized. Companion to
[[extraction-scripts]] (the scripts) and [[analysis-workflow]] (the pipeline). Reflects the
notebooks in `00_check`/`01_eda`/`02_analysis`/`03_model` (old `00_emil`/`03`/`04`/`05` and 2
helper scripts dropped during migration, not renamed/kept; `01_wind_solar_5min_endpoint_check`
added 2026-07-03; `06_investigate_abnormal_pa_wip` + its output `merged_data.csv` dropped
2026-07-05 — not formally tested, PA>SPP claims removed from the wiki;
`06_metric_nonvariable_load_capacity` added 2026-07-10 then **deleted 2026-07-14** (commit
`eace499`), replaced by `06_spare_capacity` — same slot, renamed, rewritten, now passing — see
its entry; `02_era5_ercot_temp` added 2026-07-21; `00_load_forecast_rtm_correlation_wip`
renamed `00_load_forecast_rtm_correlation` and `09_mtlf_models_eda` **deleted**, both
2026-07-23/24, uncommitted; `00.0_load_fcast_wzn_aug2023` added 2026-07-24). A 4th grouping,
`03_model/`, was adopted into CLAUDE.md §2 on 2026-07-17 (human confirmed) for statistical/ML
modeling on top of `02_analysis` outputs; its first notebook, renamed
`01_regression_data.ipynb` (was `01_regression.ipynb`) 2026-07-21, is cataloged in its own
section below, alongside a new companion R script outside the notebook-catalog's scope.

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
- **Last run: YYYY-MM-DD — PASS/FAIL.** what was actually executed, not inferred from reading code.
```

## Status-label rule (adopted 2026-07-03)
`stable`/`broken`/`wip` is a claim about **behavior**, not appearance — only a fresh execution
can justify it, never a code read. A notebook can look structurally fine (imports resolve,
paths exist, cells are ordered sensibly) and still be dead on arrival: a no-op column rename
or a variable referenced before assignment only surfaces at runtime. Rules:
- `stable` requires a recorded `Last run: <date> — PASS`, i.e. it was actually re-executed
  end-to-end with zero cell errors, and any declared output file was confirmed on disk after.
- `broken` = it was run and it failed; the entry states the exact failing cell/line and why.
- Cached cell outputs inside a notebook are not evidence of anything — a notebook's on-disk
  output can look successful while its current code, freshly run, fails (drift between edited
  code and stale cached output). Don't infer PASS from a notebook's stored outputs; re-run it.
- `updated:` in frontmatter tracks doc edits; `Last run:` tracks code verification. Don't
  conflate the two — this file's 2026-07-01 "verified" claim was a doc edit, not a re-run, and
  it was wrong.

---

## 00_check
### 00_endpoint_check_template   [check · template]
- **Purpose:** Reusable ERCOT EMIL pre-scraper review template (supersedes the old
  `00_emil_api_check`). Four phases per product list: (1) endpoint + field schema discovery,
  including a min/max probe (sort ASC/DESC, `size=1`) on each product's range field to report
  the actual datetime coverage window; (2) live-API history depth probe over sample dates;
  (3) archive-API depth (oldest/newest doc via `/archive/{PRODUCT}`); (4) row-volume →
  parquet size estimate. Ends with a human decision checklist gating extractor build.
- **In:** Public API (live + archive). **Out:** none. **Methods:** requests. **Wiki:**
  [[data-extraction-guide]]
- Requires `.env` (copy from `.env.example`, fill `ERCOT_USERNAME`/`ERCOT_PASSWORD`/
  `ERCOT_SUBSCRIPTION_KEY`) — needs real credentials only the human has.
- Fixed 2026-07-08: Phase-1 cell existed twice — a stale draft (`ts_field` computed as a
  list and passed straight to `sort`/`fields_df[...]` indexing, plus an unclosed f-string
  paren) followed by the corrected version (scalar `ts_field`, empty-df guards, closing
  paren). Deleted the stale duplicate; only the working cell remains.
- **Last run: not yet re-run since 2026-07-08 template rewrite.** Copy this notebook per
  new product set before writing an extractor.

### 01_wind_solar_5min_endpoint_check   [check · blocked]
- **Purpose:** Pre-scraper review for the planned 5-min wind/solar extractors. Four phases:
  (1) endpoint + field schema for NP4-743/746/733/738/745-CD via EMIL artifact discovery,
  (2) live-API history depth probe, (3) archive-API depth (oldest doc), (4) row-volume →
  parquet size estimate. Ends with a human decision checklist (product choice, params,
  backfill need) gating `ercot_wpp_5min.py` / `ercot_spp_5min.py`.
- **In:** Public API (live + archive). **Out:** none. **Methods:** requests. **Wiki:**
  [[data-extraction-guide]], [[wind-power-production]]
- **Last run: never — blocked on missing `.env`** (same as the template above). Built
  2026-07-03; syntax-validated only. Human must run and review before scrapers are written.
- Carries the canonical **zone-column-name reference table** (weather/LZ/FZN/wind/solar
  spellings as they appear in parquets) for schema checks; `00_emil_api_check` points here.
  Wiki mirror: [[load-zones]].

### 02_era5_ercot_temp   [check · developing]
- **Purpose:** Pre-scraper review + first pull for hourly Texas-statewide temperature from
  **ERA5** (Copernicus CDS reanalysis) — added 2026-07-21 to switch degree-days from the old
  daily GRIDMET/county source to hourly, for modeling (per [[sources/2026-07-20_meeting-notes]]).
  Clips a lat/lon bbox to the TX state boundary (GeoJSON, cached), pulls one test month via
  `cdsapi.Client.retrieve()`, masks + averages to a single Texas-wide hourly series, exports.
- **In:** CDS API (`reanalysis-era5-single-levels`, `2m_temperature`) + a public TX boundary
  GeoJSON. **Out:** `01_data/1.2_raw_api/era5_hourly_temp/*.nc`,
  `01_data/2_cleaned/weather/Texas Hourly Temperature Average test.csv`. **Methods:** cdsapi,
  xarray, geopandas. **Wiki:** [[weather-hdd-cdd]], [[data-extraction-guide]]
- Requires `.env` (`CDS_API_URL`/`CDS_API_KEY`) — present and populated in this repo's `.env`
  (unlike the ERCOT `00_check` notebooks, which are credential-blocked).
- ⚠️ Cell 4 ("test cell") calls `client.retrieve()` unconditionally, with no existing-file
  skip check (unlike the companion `.py` script) — re-running it re-hits the live CDS API.
  **Not re-executed this session** for that reason; verified indirectly instead by loading
  the pipeline's actual output (`Texas_hourly_temp_2021_2025.csv`, produced by the sibling
  script) and re-running its validation checks fresh: 43,824 rows, full hourly coverage
  2021-01-01–2025-12-31, 0 nulls/dupes, temp range 7–104°F — **PASS 2026-07-24** (data
  re-verified; retrieval cells not re-run).
- ⚠️ Output `datetime` is **UTC**, not this repo's HE-Central convention — confirmed via
  diurnal profile (peak at raw hour 21, trough at hour 11–12, a ~6h shift from expected
  local peak/trough). Not fixed — see [[weather-hdd-cdd]], [[feature-engineering]].

### 04_ercot_7d_load_fcast_by_wzn_endpoint_check   [check · template · stable]
- **Purpose:** Endpoint check for **NP3-561-CD** (Seven-Day Load Forecast by Weather Zone) and,
  as of 2026-07-22, the **canonical template** for a new ERCOT API endpoint check — the
  worked example the [[data-extraction-guide]] and the extractor-gating hook point to. Six
  cells demonstrate the full live+archive pattern: (1) live coverage probe (0 records for Aug
  2023 → archive required) + field schema; (2) archive list (`docId → postDatetime`) for a
  one-delivery-day window; (3) **timed one-day sample extraction** (delivery 2023-08-15, all
  postings, chunked `POST /download` at 50, nested unzip, `postedDatetime` injected); (4)
  runtime extrapolation → Method B vs C.
- **In:** Public API (live `np3-561-cd/7d_load_fcast_by_wzn` + archive `NP3-561-CD`). **Out:**
  none (inspection only). **Methods:** requests, zipfile, pandas. **Wiki:**
  [[data-extraction-guide]], [[ercot-data-products]], [[mid-term-load-forecast]]
- Requires `.env` credentials. Fed directly into the production extractor
  `ercot_7d_load_fcast_wzn_archive.py` ([[extraction-scripts]]) — the notebook's
  `list_docs`/`download_batch`/`process_zip`/`parse_csv` helpers are the ones the script ships.
- Surfaced two archive quirks now in [[data-extraction-guide]] pitfalls #13/#14 (case-sensitive +
  50-doc-capped `POST /download`; `postedDatetime` not in the CSV).
- **Last run: 2026-07-22 — PASS** (fresh `nbconvert --execute`, 0 errors; one-day sample = 216
  postings downloaded/parsed in 9.5 s → 4,608 rows, 24/24 delivery-hours, 0 nulls).

## 01_eda — single-source clean + explore
### 00_rtm_price_eda   [eda · stable]
- **Purpose:** Clean & aggregate RTM SPP; produce the canonical RTM price series.
- **In:** `dam_lzhb_spp_2021_2025.parquet` (1.2_raw_api). **Out:** `ercot_rtm_prices_by_settlement_2021_2025.csv`,
  `rtm_price_aggregated_2021_2025.csv` (2_cleaned/rtm_price). **Methods:** duckdb, groupby. **Wiki:** [[rtm-dam]], [[price-volatility]]
- **Last run: 2026-07-03 — PASS** (fresh `nbconvert --execute`).

### 01_load_eda   [eda · stable]
- **Purpose:** Actual-load EDA; North-zone time series.
- **In:** `load_fzn_...parquet` (1.2). **Out:** `load_by_LZ_...parquet`, `total_load_...csv` (2_cleaned/load).
- **Methods:** duckdb, rolling. **Wiki:** [[load-and-demand]]
- **Last run: 2026-07-03 — PASS.**

### 02_mtlf_eda   [eda · stable]
- **Purpose:** Mid-term load forecast across 8 weather zones + system total (actual/forecast/error).
- **In:** `mid_term_load_forecast_...parquet` (2_cleaned/load/forecast). **Out:** WZ actual/error CSVs +
  `Hourly ERCOT system load and prediction`. **Methods:** duckdb, groupby. **Wiki:** [[mid-term-load-forecast]]
- **Last run: 2026-07-03 — PASS.**

### 03_ng_price_correlation   [eda · stable]
- **Purpose:** NG-internal correlation (Henry Hub / citygate / electric-power), monthly.
- **In:** raw NG `.xls` (Henry Hub, citygate, electric power), `1.3_raw_other/ng_price/`.
  **Out:** `ng_prices_monthly.csv` → `3_analysis/ng_price/`; **new (2026-07-17,
  uncommitted):** `henry hub ng price.csv` → new `2_cleaned/ng_price/` (`MID_DIR`).
- **Methods:** resample, scatter_corr (pearson/spearman/kendall). **Wiki:** [[natural-gas-prices]]
- Fixed 2026-07-02: raw NG `.xls` copied into `1.3_raw_other/ng_price/`; output repointed from
  the raw dir to `3_analysis/ng_price/` (`OUT_DIR` added) so `01_ng_rtm_price_correlation` finds it.
- ✅ **Fixed 2026-07-17 (human):** the Henry-Hub date-windowing found earlier the same session
  (`henry_hub` sliced to 2021-2025) has been reverted — Henry Hub is back to using its full
  raw range. A separate, genuine bug was fixed alongside it: the `ng_price_timeseries.png`
  "Saved →" message pointed at a stale path from the old repo
  (`.../RESEARCH-PJM-ERCOT-Price-Volatility/...`), now correctly resolves under
  `01_data/3_analysis/ng_price/`.
- ⚠️ **Independent of the windowing fix — still open:** re-running with the full range
  restored (`merged`: 2002-2026, 289 months) **still does not reproduce the 2023-08 NG
  deviation** recorded in [[natural-gas-prices]] / [[analysis/ng-hub-correlation-breaks-uri-aug2023]]
  (only 2021-02/Uri flags for citygate; 2021-02 + 2021-12 for elec-power). So the Aug-2023
  finding's non-reproducibility was **not** caused by the windowing bug — the fixed-coefficient
  outlier rule (`citygate >= 2*0.84*henry_hub + 1.72`, `elec_pwr >= 2*0.94*henry_hub + 0.48`)
  simply doesn't flag that month under either window. Contradiction left open; see
  [[natural-gas-prices]].
- **Last run: 2026-07-17 — PASS** (fresh `nbconvert --execute`, 0 errors, after the human's
  fix; full 2002-2026 range confirmed).

### 04_price_adders_pre2025_cleaning   [eda · stable]
- **Purpose:** Clean pre-2025 adders → 15-min, hourly, and binary-activation series.
- **In:** `rtm_price_adders_15min_20200101_20251231.parquet` (1.2). **Out:** `price_adders_{15min,hourly,binary}_...csv`
  (2_cleaned/price_adders). **Methods:** duckdb aggregate. **Wiki:** [[ordc-price-adders]]
- **Last run: 2026-07-03 — PASS.**

### 05_price_adder_distribution   [eda · stable]
- **Purpose:** Pre-2025 adder value distribution (log scale).
- **In:** `2_cleaned/price_adders/price_adders_hourly_20200101_20251204.csv` (rename `datetime`→`date`).
  **Out:** `price_adders_numerical_analysis.csv`, figures.
- **Methods:** seaborn. **Wiki:** [[ordc-price-adders]]
- Fixed 2026-07-03: input path pointed at a nonexistent `3_analysis/.../rtm_price_adders_hourly.csv`
  (never produced by any script), so this notebook never actually ran and its output
  (`price_adders_numerical_analysis.csv`, consumed by `04_price_adder_rtm_load_correlation`) was
  missing. Repointed to the real cleaned file.
- **Last run: 2026-07-03 — PASS** (after fix; re-executed `--inplace`, output file regenerated).

### 06_new_pa_cleaning   [eda · stable]
- **Purpose:** Validate & aggregate post-2025 (RTC+B) ancillary adders (`RTRDPA/RU/RD/RRS/ECRS/NS`).
- **In:** `rtm_price_adders_15min_20251205_20260517.parquet` (1.2). **Out:** `post_202512_price_adders_hourly.csv` + `_binary.csv`.
- **Methods:** duckdb. **Wiki:** [[rtc-b-asdc]]
- **Last run: 2026-07-03 — PASS.**

### 07_new_pa_distribution   [eda · stable]
- **Purpose:** Post-2025 adder value distribution.
- **In:** `post_202512_price_adders_hourly.csv`, `rtm_price_mean_...csv`. **Out:** figures.
- **Methods:** seaborn, OLS. **Wiki:** [[rtc-b-asdc]]
- **Last run: 2026-07-03 — PASS.**

### 08_hdd_eda   [eda · stable]
- **Purpose:** Texas HDD/CDD vs load (and price) over the year.
- **In:** `total_load.csv`, `rtm_price_aggregated.csv`, `Texas_..._daily_HDD_CDD.parquet` (2_cleaned).
- **Out:** `Daily_HDD_rtm_load_2021_2025.csv`. **Methods:** merge, resample. **Wiki:** [[weather-hdd-cdd]]
- Corrected 2026-07-07: on-disk filename is `08_hdd_eda.ipynb` (no `_wip` suffix); wiki
  previously carried a stale `08_hdd_eda_wip` name/status with no corresponding file.
- **Last run: 2026-07-03 — PASS.**

### 09_mtlf_models_eda   — **deleted 2026-07-24**
- Alt-forecast-model EDA notebook (companion to `02_mtlf_eda`; 7 extra ERCOT models
  A3/A6/E/E1/E2/E3/M). Deleted in this session's working tree (uncommitted). **Reason
  (human, confirmed 2026-07-24): a different data source will be used for this** — a planned
  replacement, not yet built; not simply dropped. Its ensemble-mean feature had already been
  dropped 2026-07-09 (see the prior entry, now superseded). See [[feature-engineering]],
  [[mid-term-load-forecast]].

## 02_analysis — multi-source interactions
### 00_load_forecast_rtm_correlation   [analysis · stable]
- **Purpose:** Load-forecast error vs RTM price. Finding: **log(price) vs forecast error →
  weak**.
- **In:** `Hourly ERCOT system load and prediction.csv`, `rtm_price_aggregated.csv`.
- **Methods:** merge, resample, scatter. **Wiki:** [[mid-term-load-forecast]], [[load-and-demand]]
- **Renamed 2026-07-23** — file dropped its `_wip` suffix (`00_load_forecast_rtm_correlation_wip.ipynb`
  deleted, `00_load_forecast_rtm_correlation.ipynb` added, same slot). No content changes found
  beyond the 2026-07-17 fix already recorded (this entry) — promoting `wip`→`stable` since the
  filename itself signals it's no longer WIP and a fresh run confirms it.
- ⚠️→✅ **Regression found and fixed 2026-07-17:** a 2026-07-14 edit (commit `eace499`)
  had dropped `df.set_index('datetime', inplace=True)`, leaving `df` with a plain `RangeIndex`
  (columns `avg_rtm_price, datetime, actual_load, load_forecast_error, abs_load_error`); a
  later cell facetted plots by `df.index.year`, which raised `AttributeError`. **Fixed by the
  human same-day**: the year-facet cell now reads `df['datetime'].dt.year` directly instead of
  `df.index.year` (keeps `datetime` as a column rather than restoring the index).
- **Last run: 2026-07-24 — PASS** (fresh `nbconvert --execute`, 0 errors, re-verified after
  the rename).

### 00.0_load_fcast_wzn_aug2023   [analysis · developing]
- **Purpose:** Visual-check EDA for the NP3-561-CD (Seven-Day Load Forecast by Weather Zone)
  Aug-2023 pull — the notebook explicitly left for the human when the pipeline was built
  2026-07-22 ([[notebook-catalog|see extraction-scripts/ercot-data-products]]). Computes
  forecast **lead time** per posting (`day_diff×24 + posted_hr − delivery_hr` style logic via
  duckdb), plots the 3/6/24h-ahead predicted-load series, then merges with actual load + RTM
  price to look at forecast error vs price/hour, including an "extreme price" (`avg_rtm_price
  > 100`) slice binned by lead time × hour-of-day.
- **In:** `1.2_raw_api/load_fcast_wzn_archive_20230801_20230831.parquet`,
  `2_cleaned/load/total_load_20201231_20260526.csv`,
  `2_cleaned/rtm_price/rtm_price_aggregated_2021_2025.csv`. **Out:** none written (plots only).
  **Methods:** duckdb (lead-time calc), pandas merge, matplotlib. **Wiki:**
  [[mid-term-load-forecast]], [[ercot-data-products]]
- No markdown conclusion cell — the notebook is exploratory (mean/median forecast error by
  lead-time × hour varies widely, $0$–$800$+ MW, no monotonic lead-time trend evident from the
  output alone). **Not filed as an `analysis/` finding this session** — the notebook doesn't
  state a conclusion crisp enough to file without over-interpreting; flagged as a judgment
  call rather than writing one in.
- **Last run: 2026-07-24 — PASS** (fresh `nbconvert --execute`, 0 errors).

### 01_ng_rtm_price_correlation   [analysis · stable]
- **Purpose:** NG vs RTM price, incl. dedicated **Feb-2021 (Uri)** analysis.
- **In:** `ng_prices_monthly.csv`, `rtm_price_aggregated.csv`. **Methods:** resample, scatter_corr. **Wiki:** [[natural-gas-prices]], [[price-volatility]]
- Fixed 2026-07-03 (human): rename no-op corrected so the Henry-Hub-vs-RTM cells use the real
  `avg_rtm_price` column instead of a never-populated `rtm_price`.
- **Last run: 2026-07-03 — PASS** (re-executed `--inplace` after the human's fix).

### 02_price_adder_activation   [analysis · stable]
- **Purpose:** Pre-2025 adder activation % by RTM price quantile.
- **In:** `price_adders_hourly_20200101_20251204.csv` (has column `datetime`, not `date`),
  `rtm_price_aggregated_2021_2025.csv` (pre-aggregated `avg_rtm_price`, no per-LZ/HB groupby
  needed). **Out:** `price_adders_activation_analysis.csv` (3_analysis/price_adders_analysis).
- **Methods:** quantile bins, groupby, merge. **Wiki:** [[ordc-price-adders]]
- Fixed 2026-07-03: human had accidentally deleted the RTM-price load/spike/merge cells while
  editing; restored and streamlined into one spike-flagging cell, plus fixed two latent bugs
  found in the process: (1) `df_price_spike = df_price_spike.groupby(...)` referenced itself
  before assignment — now built from `df_price_rtm`, renamed `avg_rtm_price`→`price` directly
  (no groupby needed, the file is already system-wide-averaged); (2) `if_adder` and the merge
  both assumed a `date` column on `df_price_adders`, but the real column is `datetime` — this
  silently made `if_adder` always `True` (the datetime column leaked into `.any(axis=1)`) and
  would have KeyError'd the merge once it was reached. Confirmed the declared output
  (`price_adders_activation_analysis.csv`) now exists on disk for the first time.
- Fixed 2026-07-03 (2nd pass, human-spotted): `activation_rate_table`/`baseline` were computed
  as the mean **dollar value** of each adder per price bin (unbounded — RTRDP alone reaches
  ~$9000/MWh), then ×100 as if already a 0–1 fraction, instead of the mean of a binary
  "was this adder active" flag. Added `{col}_active` boolean columns and rewired both tables
  to use them; rates now correctly bounded in [0,100]% (top price-quantile bin: ~85% Adder Sum
  activation, was previously ~161,000%). `03_new_pa_activation` (the post-2025 counterpart)
  was audited the same day — bug **not present** there (see its entry below).
- **Last run: 2026-07-03 — PASS** (re-executed `--inplace`, output + scaling fix confirmed).

### 03_new_pa_activation   [analysis · stable]
- **Purpose:** Post-2025 ancillary-adder activation by price quantile.
- **In:** `post_202512_price_adders_hourly_binary.csv`, `rtm_lzhb_spp_20251205_20260516.parquet` (1.2).
- **Out:** `rtm_price_mean_...csv`, activation csv. **Methods:** quantile bins. **Wiki:** [[rtc-b-asdc]]
- Audited 2026-07-03 for the same activation-rate scaling bug found in `02_price_adder_activation`
  (mean-of-dollar-value × 100 instead of mean-of-binary-flag). **Not present here** — this
  notebook's source file is genuinely binarized upstream in `06_new_pa_cleaning` (`(col > 0)
  .astype(int)`, confirmed 0/1-only in both the raw hourly frame and this notebook's input),
  so `.mean() × 100` correctly yields a bounded [0,100]% rate. Verified against the prior label:
  before this audit the notebook's stored execution counts were **non-sequential** (76–78
  sandwiched between 101–108), which under the status-label rule above means the earlier "PASS"
  hadn't actually been earned by a fresh top-to-bottom run — re-executed now, exec counts 1–11,
  0 errors, output values confirmed bounded [0,1] pre-scaling.
- ✅ **Finding, confirmed (human) 2026-07-03:** `RTRDPNS` is active in **100% of hours** (0
  zero-hours out of 3,911, the entire Dec-2025–May-2026 window) — every other adder has a real
  zero-rate (`RTRDPA` 84%, `RTRDPRU` 8%, `RTRDPRD` 3%, `RTRDPRRS` 4%, `RTRDPECRS` 4%). This is
  a genuine RTC+B system characteristic (Non-Spin is exhausted first in the reserve fill order,
  so it prices in nearly every interval), not a parsing artifact. Recorded in [[rtc-b-asdc]].
- **Last run: 2026-07-03 — PASS** (re-executed `--inplace`).

### 04_price_adder_rtm_load_correlation   [analysis · stable]
- **Purpose:** Adder ↔ RTM ↔ load correlations, **both regimes** (largest notebook, 27 cells).
  Pre/post-Dec-2025 datasets are read, cleaned, and merged **separately** (different adder
  schema — see [[ordc-price-adders]]) and never concatenated; only plotted side-by-side.
- **In:** `2_cleaned/rtm_price/rtm_price_aggregated_2021_2025.csv` (pre; rename `avg_rtm_price`→`rtm_price`),
  `price_adders_numerical_analysis.csv` (pre), `post_202512_price_adders_hourly.csv` (post),
  `2_cleaned/load/load_by_LZ_20201231_20260526.parquet`. **Out:** `pre2025_merged_data.csv`,
  `adder_abnormal_pre2025_no_uri.csv`.
- **Methods:** merge, corr, scatter. **Wiki:** [[ordc-price-adders]], [[load-and-demand]]
- Fixed 2026-07-03: `pre_2025_rtm_price.csv` was never produced by any script/notebook (stale
  reference, not "not-yet-run upstream" as previously noted below); repointed to the actual
  cleaned RTM price file and fixed a no-op column rename (`price`→`rtm_price` when the real
  column was `avg_rtm_price`). Load path already matched the on-disk file
  (`load_by_LZ_20201231_20260526.parquet`) — the "gap" noted below was stale.
- **Last run: 2026-07-03 — PASS** (after fix; re-executed `--inplace`).

### 05_load_rtm_price_plot   [analysis · stable]
- **Purpose:** RTM price vs load, faceted by year.
- **In:** `total_load.csv`, `rtm_price_aggregated.csv` (2_cleaned). **Methods:** groupby, merge, scatter. **Wiki:** [[load-and-demand]], [[price-volatility]]
- **Last run: 2026-07-03 — PASS.**

### 06_spare_capacity   [analysis · stable]
- **Purpose:** Replaces `06_metric_nonvariable_load_capacity` (deleted 2026-07-14, commit
  `eace499`; same catalog slot). Builds the same load-vs-firm-capacity metric — renamed
  `spare_capacity` / `metric1` = `(total_load − renewable_gen) / non_re_capacity` — proposed
  in [[sources/2026-07-06_weekly-meeting]] and refined in
  [[sources/2026-07-13_weekly-meeting-spare-capacity]], then plots it against
  `log(rtm_price)`: LOWESS fit faceted by year (Uri points excluded), scatter faceted by year,
  monthly time series, and scatter color-coded by natural-gas price (log) and by degree days.
- **In:** `2_cleaned/generation/hourly_solar_wind_generation_2020_2025.parquet`,
  `2_cleaned/load/total_load_20201231_20260526.csv`,
  `2_cleaned/generation/ERCOT nonRE capacity 2020-2025.csv`,
  `2_cleaned/rtm_price/rtm_price_aggregated_2021_2025.csv`,
  `3_analysis/ng_price/ng_prices_monthly.csv`,
  `2_cleaned/weather/Texas_hourly_temp_2021_2025.csv` (**corrected 2026-07-24** — this entry
  previously listed the old daily GRIDMET file; the notebook has read the ERA5 hourly file
  since 2026-07-21). **Out:** none written (pure EDA/plotting notebook — no
  `.to_csv`/`.to_parquet` calls). **Methods:** duckdb (window functions), statsmodels LOWESS.
  **Wiki:** [[feature-engineering]], [[analysis/spare-capacity-correlates-with-rtm-price]]
- Fixes the bug that killed the old notebook: the incomplete
  `AVG(...) OVER (PARTITION BY )` window-function SQL is gone from this rewrite.
- ⚠️ `01_data/3_analysis/price incentive metrics/merged_gen_load_price_capacity.csv` — the
  leftover file flagged 2026-07-10 as unreproducible from any cell in the deleted notebook —
  is still on disk, still not written by anything in `06_spare_capacity` either. Still not
  deleted; still flagged, now against this notebook instead.
- ✅ **`degree_days` UTC/Central misalignment fixed 2026-07-24:** added a UTC→
  `America/Chicago` conversion (+ DST fold averaging) right after loading `TEMP_PATH`, before
  the duckdb join — the raw ERA5 files stay UTC/untouched per the human's instruction. See
  [[weather-hdd-cdd]], [[feature-engineering]].
- **Last run: 2026-07-24 — PASS** (fresh `nbconvert --execute`, 0 errors, after the timezone
  fix; previously verified 2026-07-17 after installing `statsmodels`).
- Finding filed: [[analysis/spare-capacity-correlates-with-rtm-price]].

### 07_pa_vs_spp   [analysis · developing]
- **Purpose:** Tests whether the ORDC price adder (PA) ever exceeds the RTM settlement point
  price (SPP), pre- and post-2025. Merges HE-hourly adders with the corrected real-RTM SPP on the
  raw HE timestamp (no shift).
- **In:** `3_analysis/price_adders_analysis/price_adders_numerical_analysis.csv`,
  `3_analysis/price_adders_analysis/post_202512/post_202512_price_adders_hourly.csv`,
  `2_cleaned/rtm_price/rtm_price_aggregated_2021_2025.csv`,
  `3_analysis/price_adders_analysis/post_202512/rtm_price_mean_20251205_20260516.csv`.
  **Out:** `3_analysis/price_adders_analysis/pa_vs_spp/` (`pa_gt_spp_exceptions.csv` + 2 PNGs).
  **Methods:** pandas merge, 1:1-line scatter. **Wiki:** [[ordc-price-adders]], [[lmp-spp]],
  [[analysis/pa-stays-below-spp-except-negative-price-hours]].
- **Last run: 2026-07-23 — PASS** (`nbconvert --execute`, 0 errors).
- Finding filed: [[analysis/pa-stays-below-spp-except-negative-price-hours]].

## 03_model — modeling on top of 02_analysis outputs
### 01_regression_data.ipynb   [model · stable]  (renamed 2026-07-21 from `01_regression.ipynb`)
- **Purpose (rebuilt 2026-07-21, per [[sources/2026-07-20_meeting-notes]]):** builds and
  exports the merged modeling dataset, now via duckdb (was pandas), with two new columns —
  `time_of_day` and `total_load` — and the ERA5 **hourly** temperature feed (was the old daily
  GRIDMET file). Still fits no model itself (titled "linear regression model dataset"); the
  fit moved to a companion R script, `ERCOT regression.Rmd` (see below). Also gained 3
  correlation-plot cells (scatter by year, overall Pearson matrix, per-year Pearson matrices).
- **In:** `2_cleaned/generation/hourly_solar_wind_generation_2020_2025.parquet`,
  `2_cleaned/load/total_load_20201231_20260526.csv`,
  `2_cleaned/generation/ERCOT nonRE capacity 2020-2025.csv`,
  `2_cleaned/rtm_price/rtm_price_aggregated_2021_2025.csv`,
  `3_analysis/ng_price/ng_prices_monthly.csv`,
  `2_cleaned/weather/Texas_hourly_temp_2021_2025.csv` (**changed from the daily GRIDMET file**).
  **Out:** `01_data/4_model/ercot_regression_model_dataset.csv` — 9 cols now
  (`datetime, year, time_of_day, season, rtm_price, total_load, spare_capacity, ng_price,
  degree_days`), 43,534 rows, 1 null row (`spare_capacity`/`ng_price`/`degree_days`), Uri
  window excluded via SQL `WHERE`. **Methods:** duckdb merge, pandas/matplotlib correlation
  plots. **Wiki:** [[feature-engineering]],
  [[analysis/spare-capacity-correlates-with-rtm-price]]
- ✅ **`OUT_DIR.mkdir()` non-idempotency issue (flagged 2026-07-17) resolved:** the `.mkdir()`
  call is gone from the current notebook (the directory is now permanent) — no longer blocks
  a clean re-run.
- **Companion R script, `03_notebooks/03_model/ERCOT regression.Rmd`** (new, not part of the
  `nbconvert`-checked notebook set): reads `ercot_regression_model_dataset.csv`, correlation
  matrices (overall + per-year), and fits `mod1 <- lm(rtm_price ~ spare_capacity + ng_price +
  degree_days + factor(year) + factor(season) + time_of_day, df)` + `vif(mod1)`. **Not
  executed this session** — no R runtime in the sandbox, no knitted HTML/output on disk to
  check against; its formula and presence are confirmed from source only.
- Historical Python modeling results (from the version of this notebook that existed before
  the 2026-07-17 human edit — **not reproducible from the current code**, kept for
  provenance): OLS R²=0.552, `spare_capacity` coef ≈+115 (p<0.001), `ng_price` coef ≈+6.3
  (p<0.001), `degree_days` coef ≈−0.44 (p<0.001), `year` not significant; sklearn
  `LinearRegression` R²=0.40; Random Forest failed (continuous target via `accuracy_score`).
- ✅ **`degree_days` UTC/Central misalignment fixed 2026-07-24** — added a UTC→
  `America/Chicago` conversion (+ DST fold averaging) right after `df_temp = pd.read_csv(TEMP_PATH)`,
  before the duckdb join. The raw ERA5 scraper/files are untouched (stay UTC, per the human's
  instruction not to re-touch already-scraped data) — the fix lives here, at the point of
  use. Null rows in `degree_days` went from 1 → 9 (DST-edge join misses, out of 43,534 rows).
  See [[weather-hdd-cdd]], [[feature-engineering]]. `mod1` (the R regression) still needs a
  fresh run to pick up the corrected values.
- **Last run: 2026-07-24 — PASS** (fresh `nbconvert --execute`, 0 errors, after the timezone
  fix; `time_of_day`/`total_load` columns and the corrected `degree_days` confirmed in the
  output CSV).

---

## Path patching — ⚠️ revise as of 2026-07-03
The 2026-07-01 verification claimed **0 legacy paths in any executable code cell** and that
missing eda↔analysis intermediates were "not a defect, produced by upstream notebooks." Actual
end-to-end execution on 2026-07-03 found that claim wrong for two notebooks:
- `05_price_adder_distribution` had a dead input path (`rtm_price_adders_hourly.csv`, never
  produced by anything) — so it never ran, so its declared output
  (`price_adders_numerical_analysis.csv`) never existed either.
- `04_price_adder_rtm_load_correlation` referenced `pre_2025_rtm_price.csv`, which **no script
  or notebook in the repo ever produces** — not a run-order issue, a genuinely missing
  provenance link. Repointed to `2_cleaned/rtm_price/rtm_price_aggregated_2021_2025.csv`
  instead (fixes it, but narrows pre-2025 RTM-price coverage to 2021–2025; 2020 adders data
  gets dropped by the inner join — flagged for the human to confirm this is acceptable).
Both now execute cleanly (see per-notebook notes above). Six notebooks still mention old
`data/…` paths in markdown/comments only — cosmetic, optional cleanup. Take "verified" claims
in this section as no longer trustworthy until each notebook is re-run and re-confirmed.

## Remaining gaps — data availability (not paths)
- ~~**NG chain.** `03_ng_price_correlation` needs raw NG `.xls`... needs a provenance
  decision~~ — resolved 2026-07-02: raw `.xls` copied to `1.3_raw_other/ng_price/`;
  `03_ng_price_correlation` now writes `ng_prices_monthly.csv` to `3_analysis/ng_price/`,
  matching where `01_ng_rtm_price_correlation` reads it. (Henry Hub / citygate / Waha remain
  manual-download `.xls` only — no live NG scraper yet; that part is still open, see
  [[natural-gas-prices]], [[extraction-scripts]].)
- ~~`04_price_adder_rtm_load_correlation` expects `ercot_LZ_load_hourly.parquet`~~ — resolved;
  notebook's code cell already used the correct on-disk name
  (`load_by_LZ_20201231_20260526.parquet`); only a stale markdown comment referenced the old name.
- ~~Two notebooks are currently `[**broken**]` for non-path reasons: `01_ng_rtm_price_correlation`,
  `02_price_adder_activation`~~ — both fixed and re-verified 2026-07-03 (human); see their
  entries above for the exact bugs and fixes. Only remaining non-path issue: `00_emil_api_check`
  is `blocked` (missing live-API credentials, not a code bug — see its entry).

## Related
- [[extraction-scripts]] · [[analysis-workflow]] · [[data-extraction-guide]]
