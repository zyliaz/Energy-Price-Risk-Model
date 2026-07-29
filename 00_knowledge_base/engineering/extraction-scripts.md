---
title: Extraction Scripts (architecture)
type: engineering
tags: [data, extraction, scripts, methods, reference]
status: stable
sources: 1
updated: 2026-07-29
---

# Extraction Scripts (architecture)

How `02_scripts/` is organized and how each script behaves. Companion to the general
playbook [[data-extraction-guide]] and the pipeline map [[analysis-workflow]]. All ERCOT
extractors share one core, `ercot_common.py` (`ERCOTAuth`, `ERCOTAPIClient`,
`ParquetChunkWriter`, `parse_payload`, `monthly_intervals`).

## Grouping
**1) ERCOT-API extractors → `02_scripts/1_scrapers/`** (network pulls; share `ercot_common`)

| Script | Data | Vintage | Strategy |
|---|---|---|---|
| `ercot_load_by_fzn` | Load by forecast zone | live 2021+ | single-pass pagination |
| `ercot_wpp_by_geo` | Wind by geo | live 2021+ | single-pass pagination |
| `ercot_spp_by_geo` | **Solar** by geo (NP4-745-CD) | live 2021+ | single-pass pagination |
| `ercot_load_archive` | Load (backfill / cross-check) | archive 2021–2023 | list docIds → batch download |
| `ercot_wpp_archive` | Wind (backfill / cross-check) | archive 2021–2023 | list docIds → batch download |
| *`ercot_lmp_archive`* | *LMP backfill (NP6-788-CD)* | *archive 2021–2023* | *list+download* |
| `ercot_mtlf_day_ahead` | Seven-Day Load Forecast, day-ahead slice (NP3-565-CD) | live | per-operating-day: keep the last in-use-model posting before the 10:00 CT DAM close |
| `ercot_7d_load_fcast_wzn_archive` | Seven-Day Load Forecast **by Weather Zone** (NP3-561-CD), **every posting kept** | archive | list docIds → batch download (**≤50/POST**); inject `postedDatetime` from doc metadata; filter to delivery-date window |

> The canonical set was **6 extractors** (3 live + 3 archive); a 7th, `ercot_mtlf_day_ahead`,
> was added 2026-07-14 for the NP3-565-CD short-horizon forecast product tracked in
> [[mid-term-load-forecast]], and an 8th, `ercot_7d_load_fcast_wzn_archive`, on 2026-07-22 for
> the sibling **NP3-561-CD** product (see [[ercot-data-products]]). They share `ercot_common.py`
> (auth/writer) like the others; all support `--trial-only`/`--auto`.
> `mtlf_day_ahead` has a trial pull only (`mtlf_day_ahead_trial.csv`); `7d_load_fcast_wzn_archive`
> has been run for **Aug 2023** (`load_fcast_wzn_archive_20230801_20230831.parquet`,
> 142,776 rows = 744 delivery-hours × ~192 postings, 0 nulls).
> `ercot_lmp_archive` is still **not copied into this repo** — NP6-788-CD nodal
> LMP was scoped out earlier. Add it if the PA-vs-SPP nodal validation ([[lmp-spp]]) goes
> ahead. **No solar archive exists** — the live solar endpoint already reaches 2021.
>
> **NP3-561-CD vs NP3-565-CD** — easy to confuse: 561 = the single official *by-weather-zone*
> forecast (no `model`/`inUseFlag` columns); 565 = the *by-model-and-weather-zone* variant that
> `ercot_mtlf_day_ahead` slices. The live endpoint for 561 returns 0 for 2023 (short rolling
> window), so historical months come from the archive; the same forecast is reposted ~hourly,
> so `deliveryDate × hourEnding` recurs across ~192 postings and every posting is retained,
> tagged by injected `postedDatetime` (not present in the archive CSV).

**1b) Non-ERCOT scrapers → `02_scripts/1_scrapers/`** (share the directory, not `ercot_common`)

| Script | Data | Source | Notes |
|---|---|---|---|
| `era5_ercot_temp.py` | Hourly Texas-statewide mean temperature, 2021–2025 | **ERA5** (Copernicus Climate Data Store reanalysis) | **Rewritten 2026-07-29** (replaces `era5_ercot_temp_2021-2025.py`, which remains idle). Defines the extraction range in **Central Prevailing Time** (CPT = `America/Chicago`), converts to UTC for the CDS API requests, downloads full UTC calendar years + a small boundary request for the tail-end hours that spill past `END_YEAR` (Option A: two requests per boundary, no cartesian over-coverage), combines `.nc` files via `xr.concat`, masks to TX boundary, averages, converts UTC→CPT, trims to the exact CPT window. Timestamps shifted +1h to **hour-ending** to match ERCOT convention; DST fall-back duplicates averaged via `groupby.mean()`, spring-forward gap aligned (ERCOT skips HE 03, ERA5+HE-shift skips HE 03 — same gap). Output columns: `datetime` (tz-naive CPT, hour-ending) + `tx_temp` (°F). Validates (schema/NaN/dupe/missing-hour/range) against a CPT-aware HE expected range. Writes `2_cleaned/weather/Texas_hourly_temp_2021_2025.csv`. Needs `CDS_API_URL`/`CDS_API_KEY` in `.env`. Checked via `00_check/02_era5_ercot_temp.ipynb` (also rewritten with same CPT-first + HE pattern). |

**2) Excel→parquet parsers → `02_scripts/2_parsers/`** (no network; consolidate local files)

| Script | Transforms |
|---|---|
| `organize_lmp_parquet` | Local DAM/RTM Excel report archives → parquet |
| `organize_rtm_lmp_2026` | RTM (report 13061) Excel → parquet. **Fixed 2026-07-23:** timestamp built as `date + DeliveryHour` (HE), was `date + (DeliveryHour−1)` (HS) — part of the repo-wide HE standardization, see [[feature-engineering]] "Datetime convention". |
| `parse_mid_term_load_forecast_parquet` | MTLF Metrics xlsx → parquet (hourly error) |
| `parse_mid_term_load_forecast_models_parquet` | MTLF Metrics xlsx → parquet (all 7 alt forecast models: A3/A6/E/E1/E2/E3/M, per zone — load-prediction features, no error calc) |
| `parse_rtm_price_adders` | Pre-2025 price adders → parquet |
| `parse_rtm_price_adders_2025dec_2026` | Post-2025 (RTC+B) adders → parquet |
| `hourly_solar_wind_generation_2021_2025` (notebook) | Two raw formats → one unified hourly Wind+Solar `renewable_gen` (MW) parquet, `01_data/2_cleaned/generation/hourly_solar_wind_generation_2020_2025.parquet`: (1) `IntGenbyFuel20{20,21,22}.xlsx` (15-min gen-by-fuel, one sheet/month) — filtered to Wind+Solar, melted, summed per hour, hour-starting shifted +1h to hour-ending to match the rest of the repo; (2) `..._Hourly_WindSolar_Output.xlsx` (2023–2025, already hourly hour-ending) — Wind+Solar summed directly. Concatenated 2020-01-01–2026-01-01, 52,614 rows, 0 nulls (verified 2026-07-10). |

> `eia_ng_waha_download` (EIA Waha NG) **removed** — legacy, out of scope for the current
> topic. Current NG series (Henry Hub / citygate) would be a new scraper. See [[natural-gas-prices]].

## Shared auth (all ERCOT extractors)
Azure AD B2C ROPC → **`id_token`** (not `access_token` — documented gotcha), cached and
refreshed ~60 s before expiry, force-refreshed once on 401. Every request also carries
`Ocp-Apim-Subscription-Key`.

## Two extraction strategies (by data vintage)
- **Live, single-pass pagination** (load/wind/solar): one date-range request, paginate
  `page`/`size`, stream each page straight to parquet via `ParquetChunkWriter` (flat memory).
- **Archive, two-step list+download** (LMP/load/wind archive): list docIds per month → POST
  batch (≤1000) → outer ZIP → inner ZIP → CSV. Backfills 2021–2023 (live LMP starts ~Dec 2023;
  load/wind archives used for cross-validation even though live reaches 2021).

## Parser pattern
- **Live:** JSON `{fields, data}` → `parse_payload()` zips field names to rows.
- **Archive:** raw CSV bytes decoded against `utf-8/latin-1/cp1252`, then a `COLUMN_RENAMES`
  dict normalizes vintage column names to the live schema exactly
  (`RepeatedHourFlag`→`repeatHourFlag`, `DELIVERY_DATE`→`deliveryDate`, …).

## Datetime & flag handling
- Live timestamps already ISO 8601; archive CSVs are `MM/DD/YYYY` → `pd.to_datetime(format=…)`.
- Wind archive: integer `HOUR_ENDING` (1–24) → `"HH:00"` string to match live.
- `repeatHourFlag`/`DSTFlag` normalized from `Y/N` · `TRUE/FALSE` · `1/0` → real boolean.
- `"24:00"` hour-ending **kept as string** (not coerced) to avoid breaking downstream SQL.
- Wind archive dedups on `(deliveryDate, hourEnding)` via a `seen_keys` set — docs are rolling
  9-day snapshots that overlap.

## Error handling (uniform across the 6 ERCOT extractors)
401 → force-refresh token once, retry. 429/5xx → retry with backoff (LMP archive exponential
2/4/8 s; load/wind archive fixed 30 s × attempt — they hit limits more). `MAX_RETRIES=3`;
network errors retried then re-raised. Per-batch `try/except` logs and continues rather than
aborting the whole run.

## Related
- [[data-extraction-guide]] · [[analysis-workflow]] · [[ercot-data-products]] · [[notebook-catalog]]

## Sources
- [[sources/2026-06-30_ercot-data-extraction-skill]]
