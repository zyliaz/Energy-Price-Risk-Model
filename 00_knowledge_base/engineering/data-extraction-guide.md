---
title: Data Extraction Guide
type: engineering
tags: [data, extraction, api, methods, reference]
status: stable
sources: 1
updated: 2026-10-28
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
| 7-Day Load Fcast by WZ | NP3-561-CD | **archive** (live returns 0 for 2023) | archive list+POST (**≤50 docIds/batch**); keep all postings, inject `postedDatetime` | `postDatetimeFrom/To` (ISO) |
| Resource outage cap | NP3-233-CD | **archive 2021→present** (verified 2026-09-24); live Dec 2023+ overlaps | archive only: monthly list+POST (100/batch OK), monthly part files | `postDatetimeFrom/To` (ISO) |

> ⚠️ **Naming trap:** `ercot_spp_by_geo.py` = **Solar Power Production** (NP4-745-CD), *not*
> Settlement Point Price. "SPP" is overloaded across this project. See [[lmp-spp]] for the
> price SPP.
> ⚠️ CORRECTED 2026-07-03: this page previously said "only NP6-788-CD has the Dec-2023 live
> cutoff; load/wind/solar go back to 2021 live." Wrong for wind — the on-disk live wind pull
> starts 2023-12-09 (which is why `ercot_wpp_archive.py` exists). Solar's 2021+ claim is
> untested. Never trust a coverage claim without a dated pull or notebook check behind it.

## Top pitfalls (ordered by surprise)
1. **Zone systems don't align.** Price LZ ≠ forecast zone ≠ weather zone ≠ wind/solar region.
   "North" wind ≠ "North" LZ; "NorthWest" solar = Panhandle, *not* North TX. Even spellings
   drift per source (`LZ_RAYB` in gpkg vs `LZ_RAYBN` in price parquets). Resolve via the
   county mapping, by overlap %. Schemas + join caveats: [[load-zones]].
2. **Archive ≠ live.** Archive CSV timestamps are US format `MM/DD/YYYY`; columns differ in
   case (`SettlementPoint` vs `settlementPoint`); flags are `Y/N` not bool; ZIP is **nested**
   (outer→inner→CSV). Normalize columns to match live parquet exactly. Build rename maps from
   a **real downloaded doc per era**, not from the live field names: NP3-233-CD archive CSVs
   label the date `Date`, and a map keyed on `OperatingDate` silently dropped the date column.
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
12. **Manual bulk-download sources can mix hour convention mid-series.** ERCOT's 2020–2022
    fuel-mix files (`IntGenbyFuel20YY.xlsx`) report 15-min intervals hour-**starting**; the
    2023–2025 hourly wind/solar output files are already hour-**ending**. Concatenating
    without shifting the older span by +1h silently misaligns two segments of the same series.
    Check convention per file, not per dataset. See `hourly_solar_wind_generation_2021_2025.ipynb`,
    [[ercot-data-products]]. **Project standard is hour-ending (HE)** — full convention + date+HE→datetime
    recipes in [[feature-engineering]] "Datetime convention". RTM adders / RTM LZ-HB SPP were
    realigned HS→HE on 2026-07-23 (kept 15-min interval-beginning as atomic truth).
13. **Archive `POST /download` is case-sensitive AND batch-capped** (found on NP3-561-CD,
    2026-07-22). The download route needs the **UPPERCASE** EMIL id (`.../archive/NP3-561-CD/download`);
    a lowercase POST returns **HTTP 405**. It also caps at **~50 docIds per request** — n≥100
    returns HTTP 405 (a misleading status for an oversized batch, not a real "method not
    allowed"). Chunk downloads at 50. The **list GET** accepts either case and `size` up to 1000.
14. **Some archive forecasts omit `postedDatetime` from the CSV.** NP3-561-CD archive CSVs carry
    only `DeliveryDate/HourEnding/<zones>/SystemTotal/DSTFlag` — the posting timestamp lives only
    in the archive doc metadata (`postDatetime`) and the ZIP entry filename. When every posting
    must stay distinguishable (rolling snapshots, ~192 postings per delivery-hour), map each inner
    file's **leading docId → the list's `postDatetime`** and inject it as a column.
15. **Non-ERCOT sources bring their own timestamp convention — verify it, don't assume HE.**
    Found 2026-07-24: the ERA5 (Copernicus CDS) hourly temperature pipeline
    (`era5_ercot_temp_2021-2025.py`) writes `valid_time` straight through as `datetime` with no
    conversion — ERA5 is natively **UTC**, but every ERCOT-derived series in this repo is
    hour-ending **Central Time**. Joining on raw `datetime` equality silently misaligns by
    ~5–6 hours. Check a new source's diurnal pattern (peak/trough hour) against the expected
    local pattern before trusting a timestamp join. See [[weather-hdd-cdd]],
    [[feature-engineering]]. Also: the CDS API needs live credentials (`CDS_API_URL`/
    `CDS_API_KEY` in `.env`) and `client.retrieve()` calls a real, potentially slow external
    queue — don't re-run a CDS notebook/script cell unattended if the target `.nc` file already
    exists on disk (the `.py` script has an existing-file skip check; the check notebook's
    "test cell" does not).

16. **HPC paths ≠ local paths — never hardcode.** On HPC, `ercot_common.py` is copied flat
    to the SLURM `--chdir` (e.g. `/work/users/z/y/zylia/`), so `PROJECT_ROOT`
    (`Path(__file__).resolve().parents[2]`) resolves to a completely different tree than the
    local repo's `ERCOT-Research/`. Any path passed as a CLI argument (like `--existing
    01_data/...`) will fail because the relative prefix doesn't exist on the cluster. **Fix:**
    always derive paths from `OUT_DIR` (which follows `PROJECT_ROOT` automatically) rather
    than passing them as string arguments. For resume scripts, glob for the partial parquet
    by its naming pattern inside `OUT_DIR` instead of taking a path flag.
17. **Archive coverage can reach the present — list recent years before building a live
    extractor.** NP3-233-CD's archive runs from 2021 to the current hour, overlaps the live API
    and matches it exactly. We assumed it stopped at the live cutoff and spent ~27 h over 3 HPC
    attempts paging the live API (~21 s/page) for data the archive had. One
    `GET archive/{id}?postDatetimeFrom=<recent>` with `size=1` settles it.
18. **One writer per long job means one point of failure.** The sep19 NP3-233-CD archive job
    streamed 4.8M rows through a single `ParquetChunkWriter`, and the file came back unreadable
    (`Corrupt snappy compressed data`), so every row was lost. For multi-hour jobs, write
    **one part file per month**:
    - Write to a tmp file, then rename, and only after every batch and the posting count check out.
    - On rerun, skip the parts that already exist.
    - Combine the parts at the end and check the row count from the parquet metadata.

    Resume then needs no att2 script (see `ercot_outage_cap_archive_full.py`).
19. **Report 13061 SPP Excel is 15-min, not hourly, and lists load zones twice.** Each
    hour has 4 `Delivery Interval` rows, and every `LZ_*` point appears as both `LZ` and `LZEW`
    type (identical prices). `drop_duplicates` on date/hour/point silently keeps interval 1
    only; average the intervals instead (`organize_rtm_lmp_2026`, fixed 2026-10-28). Also,
    the yearly file has no posting date in its name (`RTMLZHBSPP_2026.xlsx`), so a re-download
    collides with the old copy (macOS saved it as `RTMLZHBSPP_2026 2.xlsx`) — name the file
    explicitly rather than globbing.
20. **Not every scraper loads `.env`, and a pipe hides the failure.** `ercot_load_by_fzn.py`
    reads `ERCOT_*` from the environment only (no `load_dotenv`), so run from a shell without
    them it exits on "Required environment variable … not set". Piped into `tail`, the
    command still reports exit 0 (found 2026-10-28). Load `.env` first, and check the output
    file exists rather than trusting the exit code of a pipeline.
21. **Close netCDF files before re-opening them in the same process.** In
    `02_era5_ercot_temp`, cell 13 opened every 2026 `.nc` without closing, and the later splice
    check re-opened the Jan file: the Jupyter kernel died with no Python traceback (found
    2026-10-28). Open with `with xr.open_dataset(p) as ds:`. Separately, a gap check on CPT
    hour-ending data must build its expected hours in `America/Chicago`, since the
    spring-forward hour does not exist locally.

## Timeouts (non-member, empirical)
Connect 10 s · read 60 s (live) / 180 s (archive list) / 240 s (archive download) · sleep
0.25 s/page · retry 3× backoff 2→4→8 s. On 429s, **raise the sleep (0.5–1 s), not the
timeout.** Row sanity: hourly ≈ 8,760/yr, 5-min ≈ 105,120/yr.

## EMIL self-describing workflow (skip the portals)
Two GETs discover everything: `GET /api/public-reports/{PRODUCT}` → sub-report endpoint;
`GET {endpoint}` (no params) → `fields[].name/dataType/hasRange/searchable`. Any field with
`hasRange=True` accepts `{field}From`/`{field}To`. Page-1 with no params returns *today*.
Compute pages yourself: `ceil(totalRecords / page_size)`.

> **Endpoint-check template (live + archive):** the canonical worked example for a new ERCOT
> API endpoint check is `03_notebooks/00_check/04_ercot_7d_load_fcast_by_wzn_endpoint_check.ipynb`
> — it demonstrates the full pattern end-to-end: live coverage probe → archive list
> (`docId → postDatetime`) → chunked `POST /download` → nested unzip → schema + timed one-day
> sample → runtime extrapolation (Method B vs C). Copy it (not the older, credential-blocked
> `00_endpoint_check_template`) when standing up the next extractor. A **PreToolUse(Write) hook**
> (`.claude/hooks/require_endpoint_check.sh`, added 2026-07-22) gates new
> `02_scripts/1_scrapers/ercot_*.py` extractors on a matching `00_check` notebook existing first.
> See [[notebook-catalog]].

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
