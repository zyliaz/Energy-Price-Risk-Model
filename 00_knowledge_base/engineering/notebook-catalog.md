---
title: Notebook Catalog (architecture)
type: engineering
tags: [methods, notebooks, reference]
status: developing
sources: 0
updated: 2026-07-10
---

# Notebook Catalog (architecture)

What each **kept** notebook does and how `03_notebooks/` is organized. Companion to
[[extraction-scripts]] (the scripts) and [[analysis-workflow]] (the pipeline). Reflects the
19 notebooks in the new repo (old `00_emil`/`03`/`04`/`05` and 2 helper scripts dropped
during migration, not renamed/kept; `09_mtlf_models_eda` added 2026-07-03;
`01_wind_solar_5min_endpoint_check` added 2026-07-03;
`06_investigate_abnormal_pa_wip` + its output `merged_data.csv` dropped 2026-07-05 —
not formally tested, PA>SPP claims removed from the wiki; `06_metric_nonvariable_load_capacity`
added 2026-07-10, currently broken — see its entry).

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
  **Out:** `ng_prices_monthly.csv` → `3_analysis/ng_price/`.
- **Methods:** resample, scatter_corr (pearson/spearman/kendall). **Wiki:** [[natural-gas-prices]]
- Fixed 2026-07-02: raw NG `.xls` copied into `1.3_raw_other/ng_price/`; output repointed from
  the raw dir to `3_analysis/ng_price/` (`OUT_DIR` added) so `01_ng_rtm_price_correlation` finds it.
- **Last run: 2026-07-03 — PASS.**

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

### 09_mtlf_models_eda   [eda · stable]
- **Purpose:** Alt-forecast-model EDA (companion to `02_mtlf_eda`): the 7 extra ERCOT models
  (A3/A6/E/E1/E2/E3/M) per zone, ERCOT-total only.
- **In:** `mid_term_load_forecast_models_20220201_20251201.parquet` (1.2_raw_api). **Out:**
  `2_cleaned/load/forecast/Hourly_ERCOT_all_models_20220201_20251201.csv` (actual + selected +
  all 7 alt models, ERCOT-only, hourly) — only declared output as of the current saved
  notebook.
- **Methods:** duckdb, groupby, null/duplicate checks, plots. **Wiki:** [[mid-term-load-forecast]]
- Note: reads directly from `1.2_raw_api` (the parser's actual output location), unlike
  `02_mtlf_eda` which reads a `2_cleaned` copy of the base parser's output — that's a
  pre-existing path oddity in `02_mtlf_eda`, not fixed here (out of scope for this task).
- ⚠️ **Drift found 2026-07-10:** an uncommitted, unlogged edit (file mtime 2026-07-09) removed
  the ensemble-mean computation/export cell and the zone-sum-vs-ERCOT-total validation plots
  entirely — the notebook no longer writes `model_ensemble_features_ERCOT_*.csv`, and the
  "ensemble mean less consistent than Selected (~359 MW mean diff)" finding previously recorded
  here is **no longer reproducible from the current code** (only markdown-docstring text still
  claims the ensemble-mean output; the code doesn't). Removed the stale finding and file
  reference from this entry and from [[feature-engineering]] pending human confirmation this
  simplification (vs. an accidental partial edit) was intentional — see log.
- **Last run: 2026-07-10 — PASS** (fresh `nbconvert --execute`, 0 errors; sole declared output
  confirmed on disk).

## 02_analysis — multi-source interactions
### 00_load_forecast_rtm_correlation_wip   [analysis · wip]
- **Purpose:** Load-forecast error vs RTM price. Finding: **log(price) vs forecast error → weak**.
- **In:** `Hourly ERCOT system load and prediction.csv`, `rtm_price_aggregated.csv`.
- **Methods:** merge, resample, scatter. **Wiki:** [[mid-term-load-forecast]], [[load-and-demand]]
- **Last run: 2026-07-03 — PASS.**

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

### 06_metric_nonvariable_load_capacity   [analysis · broken]
- **Purpose:** Build the load-vs-firm-capacity price-incentive metric proposed in
  [[sources/2026-07-06_weekly-meeting]]: `(total_load − renewable_gen) / non_re_capacity`,
  plus exploratory RTM-price rolling-average/daily-spread metrics.
- **In:** `2_cleaned/generation/hourly_solar_wind_generation_2020_2025.parquet`,
  `2_cleaned/load/total_load_20201231_20260526.csv`,
  `2_cleaned/generation/ERCOT nonRE capacity 2020-2025.csv`,
  `2_cleaned/rtm_price/rtm_price_aggregated_2021_2025.csv`. **Out:** none currently written
  (see below). **Methods:** duckdb (window functions). **Wiki:** [[feature-engineering]],
  [[ercot-data-products]]
- **Last run: 2026-07-10 — FAIL.** Fresh `nbconvert --execute`: cells 1–7 pass, including the
  capacity-ratio metric (`df_metric`, joins gen+load+capacity on datetime/year, computes the
  ratio cleanly). Fails at the price-metrics cell — a DuckDB window-function SQL string has an
  incomplete `AVG(rtm_price) OVER (PARTITION BY )` clause (empty partition list) →
  `ParserException: syntax error at or near ")"`. No output file is written by any cell in the
  current saved notebook.
- ⚠️ `01_data/3_analysis/price incentive metrics/merged_gen_load_price_capacity.csv` exists on
  disk (43,294 rows, 2021-01-01–2025-12-28, columns match an earlier merge step) but predates
  this notebook's last save by ~1h20m and no cell in the current version writes it — likely
  output of an earlier edit of this same notebook, not reproducible from the code as saved.
  Not deleted; flagged for human confirmation (see log).

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
