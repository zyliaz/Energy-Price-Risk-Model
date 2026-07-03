---
title: Data Extraction Guide
type: concept
tags: [data, extraction, api, methods, reference]
status: stable
sources: 1
updated: 2026-07-03
---

# Data Extraction Guide

Condensed, reusable playbook for pulling ERCOT data via the Public API — built from past
iterations. Read before adding a **new data source**. Full detail:
[[sources/2026-06-30_ercot-data-extraction-skill]]. Product catalog: [[ercot-data-products]].

## Auth (every request needs both)
- **OAuth:** Azure AD B2C ROPC (username+password → token). ⚠️ field is **`id_token`, not
  `access_token`** — using the wrong one silently gives `""` and fails on first call.
- **Subscription key:** header `Ocp-Apim-Subscription-Key`. Non-member tier = lower rate limits.
- Token ~1 h: cache + refresh ~60 s early; force-refresh once on 401. Credentials in
  gitignored `.env` (`set -a && source .env && set +a`), never hardcoded.

## Endpoints & ranges (verify depth before building an archive fallback)
| Dataset | Report | Coverage | Strategy | Date param |
|---|---|---|---|---|
| RTM LMP (5-min) | NP6-788-CD | **live Dec 2023+**, archive 2021–2023 | live: monthly chunk; pre-2024: archive list+POST | `SCEDTimestampFrom/To` (ISO) |
| Load by fcst zone | NP6-346-CD | live **2021+** | **single-pass** paginate | `operatingDayFrom/To` (date) |
| Wind by geo (WPP) | NP4-742-CD | **live Dec 2023+**, archive 2021–2023 (`ercot_wpp_archive.py`) | single-pass | `deliveryDateFrom/To` |
| **Solar by geo** | NP4-745-CD | claimed live 2021+ — **unverified, scraper never run** | single-pass | `deliveryDateFrom/To` |
| Wind 5-min by geo | NP4-743-CD | TBD → `00_check/01` notebook | planned `ercot_wpp_5min.py` | TBD (Phase 1 of notebook) |
| Solar 5-min by geo | NP4-746-CD | TBD → `00_check/01` notebook | planned `ercot_spp_5min.py` | TBD (Phase 1 of notebook) |
| DAM SPP / RTM SPP (bulk) | 13060 / 13061 | archive | bulk zip download | — |
| Price adders | NP6-793-ER | 2014+ | — | — |

> ⚠️ **Naming trap:** `ercot_spp_by_geo.py` = **Solar Power Production** (NP4-745-CD), *not*
> Settlement Point Price. "SPP" is overloaded across this project. See [[lmp-spp]] for the
> price SPP.
> ⚠️ CORRECTED 2026-07-03: this page previously said "only NP6-788-CD has the Dec-2023 live
> cutoff; load/wind/solar go back to 2021 live." Wrong for wind — the on-disk live wind pull
> starts 2023-12-09 (which is why `ercot_wpp_archive.py` exists). Solar's 2021+ claim is
> untested. Never trust a coverage claim without a dated pull or notebook check behind it.

## Top pitfalls (ordered by surprise)
1. **Zone systems don't align.** Price LZ ≠ forecast zone ≠ wind region ≠ solar region.
   "North" wind ≠ "North" LZ; "NorthWest" solar = Panhandle, *not* North TX. Resolve via the
   county mapping, by overlap %. See [[load-zones]].
2. **Archive ≠ live.** Archive CSV timestamps are US format `MM/DD/YYYY`; columns differ in
   case (`SettlementPoint` vs `settlementPoint`); flags are `Y/N` not bool; ZIP is **nested**
   (outer→inner→CSV). Normalize columns to match live parquet exactly.
3. **`hourEnding='24:00'`** = next day 00:00 — needs the DuckDB `CASE … INTERVAL 1 DAY` pattern.
4. **Monthly chunking returns 0 rows on load/wind/solar** — those need one wide date range.
   LMP is the opposite: chunk monthly and check `totalRecords`/chunk (large ranges silently 0).
5. **DST:** spring = 1 missing hour, fall = 1 duplicate. Filter `repeatHourFlag=FALSE` (LMP) /
   `DSTFlag=FALSE` (load/gen). Always check row counts near the DST Sundays.
6. **LMP timestamps have sub-minute offsets** (:27, :16). Resample `.resample('1h').mean()`.
7. **Keep price extremes** — negative or $5,000+/MWh LMPs are real; flag, don't drop.
8. **Script exists ≠ data exists.** `ercot_spp_by_geo.py` sat unrun with no output parquet
   while the wiki implied solar was covered. Verify the output file on disk, not the script.
9. **Rolling-window snapshot duplication.** Gen reports repost each interval in every
   overlapping snapshot (~12× for 5-min reports w/ 60-min windows; ~216× for wind hourly
   archive). Undeduped: `wpp_archive` parquet = 4.78M rows vs ~27k real intervals. Dedupe on
   the interval key at write time — actuals are settled, any snapshot copy is equivalent.
   Corollary: parquet size fears come from duplication, not resolution; deduped 5-min ≈ 3–5 MB/yr.
10. **Our own outputs can mismatch too.** Wind archive parquet stores `hourEnding` as
    `"01:00"` strings + no `postedDatetime`; live stores int 1–24. Normalize to the live
    schema *before* writing, or the merge breaks later (pitfall 2 applies to ourselves).
11. **Check for by-geo report variants before building.** 5-min by-geo products are
    **NP4-743-CD** (wind) / **NP4-746-CD** (solar) — not the system-wide NP4-733/738-CD a
    keyword search surfaces first. Resolve IDs via EMIL artifact discovery, not guessing.

## Timeouts (non-member, empirical)
Connect 10 s · read 60 s (live) / 180 s (archive list) / 240 s (archive download) · sleep
0.25 s/page · retry 3× backoff 2→4→8 s. On 429s, **raise the sleep (0.5–1 s), not the
timeout.** Row sanity: hourly ≈ 8,760/yr, 5-min ≈ 105,120/yr.

## EMIL self-describing workflow (skip the portals)
Two GETs discover everything: `GET /api/public-reports/{PRODUCT}` → sub-report endpoint;
`GET {endpoint}` (no params) → `fields[].name/dataType/hasRange/searchable`. Any field with
`hasRange=True` accepts `{field}From`/`{field}To`. Page-1 with no params returns *today*.
Compute pages yourself: `ceil(totalRecords / page_size)`.

## Memory-efficient pattern
Stream pages straight to parquet via a chunk writer (open on first write to fix schema,
`reindex(columns=fixed_cols)` after) — never accumulate all pages in memory. Shared helpers:
`ercot_common.py` (`ERCOTAPIClient`, `ParquetChunkWriter`, `monthly_intervals`).

## SLURM / HPC jobs convention
Big extracts (e.g. archive LMP, 11–22 h) run as SLURM jobs in **`04_jobs/<dataset>_<date>/`**.
Each job is **self-contained** (Python script + `.sh`, no project imports), always `--auto`
(trial/validation belongs in the `00_check` notebook, not the job). `.sh` sets SBATCH headers,
`module purge && module add anaconda`, credential exports, preflight `python -c "import ..."`.

## Related
- [[extraction-scripts]] — the actual scripts, grouped (extractors vs parsers) with behavior.
- [[analysis-workflow]] · [[ercot-data-products]] · [[load-zones]] · [[feature-engineering]]

## Sources
- [[sources/2026-06-30_ercot-data-extraction-skill]]
