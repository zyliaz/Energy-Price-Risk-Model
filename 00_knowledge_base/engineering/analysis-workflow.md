---
title: Analysis Workflow
type: engineering
tags: [methods, workflow, pipeline, reference]
status: stable
sources: 1
updated: 2026-07-17
---

# Analysis Workflow

The standard path from a raw ERCOT source to a cross-source finding, mapped to the repo. Use
it when onboarding **any new data source** so files land in the right layer and stay reusable.

## The 5 steps
inspect → extract → aggregate → analyze-single → merge-across. The step-by-step with folders
and outputs lives in the copy-paste **[[new-source-checklist]]** (single source of truth — not
duplicated here). This page covers the *why*: the layering rule and how files relate.

## What to keep at each layer (the rule)
- **`01_data/1.x_raw*`** — immutable. Never edit. Parquet from API → `1.2`; downloaded bulk
  zip/csv/xlsx → `1.1`; self-contained scrapers / imported reference → `1.3`.
- **`2_cleaned`** — csv aggregated in **time or space from a *single* source** (e.g. 5-min →
  hourly, nodes → zone, value → binary activation flag). One source in, one source out.
- **`3_analysis`** — csv that **merges multiple sources** for a relationship/finding. Figures
  may live here or stay in the old repo (project convention).
- **`4_model`** (added 2026-07-14, adopted 2026-07-17) — modeling-ready datasets exported from
  `03_notebooks/03_model` (regression/ML inputs, one step past `3_analysis`). Populated by
  `01_regression.ipynb` → `ercot_regression_model_dataset.csv`. Note: that notebook's
  `OUT_DIR.mkdir()` call is not idempotent (no `exist_ok=True`) — re-running it after the
  directory already exists fails; not yet fixed.

See [[data-extraction-guide]] for step-1/2 mechanics. Feature definitions: [[feature-engineering]].
Quick copy-paste version: [[new-source-checklist]].

## Data-file lineage (current sources)
```
NP6-346-CD load ──► load_fzn.parquet ──► total_load.csv, load_by_LZ.parquet ┐
NP6-793-ER adder ─► rtm_price_adders_15min.parquet ─► price_adders_{hourly,binary}.csv ┤
13061 RTM SPP ────► rtm_lzhb_spp.parquet ──► rtm_price_aggregated.csv ───────┼─► merged
NP4-742/745 W&S ──► wpp_geo.parquet ──► (capacity factor) ──────────────────┤   analyses
EIA NG ───────────► ng_prices_monthly.parquet ─────────────────────────────┤   (3_analysis)
GRIDMET temp ─────► Texas_..._daily_HDD_CDD.parquet ────────────────────────┘
        raw (1.2/1.3)             cleaned (2_cleaned)            analysis (3_analysis)
```
Examples of step-5 merges: adder × RTM price quantile ([[ordc-price-adders]]); load × RTM
price ([[load-and-demand]]); NG × RTM ([[natural-gas-prices]]); forecast error × price
([[mid-term-load-forecast]]); spare-capacity (load, renewable gen, non-RE capacity) × RTM
price × NG price × degree-days ([[analysis/spare-capacity-correlates-with-rtm-price]]).
Notebook-by-notebook: [[notebook-catalog]].


## Conventions
- **Trial before full extract** (step 1) validates auth/params cheaply — see [[data-extraction-guide]].
- **Normalize archive output** to match live parquet schema exactly (columns, types, flags).
- **One concept per cleaned file**; name with explicit date span (`_YYYYMMDD_YYYYMMDD`).
- Path discipline: notebooks read from `01_data/{1.2_raw_api,2_cleaned,3_analysis}` (path
  patching complete as of 2026-07-01; see [[notebook-catalog]] for current per-notebook status).

## Related
- [[data-extraction-guide]] · [[notebook-catalog]] · [[ercot-data-products]] · [[feature-engineering]]

## Sources
- [[sources/2026-06-30_ercot-data-extraction-skill]]
