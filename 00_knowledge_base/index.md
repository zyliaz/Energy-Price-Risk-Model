---
title: Index
type: overview
updated: 2026-07-05
---

# Wiki Index

Catalog of every page. Read this first when answering a query, then drill into pages.
Update on every ingest.

Two knowledge tracks: **Market knowledge** (`concepts/`) — how the ERCOT market works;
**Engineering** (`engineering/`) — how we get and process the data.

## Start here
- [[00_overview]] — research question, evolving thesis, open questions.
- [[scope-and-history]] — how the topic narrowed from ERCOT-vs-PJM to ERCOT-only, and why (PJM capacity-price surge pushing investors toward energy-only markets).

## Entities
- [[ercot]] — the ISO and its market design.
- [[ercot-data-products]] — datasets, report IDs, extraction code map.
- [[puct]] — regulator; offer caps & ORDC parameters.
- [[eia]] — natural-gas data source.
- [[waha-hub]] — West Texas gas hub.

## Market knowledge — core pricing
- [[price-volatility]] — the dependent variable; how it's measured.
- [[ordc-price-adders]] — scarcity adders (ORDC, pre-Dec-2025); suspected dominant driver.
- [[rtc-b-asdc]] — Dec 2025 regime change: co-optimized adders / ASDC.
- [[lmp-spp]] — price decomposition (SPP = LMP + adders).
- [[ancillary-services]] — reserve products; carry scarcity value under RTC+B.
- [[energy-only-market]] — why ERCOT prices are structurally spiky.
- [[rtm-dam]] — real-time vs day-ahead markets; DAM mechanics.

## Market knowledge — drivers
- [[load-and-demand]] — total/zonal demand and net-load ramps.
- [[wind-power-production]] — wind & solar output, forecast error, capacity factor.
- [[natural-gas-prices]] — marginal fuel cost (Henry Hub, Citygate, Waha).
- [[weather-hdd-cdd]] — temperature → load (GRIDMET; HDD/CDD).
- [[mid-term-load-forecast]] — forecast error channel; now also carries 7 alt-model
  load-prediction features (A3/A6/E/E1/E2/E3/M).
- [[data-center-demand]] — structural demand shift (hypothesis-stage).
- [[load-zones]] — **all zone geographies** (LZ / weather zones / forecast zones / wind-solar regions; aliased as weather-zones, forecast-zones): mapping-file inventory (LZ→county canonical in ercot.gpkg; weather-zone→county missing), parquet schemas per geography, join caveats.

## Engineering (pipeline & methods, in `engineering/`)
- [[new-source-checklist]] — compressed copy-paste todo for adding a data source.
- [[data-extraction-guide]] — API auth, endpoints, pitfalls, timeouts, EMIL, jobs convention.
- [[extraction-scripts]] — script architecture: 6 API extractors vs excel→parquet parsers.
- [[analysis-workflow]] — 5-step raw→cleaned→analysis pipeline mapped to the repo + lineage.
- [[feature-engineering]] — adder demand, CDD/HDD, capacity factor, net load.
- [[notebook-catalog]] — architecture of the 18 kept notebooks (I/O, patterns) + template.
  Also tracks 3 open gaps: no WPP EDA, no RTM-vs-DAM comparison, no node→zone cleaning
  notebook (all dropped, not renamed, during the old→new repo migration). Every entry now
  carries a `Last run` execution stamp (2026-07-03). All previously-broken notebooks fixed as
  of 2026-07-03 except `00_emil_api_check` (blocked on missing `.env` credentials, not a code bug).
  New 2026-07-03: `09_mtlf_models_eda`, alt-forecast-model EDA + ensemble features.

## Sources
- [[sources/2026-06-30_ercot-market-concepts]] — pricing mechanics (ORDC/ASDC, LMP/SPP, ancillary).
- [[sources/2026-06-30_data-and-eda-notes]] — data sources, mappings, features, EDA findings.
- [[sources/2026-06-30_ercot-data-extraction-skill]] — extraction playbook + pitfalls (from old repo).
- [[sources/2026-07-01_research-meeting]] — advisor meeting: net-load direction, seasonality, deliverables.
- [[sources/2026-07-01_kickoff-project-tracker]] — PM kickoff: Notion ↔ repo bridge via `Related Area`.
- [[sources/2026-07-03_analysis-summary]] — progress note: NG-correlation 2nd deviation (Aug 2023),
  refined monthly seasonality, sharpened MTLF over-prediction puzzle, weather/population findings.

## Analysis (filed findings)
- [[analysis/2026-07-03_empirical-findings-summary]] — consolidated EDA/analysis results across
  NG prices, price adders, load/forecast error, and weather as of 2026-07-03.
