---
title: Extraction Scripts (architecture)
type: engineering
tags: [data, extraction, scripts, methods, reference]
status: stable
sources: 1
updated: 2026-07-10
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

> The canonical set is **6 extractors** (3 live + 3 archive). `ercot_lmp_archive` is **not
> copied into this repo** — NP6-788-CD nodal LMP was scoped out earlier. Add it if the
> PA-vs-SPP nodal validation ([[lmp-spp]]) goes ahead. **No solar archive exists** — the
> live solar endpoint already reaches 2021.

**2) Excel→parquet parsers → `02_scripts/2_parsers/`** (no network; consolidate local files)

| Script | Transforms |
|---|---|
| `organize_lmp_parquet` | Local DAM/RTM Excel report archives → parquet |
| `organize_rtm_lmp_2026` | RTM (report 13061) Excel → parquet |
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
