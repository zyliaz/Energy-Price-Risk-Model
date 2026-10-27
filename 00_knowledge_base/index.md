---
title: Index
type: overview
updated: 2026-10-16
---

# Wiki Index

Catalog of every page. Read this first when answering a query, then drill into pages.
Update on every ingest.

Two knowledge tracks: **Market knowledge** (`concepts/`) — how the ERCOT market works;
**Engineering** (`engineering/`) — how we get and process the data.

## Start here
- [[00_overview]] — research question, evolving thesis.
- [[scope-and-history]] — how the topic narrowed from ERCOT-vs-PJM to ERCOT-only, and why (PJM capacity-price surge pushing investors toward energy-only markets).

## Entities
- [[ercot]] — the ISO and its market design.
- [[ercot-data-products]] — datasets, report IDs, extraction code map. NP3-233-CD: use
  `totalResourceMW` for full-period series (zone cols NaN before 2021-05-27 17:01); archive
  reaches back to 2014-05 (unextracted); live parquet kept for validation; one all-zero
  source posting (2024-07-23 16:00) to drop.
- [[puct]] — regulator; offer caps & ORDC parameters.
- [[eia]] — natural-gas data source (Henry Hub, TX Citygate; Waha removed 2026-07-03).

## Market knowledge — core pricing
- [[price-volatility]] — the dependent variable; how it's measured.
- [[ordc-price-adders]] — scarcity adders (ORDC, pre-Dec-2025); suspected dominant driver.
- [[rtc-b-asdc]] — Dec 2025 regime change: co-optimized adders / ASDC.
- [[lmp-spp]] — price decomposition (SPP = LMP + adders).
- [[ancillary-services]] — reserve products; carry scarcity value under RTC+B.
- [[energy-only-market]] — why ERCOT prices are structurally spiky.
- [[rtm-dam]] — real-time vs day-ahead markets; DAM mechanics.
- [[winter-storm-uri]] — Feb 13–17, 2021 storm (ERCOT emergency ~Feb 14–19); canonical
  extreme-scarcity outlier.

## Market knowledge — drivers
- [[load-and-demand]] — total/zonal demand and net-load ramps.
- [[wind-power-production]] — wind & solar output, forecast error, capacity factor.
- [[natural-gas-prices]] — marginal fuel cost (Henry Hub, Citygate).
- [[weather-hdd-cdd]] — temperature → load. Two sources now: **GRIDMET** (daily, per-county,
  legacy, still used by `08_hdd_eda`) and **ERA5** (hourly, Texas-wide, added 2026-07-21 for
  modeling). ERA5 scraper **rewritten 2026-07-29** (`era5_ercot_temp.py`) — now delivers
  tz-naive CPT hour-ending timestamps directly (was UTC); DST handled (fall-back averaged,
  spring-forward gap aligned with ERCOT). The prior notebook-level UTC→CPT conversion
  (`06_spare_capacity`, `01_regression_data`, fixed 2026-07-24) is now redundant.
- [[mid-term-load-forecast]] — forecast error channel; now also carries 7 alt-model
  load-prediction features (A3/A6/E/E1/E2/E3/M — each a different weather-forecast input,
  answered 2026-07-07; EDA notebook `09_mtlf_models_eda` **deleted 2026-07-24** — a different
  data source will be used for this instead, per the human). Short-horizon forecast product:
  NP3-565-CD (day-ahead slice, extractor built, not yet EDA'd) and its sibling NP3-561-CD
  (by-weather-zone, EDA'd 2026-07-24 in `00.0_load_fcast_wzn_aug2023`, no crisp finding filed
  yet — human plans to file one next week).
- [[load-zones]] — **all zone geographies** (LZ / weather zones / forecast zones / wind-solar regions; aliased as weather-zones, forecast-zones): mapping-file inventory (LZ→county canonical in ercot.gpkg; weather-zone→county missing), parquet schemas per geography, join caveats.

## Engineering (pipeline & methods, in `engineering/`)
- [[new-source-checklist]] — compressed copy-paste todo for adding a data source.
- [[data-extraction-guide]] — API auth, endpoints, pitfalls, timeouts, EMIL, jobs convention.
- [[extraction-scripts]] — script architecture: 10 ERCOT API extractors (incl. the
  NP3-233-CD outage-capacity pair from 2026-09-19, superseded 2026-09-24 by the
  full-range archive extractor `ercot_outage_cap_archive_full`, 2021→present; full pull
  landed 2026-09-24, 9.54M rows / 50,202 postings)
  vs excel→parquet parsers, plus a non-ERCOT-scraper grouping (`era5_ercot_temp.py`,
  rewritten 2026-07-29 with CPT-aligned timestamps — replaces the old UTC-only
  `era5_ercot_temp_2021-2025.py`).
- [[analysis-workflow]] — 5-step raw→cleaned→analysis pipeline mapped to the repo + lineage.
- [[feature-engineering]] — adder demand, CDD/HDD, capacity factor, net load, spare-capacity ratio.
- [[notebook-catalog]] — architecture of the `00_check`/`01_eda`/`02_analysis`/`03_model`
  notebooks (I/O, patterns) + template. `00_check/` now includes NP3-233-CD endpoint check
  (`05`) and Uri forecast drift analysis (`06`). `01_eda/` gained `09_outage_eda`
  (NP3-233-CD → 1h-ahead hourly `outage_MW`, 50,219 h, in `2_cleaned/outage/`) and
  `09.1_outage_live_archive_comparison` (wip). `03_model/` has 4 files: `01_regression_data`
  (data prep v1), `02_linear_regression.Rmd` (v1 model), `03_v2_data_prep` (data prep v2,
  decomposes price into base energy + per-component adders), `04_v2_decomposed_model.Rmd`
  (v2: 7-submodel decomposed price model — base OLS + 3×hurdle for ORDC adders). Tracks 3 open gaps: no
  WPP EDA, no RTM-vs-DAM comparison,
  no node→zone cleaning notebook (all dropped, not renamed, during the old→new repo
  migration). Every entry carries a `Last run` execution stamp. `00_emil_api_check` deleted
  2026-07-08, superseded by `00_endpoint_check_template` (not yet re-run since its 2026-07-08
  rewrite). **2026-07-14:**
  `06_metric_nonvariable_load_capacity` (broken) deleted, replaced by `06_spare_capacity`
  (passing) — see [[analysis/spare-capacity-correlates-with-rtm-price]].
  **2026-07-17:** `00_load_forecast_rtm_correlation_wip` found broken (dropped `set_index`
  call), **fixed same day** — passing again. `03_ng_price_correlation`'s Henry-Hub
  date-windowing bug fixed same day, but the Aug-2023 NG-deviation finding still doesn't
  reproduce for an unrelated reason — see [[natural-gas-prices]].
  **2026-07-22:** new `00_check/04_ercot_7d_load_fcast_by_wzn_endpoint_check` (NP3-561-CD) —
  PASS, and now the **canonical ERCOT endpoint-check template**; feeds the new
  `ercot_7d_load_fcast_wzn_archive` extractor (Aug 2023 pulled). A PreToolUse hook now gates new
  extractors on a matching `00_check` notebook.
  **2026-10-16:** new `01_eda/10_renewable_gen_eda` (wip; price × renewable gen × load merge, plots only, not re-run); `05_load_rtm_price_plot` edited 2026-10-14 (not re-run).
  **2026-07-24 (sync — mostly uncommitted repo drift from 2026-07-21–23):** new
  `00_check/02_era5_ercot_temp` (hourly ERA5 Texas temperature, native UTC timestamps,
  credentials present); `00_load_forecast_rtm_correlation_wip` renamed →
  `00_load_forecast_rtm_correlation` (promoted `wip`→`stable`); new
  `02_analysis/00.0_load_fcast_wzn_aug2023` (NP3-561-CD lead-time EDA, fills the 2026-07-22
  gap, no crisp finding filed yet — human will file one next week); `09_mtlf_models_eda`
  **deleted** (a different data source will be used, per the human); `03_model/01_regression.ipynb`
  renamed → `01_regression_data.ipynb`, promoted `wip`→`stable` (the `OUT_DIR.mkdir()` issue is
  resolved), gained `time_of_day`/`total_load` columns and an hourly (ERA5) degree-days feed —
  its UTC-vs-Central misalignment was found **and fixed same session** (conversion added in
  `06_spare_capacity`/`01_regression_data` at the point of use, scraper/raw files untouched
  per the human's instruction); modeling itself moved to a new, unverified companion R script
  (`ERCOT regression.Rmd`). All notebooks re-verified via fresh `nbconvert --execute` this
  session except the live-CDS-API cell in `02_era5_ercot_temp` (not re-run; data verified from
  its actual output instead — see [[notebook-catalog]]).

## Sources
- [[sources/2026-06-30_ercot-market-concepts]] — pricing mechanics (ORDC/ASDC, LMP/SPP, ancillary).
- [[sources/2026-06-30_data-and-eda-notes]] — data sources, mappings, features, EDA findings.
- [[sources/2026-06-30_ercot-data-extraction-skill]] — extraction playbook + pitfalls (from old repo).
- [[sources/2026-07-01_research-meeting]] — advisor meeting: net-load direction, seasonality, deliverables.
- [[sources/2026-07-01_kickoff-project-tracker]] — PM kickoff: Notion ↔ repo bridge via `Related Area`.
- [[sources/2026-07-03_analysis-summary]] — progress note: NG-correlation 2nd deviation (Aug 2023),
  refined monthly seasonality, sharpened MTLF over-prediction puzzle, weather/population findings.
- [[sources/2026-07-06_weekly-meeting]] — working session: MTLF model-heading question,
  stakeholder-metric proposals (planning only), non-renewable capacity source decision.
- [[sources/2026-07-07_research-update]] — progress note: MTLF model-heading question
  answered, NP3-565-CD + PG7-126-M report IDs identified, non-renewable-capacity coverage
  caveat (~25% thermal capacity excluded).
- [[sources/2026-07-13_weekly-meeting-spare-capacity]] — spare-capacity metric
  `(load−renewable_gen)/non_re_capacity` proposed, correlates strongly with `log(price)`.
- [[sources/2026-07-14_capacity-model-research-update]] — regression modeling plan for the
  spare-capacity metric (year + season + spare_capacity + ng_price + degree_days).
- [[sources/2026-07-20_meeting-notes]] — reframes the model's purpose as scenario
  **simulation**; specifies hourly degree-days, `time_of_day`, and an R regression; surfaces
  the degree-days/spare-capacity collinearity-via-load issue.
- [[sources/2026-07-27_modeling-strategy-update]] — modeling architecture finalized: parametric
  (not iterative) for simulation; cap_threshold feature; load-forecast-error dropped; price
  lower-tail removed; full-precision temperature; feature decisions on load/time/lasso.
- [[sources/2026-08-03_research-meeting]] — model refinement: log-10 scale loss, baseline year
  2025, binary heating/cooling variable, tail-behavior models (logistic/piecewise), feature
  decisions (drop perc_load, time-of-day fits well hours 16–21, degree-days still needed despite
  collinearity).
- [[sources/2026-09-09_modeling-next-steps-yash]] — email: prioritized modeling roadmap
  (hourly outage data, reserve margin, separate adder model, evaluation metrics, quantile
  regression, asinh transformation).
- [[sources/2026-09-16_np3-233-cd-outage-data]] — meeting note: NP3-233-CD (Hourly Resource
  Outage Capacity) data source for spare_capacity_v2; resolves Uri exclusion via supply-side
  outage tracking.
- [[sources/2026-09-30_meeting-notes]] — meeting note: outage-vs-capacity mismatch (coal), adder modeling question, poster guidance, model to-dos.

## Analysis (filed findings — one note per notebook, named by finding)
- [[analysis/ng-hub-correlation-breaks-uri-aug2023]] — NG benchmarks track monthly except
  2021-02 (Uri) and 2023-08. (`03_ng_price_correlation`)
- [[analysis/adder-activation-steepens-with-price]] — pre-2025 adder activation rises with
  RTM price quantile; RTRDP tail non-monotonic. (`02_price_adder_activation`)
- [[analysis/rtcb-activation-mirrors-ordc]] — RTC+B adders reproduce the ORDC activation
  pattern; RTRDPNS active 100% of hours. (`03_new_pa_activation`)
- [[analysis/pa-stays-below-spp-except-negative-price-hours]] — PA ≤ RTM SPP in ~99.9% of
  pre-2025 hours; all exceptions are negative-price hours. (`07_pa_vs_spp`)
- [[analysis/load-price-correlation-is-seasonal]] — log(price)–load correlation concentrates
  in months 1–2 and 5–10. (`05_load_rtm_price_plot`)
- [[analysis/mtlf-overpredicts-at-high-load-price]] — forecast error alone weak; MTLF
  over-predicts at high load + high price. (`00_load_forecast_rtm_correlation`)
- [[analysis/cooling-demand-rising-with-population]] — U-shaped temp–load; CDD side rose
  ~50% 2021→2022 with population. (`08_hdd_eda`)
- [[analysis/spare-capacity-correlates-with-rtm-price]] — `(load−renewable_gen)/
  non_re_capacity` correlates strongly with `log(rtm_price)`; OLS R²=0.552 with NG price +
  degree-days added (regression notebook uncommitted, cached results only).
  (`06_spare_capacity`, `03_model/01_regression_data`)
