---
title: Index
type: overview
updated: 2026-07-17
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
- [[ercot-data-products]] — datasets, report IDs, extraction code map.
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
- [[weather-hdd-cdd]] — temperature → load (GRIDMET; HDD/CDD).
- [[mid-term-load-forecast]] — forecast error channel; now also carries 7 alt-model
  load-prediction features (A3/A6/E/E1/E2/E3/M — each a different weather-forecast input,
  answered 2026-07-07). Planned: NP3-565-CD short-horizon (3hr/6hr/day-ahead) forecast product.
- [[load-zones]] — **all zone geographies** (LZ / weather zones / forecast zones / wind-solar regions; aliased as weather-zones, forecast-zones): mapping-file inventory (LZ→county canonical in ercot.gpkg; weather-zone→county missing), parquet schemas per geography, join caveats.

## Engineering (pipeline & methods, in `engineering/`)
- [[new-source-checklist]] — compressed copy-paste todo for adding a data source.
- [[data-extraction-guide]] — API auth, endpoints, pitfalls, timeouts, EMIL, jobs convention.
- [[extraction-scripts]] — script architecture: 7 API extractors (incl. new
  `ercot_mtlf_day_ahead`, 2026-07-14) vs excel→parquet parsers.
- [[analysis-workflow]] — 5-step raw→cleaned→analysis pipeline mapped to the repo + lineage.
- [[feature-engineering]] — adder demand, CDD/HDD, capacity factor, net load, spare-capacity ratio.
- [[notebook-catalog]] — architecture of the 19 kept `00_check`/`01_eda`/`02_analysis`
  notebooks (I/O, patterns) + template, plus `03_model/01_regression.ipynb` — the first
  notebook in a new, adopted (2026-07-17) 4th grouping for modeling. Tracks 3 open gaps: no
  WPP EDA, no RTM-vs-DAM comparison,
  no node→zone cleaning notebook (all dropped, not renamed, during the old→new repo
  migration). Every entry carries a `Last run` execution stamp. `00_emil_api_check` deleted
  2026-07-08, superseded by `00_endpoint_check_template` (not yet re-run since its 2026-07-08
  rewrite). `09_mtlf_models_eda` (alt-forecast-model EDA, added 2026-07-03): ensemble-mean
  feature added 07-03, removed in an uncommitted 07-09 edit. **2026-07-14:**
  `06_metric_nonvariable_load_capacity` (broken) deleted, replaced by `06_spare_capacity`
  (passing) — see [[analysis/spare-capacity-correlates-with-rtm-price]].
  **2026-07-17:** `00_load_forecast_rtm_correlation_wip` found broken (dropped `set_index`
  call), **fixed same day** — passing again. `03_ng_price_correlation`'s Henry-Hub
  date-windowing bug fixed same day, but the Aug-2023 NG-deviation finding still doesn't
  reproduce for an unrelated reason — see [[natural-gas-prices]]. `03_model/01_regression`
  had its Random Forest cell removed (fixed the metric bug) but the edit also removed the
  OLS/linear-regression cells — now a dataset-export step only, no model fit.

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

## Analysis (filed findings — one note per notebook, named by finding)
- [[analysis/ng-hub-correlation-breaks-uri-aug2023]] — NG benchmarks track monthly except
  2021-02 (Uri) and 2023-08. (`03_ng_price_correlation`)
- [[analysis/adder-activation-steepens-with-price]] — pre-2025 adder activation rises with
  RTM price quantile; RTRDP tail non-monotonic. (`02_price_adder_activation`)
- [[analysis/rtcb-activation-mirrors-ordc]] — RTC+B adders reproduce the ORDC activation
  pattern; RTRDPNS active 100% of hours. (`03_new_pa_activation`)
- [[analysis/load-price-correlation-is-seasonal]] — log(price)–load correlation concentrates
  in months 1–2 and 5–10. (`05_load_rtm_price_plot`)
- [[analysis/mtlf-overpredicts-at-high-load-price]] — forecast error alone weak; MTLF
  over-predicts at high load + high price. (`00_load_forecast_rtm_correlation_wip`)
- [[analysis/cooling-demand-rising-with-population]] — U-shaped temp–load; CDD side rose
  ~50% 2021→2022 with population. (`08_hdd_eda`)
- [[analysis/spare-capacity-correlates-with-rtm-price]] — `(load−renewable_gen)/
  non_re_capacity` correlates strongly with `log(rtm_price)`; OLS R²=0.552 with NG price +
  degree-days added (regression notebook uncommitted, cached results only).
  (`06_spare_capacity`, `03_model/01_regression`)
