---
title: Repo Migration Map (old → new)
type: concept
tags: [meta, migration, repo]
status: developing
updated: 2026-06-30
---

# Repo Migration Map (old → new)

How the legacy repo **`RESEARCH-PJM-ERCOT-Price-Volatility`** maps into the new
**`ERCOT-Research`** structure.

> **Mode: COPY only.** The old repo stays fully intact; files are duplicated into the new
> structure (no `git mv`, no deletes from the source). No PJM-specific data exists in the
> repo — everything is ERCOT, so nothing is excluded on scope grounds.
> **Disk note:** workspace has ~8.6 GB free; full `data/` is 3.7 GB.

## 01_data — classification rule
- **1.1_raw_bulk** — downloaded raw zip/csv/excel. ← *everything in* `data/01_raw`.
- **1.2_raw_api** — raw parquet from API calls. ← `data/parquet/*` + raw parquet currently
  misfiled in `data/02_processed`.
- **1.3_raw_other** — self-contained scrapers / imported data. ← `data/other sources`
  (+ `data/mapping` imported reference files).
- **2_cleaned** — csv aggregated in time/space from a **single** source. ← csv in `data/02_processed`.
- **3_analysis** — csv that **merges multiple** sources for analysis. ← `data/03_analysis`.

### Data file mapping
| Old | New | Size |
|---|---|---|
| `data/01_raw/**` (286 zip, 75 xlsx, 5 csv) | `01_data/1.1_raw_bulk/` | ~1 GB |
| `data/parquet/ercot/*.parquet` | `01_data/1.2_raw_api/` | ~620 MB* |
| `data/02_processed/**/*.parquet` (load_by_LZ, mtlf) | `01_data/1.2_raw_api/` | ~4 MB |
| `data/02_processed/**/*.csv` (price adders, load, RTM cleaned) | `01_data/2_cleaned/` | ~50 MB |
| `data/03_analysis/**` (NG Price: parquet/csv + figures/raw imports) | `01_data/3_analysis/` | ~28 MB |
| `data/mapping/**` (LZ↔county, shapefiles, gpkg) | `01_data/1.3_raw_other/mapping/` | 12 MB |
| `data/other sources/CDD/**` (GridMET, shapefiles, scraper nb) | `01_data/1.3_raw_other/CDD/` | 2 GB |
| `data/other sources/Plant-level Generation/**` | `01_data/1.3_raw_other/` | 1.3 MB |
| `data/output/**` (archived figures) | `01_data/3_analysis/output/` | 3.5 MB |

\* *Includes the two `NP6-788-CD_*` nodal-LMP parquets = **600 MB**, which are the **superseded**
RTM approach (current RTM source = report 13061). Kept only for the [[lmp-spp]] PA-vs-SPP
nodal validation — see decision below.*

## 02_scripts — final grouping (see [[extraction-scripts]])
**`1_scrapers/` — ERCOT-API extractors** (+ `ercot_common` core): `ercot_load_by_fzn`,
`ercot_wpp_by_geo`, `ercot_spp_by_geo` (solar, live) + `ercot_load_archive`,
`ercot_wpp_archive` (archive). Canonical set = 6; **`ercot_lmp_archive` (NP6-788-CD) not
copied** — add only for PA-vs-SPP nodal validation.
**`2_parsers/` — excel→parquet + adder parsers:** `organize_lmp_parquet`,
`organize_rtm_lmp_2026`, `parse_mid_term_load_forecast_parquet`, `parse_rtm_price_adders`,
`parse_rtm_price_adders_2025dec_2026`.
**Removed:** `eia_ng_waha_download` (legacy, out of scope).

**Verified self-contained:** all cross-script imports (`ercot_common`,
`organize_lmp_parquet`) resolve inside `1_scrapers/`; nothing imports the never-copied
`ercot_public_api` or the dropped `ercot_lmp_archive`.

## 03_notebooks — DONE (kept set only)
Per scope decision, only `01_RTM_price_eda`, `02_load_eda`, and notebooks `06`→ were
kept (plus helper dependencies). **Legacy, not copied:** `00_ercot_emil_snippet`,
`03_LZ_price_cleaning`, `04_rtm_dam_price_eda`, `05_wpp_eda`.

| Old | New |
|---|---|
| `01_ercot_RTM_price_eda` | `01_eda/00_rtm_price_eda` |
| `02_ercot_load_eda` | `01_eda/01_load_eda` |
| `06_mid_term_load_forecast_eda` | `01_eda/02_mtlf_eda` |
| `07_ng_price_correlation` | `01_eda/03_ng_price_correlation` |
| `08_price_adders_pre_2025_cleaning` | `01_eda/04_price_adders_pre2025_cleaning` |
| `08.2_price_adder_numerical_distribution` | `01_eda/05_price_adder_distribution` |
| `09_new_PA_eda` | `01_eda/06_new_pa_cleaning` |
| `09.2_new_PA_numerical_distribution` | `01_eda/07_new_pa_distribution` |
| `11_[IN PROGRESS]_HDD_eda` | `01_eda/08_hdd_eda_wip` |
| `06.1_..._load_forecast_rtm_coorelation` | `02_analysis/00_load_forecast_rtm_correlation_wip` |
| `07.1_ng_rtm_price_correlation` | `02_analysis/01_ng_rtm_price_correlation` |
| `08.1_..._price_adder_activation_analysis` | `02_analysis/02_price_adder_activation` |
| `09.1_new_PA_activation_analysis` | `02_analysis/03_new_pa_activation` |
| `10_price_adder_rtm_load_correlation` | `02_analysis/04_price_adder_rtm_load_correlation` |
| `10.0_load_rtm_price_plot` | `02_analysis/05_load_rtm_price_plot` |
| `10.1_[PENDING]_investigate_abnormal_PA` | `02_analysis/06_investigate_abnormal_pa_wip` |

**Helpers dropped** (`00_reusable_functions`, `Scatter corr.py`): inspection showed the only
two consumers (`03_ng_price_correlation`, `01_ng_rtm_price_correlation`) **define
`scatter_corr()` inline** rather than importing the helper — so neither was a real
dependency. `00_reusable_functions` was also a stale duplicate of `scatter_corr.py`.
> 💡 If you later want a single shared `scatter_corr`, lift it into `02_scripts/` and have
> the two notebooks import it instead of redefining it.

`00_check/` left empty for a future prelim API-check notebook (legacy `00_emil_snippet`
not copied; say the word to add it).

## 04_jobs — individual HPC bash jobs
`jobs/*` copied as-is (each folder = one HPC job: lmp_np6788cd*, wpp/spp geo, archives).

## Decisions
- **Mode:** COPY only, old repo intact. ✅
- **Dead artifacts excluded:** `.ipynb_checkpoints`, `__pycache__`, `.DS_Store`, `.Rhistory`, `.venv`. ✅
- **Script split:** scrapers / parsers, drop nothing but mark NP6-788-CD legacy. ✅ (proposed)
- **Data scope:** _pending_ — see options below.
- **NP6-788-CD nodal (600 MB) + its scripts:** _pending_ — keep for PA-vs-SPP validation, or skip.
- **Figures/raw imports in 03_analysis & output (pngs/htm/xls):** _pending_ — keep alongside
  `3_analysis/`, or leave in old repo.

### Data-scope options
| Option | Copies | Size |
|---|---|---|
| **A. Full** | 1.1+1.2+1.3+2+3 (everything, per mapping) | ~3.7 GB (or ~1.1 GB if NP6-788-CD + CDD excluded) |
| **B. Lean** | only `2_cleaned` + `3_analysis` csv now; raw/api/other re-pulled later | ~80 MB |
| **C. Code only** | no data | 0 |

(All options copy `02_scripts`, `03_notebooks`, `04_jobs`.)

## Status — COPIED 2026-06-30 ✅
- **Scripts:** 9 scrapers + 3 parsers (`ercot_lmp_archive` NP6-788-CD dropped).
- **Jobs:** wpp/spp geo + wpp archive (NP6-788-CD nodal jobs dropped).
- **Notebooks:** 16 kept (+2 helpers), renumbered; 4 legacy dropped.
- **Data (~82 MB):** 11 raw-API parquet (NP6-788-CD skipped) → `1.2_raw_api`;
  derived csv/parquet → `2_cleaned`; `ng_prices_monthly.parquet` → `3_analysis`.
  Raw bulk (`01_raw`), CDD raw (2 GB), mapping, and all figures/htm/xls left in old repo.

### Path patching
- **Scripts — DONE ✅** All 12 scripts repointed to the new layout: `ercot_common.OUT_DIR`
  → `01_data/1.2_raw_api` (covers all 5 API scrapers); organizers read
  `01_data/1.1_raw_bulk/ercot/{DAM,RTM}` → write `01_data/1.2_raw_api`; price-adder +
  MTLF parsers read `1.1_raw_bulk` → write `1.2_raw_api`; EIA NG → `1.3_raw_other/ng_price`.
  Docstrings normalized; no old `data/...` or `src/extraction/` paths remain.
  (Raw-bulk inputs live under `01_data/1.1_raw_bulk/` — currently empty; populate or
  symlink from the old repo's `data/01_raw` before running the organizers/parsers.)
- **Notebooks — DONE ✅** All 16 notebooks repointed (root anchor fixed for the new
  two-level depth: `Path('..')` → `Path('../..')`, `Path.cwd().parent` →
  `Path.cwd().parents[1]`). Path mapping: raw parquet → `1.2_raw_api`; single-source
  cleaned csv → `2_cleaned/{rtm_price,load,load/forecast,price_adders,weather}`;
  analysis intermediates → `3_analysis/{price_adders_analysis,ng_price,load_forecast,HDD}`;
  NG raw → `1.3_raw_other/ng_price`; figures → `3_analysis/output`. JSON re-validated,
  no residual old paths in code cells.
  - **Expected-missing inputs** (not errors): some notebooks read intermediates that
    *upstream* notebooks generate (e.g. `price_adders_analysis/rtm_price_adders_hourly.csv`,
    `post_202512/post_202512_price_adders_hourly.csv`) — run the cleaning/EDA notebooks
    first. Raw NG `.xls` files live in `1.3_raw_other/ng_price` (left in old repo; re-pull
    via `eia_ng_waha_download.py`).
  - **Data nit:** `01_ng_rtm_price_correlation` reads `ng_prices_monthly.csv`, but the
    migrated file is `ng_prices_monthly.parquet`. Re-export as CSV or adjust the read.
  - Reminder: organizers/parsers + cleaning notebooks read `01_data/1.1_raw_bulk/`
    (currently empty — populate or symlink the old repo's `data/01_raw`).

## Related
- [[00_overview]] · [[ercot-data-products]] · [[scope-and-history]]
