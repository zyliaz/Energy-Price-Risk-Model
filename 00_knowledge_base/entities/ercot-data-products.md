---
title: ERCOT Data Products
type: entity
tags: [data-source, api, ercot]
status: developing
sources: 0
updated: 2026-09-26
---

# ERCOT Data Products

Reference for the ERCOT datasets feeding this project and where they come from.
**Authoritative list** per [[sources/2026-06-30_data-and-eda-notes]].

| Product                  | What                               | Report / source                                               | Granularity                                                           | Extraction code                                       |
| ------------------------ | ---------------------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------- |
| Wind production          | WPP by geography (NP4-742-CD)      | live API                                                      | hourly, by **wind region** (6, not weather zone — see [[load-zones]]) | `ercot_wpp_by_geo.py`, `ercot_wpp_archive.py`         |
| Solar production         | Solar PP by geography (NP4-745-CD) | live API                                                      | hourly                                                                | `ercot_spp_by_geo.py`                                 |
| Actual load              | By forecast zone                   | **NP6-346-CD** archive (2021–Nov 2023) + live API (Dec 2023–) | by FZN                                                                | `ercot_load_by_fzn.py`, `ercot_load_archive.py`       |
| Temperature              | County temp (daily, legacy)        | **GRIDMET**                                                   | daily, per county                                                     | none — pre-existing `2_cleaned` parquet only, no scraper in repo |
| Temperature (hourly)     | Texas-statewide mean temp          | **ERA5** (Copernicus CDS reanalysis) — added 2026-07-21 per [[sources/2026-07-20_meeting-notes]] | hourly, Texas-statewide (masked to state boundary, not per-county) | `era5_ercot_temp_2021-2025.py`, checked via `00_check/02_era5_ercot_temp.ipynb` |
| NG — Henry Hub           | Spot                               | EIA `rngwhhdd`                                                | daily (corrected 2026-07-07; was mislabeled "hourly")                 | (to add — new scraper)                                |
| NG — Citygate / TX power | S. TX prices                       | EIA `ng_pri_sum_dcu_stx_m`                                    | monthly                                                               | (to add — new scraper)                                |
| MTLF                     | Mid-term load forecast             | Public API                                                    | hourly, by weather zone                                               | `parse_mid_term_load_forecast_parquet.py`             |
| DAM/RTM SPP (bulk)       | Excel report archives              | reports 13060 / 13061                                         | 15-min raw, aggregated hourly, by LZ/HB; post-2025 RTM continuation 2025-12-05 – 2026-10-24 (2026-10-25 posting) | `organize_lmp_parquet.py`, `organize_rtm_lmp_2026.py` |
| Price adders             | Reserve/adder prices               | **NP6-793-ER**                                                | 15-min, system-wide; post-2025 (RTC+B) series 2025-12-05 – 2026-10-24 (manual bulk download, report 13240 HIST, 2026-10-25 posting) | `parse_rtm_price_adders*.py`                          |
| Renewable generation (wind+solar) | Combined hourly Wind+Solar output | manual bulk download: `IntGenbyFuel20{20-22}.xlsx` (fuel mix, 15-min) + **PG7-126-M** "Hourly Aggregated Wind and Solar Output" (2023–2025 portion; report ID confirmed 2026-07-07) | hourly, 2020-01-01–2026-01-01 (52,614 rows) | `hourly_solar_wind_generation_2021_2025.ipynb` → `2_cleaned/generation/hourly_solar_wind_generation_2020_2025.parquet` |
| Non-renewable capacity | Generation capacity by fuel type (gas-cc + gas-other only; coal/nuclear/diesel excluded — together ~25% of thermal capacity, but no coal/nuclear and only minimal diesel is planned per ERCOT's forecast) | ERCOT [Capacity Changes by Fuel Type Charts](https://www.ercot.com/files/docs/2026/06/03/Capacity-Changes-by-Fuel-Type-Charts_May_2026.xlsx) (May 2026), decided 2026-07-06, reconfirmed 2026-07-07 | yearly, 2020–2025 | manual → `2_cleaned/generation/ERCOT nonRE capacity 2020-2025.csv` |
| Seven-Day Load Forecast by Model & Weather Zone | Per-model hourly load prediction, current day → 7 days ahead; day-ahead slice kept before DAM close | **NP3-565-CD**, live, hourly report cadence — identified 2026-07-07, extractor built 2026-07-14 | hourly, by weather zone, 7-day horizon (day-ahead slice extracted) | `ercot_mtlf_day_ahead.py` — trial pull only so far (`mtlf_day_ahead_trial.csv`); full extract not yet run |
| Seven-Day Load Forecast by Weather Zone | The **single official** hourly forecast (current day → 7 days ahead), 8 weather zones + `systemTotal`; **no** per-model/`inUseFlag` columns (that's the 565 variant above) | **NP3-561-CD** (Report Type ID 12312), **archive** (live returns 0 for 2023 — short rolling window) — added 2026-07-22 | hourly, by weather zone, 8-day snapshot reposted ~hourly | `ercot_7d_load_fcast_wzn_archive.py` — every posting kept, `postedDatetime` injected; **Aug 2023 run** → `01_data/1.2_raw_api/load_fcast_wzn_archive_20230801_20230831.parquet` (142,776 rows) |
| Resource outage capacity | Hourly aggregated outage MW; 3 categories: Total Resource (keep), IRR/wind+solar (drop), New Equipment (drop). Rolling 168-hr forward forecast, **not** realized actuals. **⭐ Enables spare-capacity v2:** outage MW in the denominator resolves the Uri exclusion. | **NP3-233-CD**, archive **2014-05→present** (verified 2026-09-26; extracted 2021→; live API Dec 2023– overlaps it) — added 2026-09-17. | hourly, system-wide (early 2021) / 4 zones South·North·West·Houston (after) | `ercot_outage_cap_archive_full.py` (archive, full range, 18 cols; job copy in `04_jobs/outage_cap_archive_full_sep24/`) — supersedes the sep19 live + archive pair. Raw: `1.2_raw_api/outage/outage_cap_archive_20210101_20260924.parquet` |

**NP3-233-CD archive format change (confirmed 2026-09-17):** The archive has two distinct
formats across time. **2021 and earlier:** 168 rows per doc, 5 system-wide columns
(`Date, HourEnding, TotalResourceMW, TotalIRRMW, TotalNewEquipResourceMW`), forward-only —
the hour-23 doc for date D contains only 1 row for D itself (HE 24); past hours are gone.
**2022–present:** 192 rows per doc, 14 per-zone columns, includes all 24 hours of the
posting date (historical + forward); the historical values are **identical to the live API**
(verified: zero drift on a test date). The data is a rolling forecast, not realized actuals —
each hourly posting revises the forward window. (Transition timing refined 2026-09-24 — see
correction below.) During Winter Storm Uri (Feb 15, 2021), the D−1
forecast showed ~12,000 MW of outages while the closest-to-real-time forecast reached ~31,000
MW — a 158% underestimate. On normal days, 1-hour-ahead forecasts overestimate actuals by
~6–17%. **Extraction strategy decided (2026-09-19, advisor-approved Option A):** use 1-hour-ahead
forecasts consistently across all years; store ALL archive postings as parquet; downstream
cleaning selects the 1h-ahead entries. 2022+ historical values serve as a validation metric
to quantify the 1h-ahead bias.
See `00_check/06_np3_233_cd_uri_forecast_drift.ipynb` for the drift analysis.

> ⚠️ CORRECTED 2026-09-24 (verified by API listing + one downloaded doc per era):
> - **Archive coverage runs to the present, not just 2023.** Doc counts: 8,758 (2024),
>   8,758 (2025), 6,387 (2026 through 09-24, latest posting 2026-09-24 09:00). The archive
>   and live API overlap from Dec 2023, and they agree exactly: the 2025-06-30 12:00 posting
>   matches on 192/192 rows with zero difference in all 4 zones. The earlier split (archive
>   to 2023-12-09, live after) came from our own assumption, not from an API limit.
> - **The column format changed earlier than the row count.** 2021-01-05 has 168 rows and
>   5 system-wide columns. 2021-06-01 already has the 14 per-zone columns but still 168
>   rows. 2023-12-15, 2025-06-01 and 2026-09-23 have 192 rows and 14 columns. So the
>   5 → 14 column switch happened between Jan and Jun 2021. Every era labels the date
>   column `Date` (MM/DD/YYYY), never `OperatingDate`.
>
> **Pipeline now:** one full-range archive job, `04_jobs/outage_cap_archive_full_sep24/`
> (2021-01-01 → 2026-09-24, 50,202 postings). It keeps all 12 per-zone columns
> (`total{Resource,IRR,NewEquipResource}MWZone{South,North,West,Houston}`) plus the
> system-wide totals `totalResourceMW`, `totalIRRMW` and `totalNewEquipResourceMW`. In
> early 2021 the totals come straight from the CSV; after that they are sums of the zones.
> The sep19 pair is superseded:
> - The live pull finished (`1.2_raw_api/outage/outage_cap_20231210_20260923.parquet`,
>   4,669,768 rows). It took ~27 h over 3 HPC attempts.
> - The sep19 archive parquet (4,846,200 rows) is unreadable (`Corrupt snappy compressed data`).
>
> **Full pull landed 2026-09-24** (verified 2026-09-25 by reading the parquet):
> `1.2_raw_api/outage/outage_cap_archive_20210101_20260924.parquet` — 9,541,728 rows,
> 18 cols, **50,202 postings** (2021: 8,759 · 2022: 8,756 · 2023: 8,759 · 2024: 8,782 ·
> 2025: 8,758 · 2026: 6,388), posted 2021-01-01 00:01 → 2026-09-24 10:00, operatingDate to
> 2026-10-01. 0 duplicate (posting, date, HE) keys; `totalResourceMW` has 0 NaN and equals the
> zone sum exactly in the zonal era. Exact format boundaries from the full data:
> - **System-wide-only (5-col) era = 2021-01-01 00:01 → 2021-05-27 16:01** (3,520 postings,
>   7.0%; per-zone columns NaN). Per-zone values start with the 2021-05-27 17:01 posting.
> - **168 vs 192 rows is not a clean switch:** first 192-row posting 2021-06-18 12:01, but
>   168-row postings recur until 2024-07-23 16:00 (4,044 postings total vs 46,158 at 192).
> - A local 2024 run of the `02_scripts` copy (`outage_cap_archive_20240101_20241231.parquet`
>   + 12 monthly `outage_cap_archive_parts/`) matches the 2024 slice of the full file
>   (1,686,120 rows, identical `totalResourceMW` sum).
> - **Use `totalResourceMW` for any full-period series** (verified 2026-09-26). In the
>   system-wide era the 4 `totalResourceMWZone*` columns are NaN (168 rows × 4 = 672 NaN per
>   posting), but `totalResourceMW` has 0 NaN (e.g. 7,754 MW for HE 1 in the 2021-01-01
>   00:01 posting). Selecting only the zone columns hides the whole Jan–May 2021 span,
>   Winter Storm Uri included, which is what cell 5 of `01_eda/09_outage_eda.ipynb` does.
>   Zone-level analysis can start only at the 2021-05-27 17:01 posting.
> - **Source quirks, not extraction bugs:**
>   - 110,291 negative values: 110,288 in `totalIRRMWZoneHouston` (≥ −8 MW, Aug 2025–Jan 2026)
>     and 3 in `totalIRRMWZoneSouth` (≥ −88 MW, Jun 2021). Resource columns are never negative.
>   - Posting cadence isn't strictly one per hour. 21 non-DST days have 22–23 postings, and
>     some hours have two (e.g. 2023-07-14 at 16:09:39 and 16:09:51). 1h-ahead selection has
>     to pick the latest posting before each hour, not assume one per hour.
>   - **One all-zero posting: `2024-07-23T16:00:00.000`** (docId 1022038164), verified
>     2026-09-26 against the raw CSV re-downloaded from ERCOT. All 168 rows × 12 numeric
>     columns are 0, and it covers only forward hours (07-23 HE 17 → 07-30 HE 16). It is the
>     only posting of 50,202 with:
>     - a timestamp of exactly `:00:00.000` (normal postings arrive ~:01);
>     - 168 rows after mid-2021 (the other 2024 postings have 192);
>     - all zeros (no posting has zeros in only some rows).
>
>     It takes the slot of the regular 16:01 posting, which is absent. The 15:01 and 17:01
>     postings are normal (4,002 / 4,112 MW mean over their forecast windows). In the 1h-ahead
>     series it hits only **2024-07-23 HE 17** (0 MW; excluding it gives 5,948 MW from the 15:01
>     posting). Drop postings whose `totalResourceMW` sums to 0 before selecting.
>   - **Hour-to-hour jumps > 3,000 MW in the 1h-ahead series are real.** All 26 fall at
>     midnight (HE 24 → HE 1) and the new level persists. Most are maintenance-season starts
>     (Mar 1–2 every year, Nov 1, mid-Oct); the rest are the Uri nights (Feb 16–18, 2021).
>     Max 6,746 MW (2025-03-01); p99.9 of |Δ| = 2,506 MW.
> - **Archive depth: 2014-05-01 → present** (API doc counts, 2026-09-26): 2014: 5,876 (first
>   posting 2014-05-01 00:00) · 2015: 8,755 · 2016: 8,783 · 2017: 8,756 · 2018: 8,758 ·
>   2019: 8,760 · 2020: 8,784. None of it is extracted yet (the pull starts 2021-01-01), and
>   the CSV format before 2021 hasn't been checked.
> - **The live parquet is kept for validation** (`outage_cap_20231210_20260923.parquet`, not
>   deleted). Over its window it matches the archive exactly (0 diff, all 4 zones). It has
>   known defects, likely because new postings kept arriving during the ~27 h, 3-restart
>   paging run:
>   - 13,949 duplicate (posting, date, HE) rows. Dedupe before use.
>   - It lacks 13,789 archive rows across 155 postings from 2026-09-14 on. Compare only before 2026-09-14.

The NP3-561-CD Aug-2023 pull was EDA'd 2026-07-24 in `02_analysis/00.0_load_fcast_wzn_aug2023`
— fills the "visual-check EDA notebook intentionally left for the human" gap noted when the
pipeline was built (2026-07-22). See [[mid-term-load-forecast]], [[notebook-catalog]].

Script architecture & behavior: [[extraction-scripts]].

> ⚠️ CONTRADICTION (resolved): legacy extraction used nodal **NP6-788-CD** for RTM LMP
> (`04_jobs/lmp_np6788cd*`, `organize_*lmp*.py`). The current data plan uses **report 13061
> (RTM SCED SPP by load zone)** instead. Keep NP6-788-CD nodal pulls only for the
> [[lmp-spp]] PA-vs-SPP validation; use 13060/13061 for zonal price/volatility series.

Access via ERCOT **Public API / EMIL** + bulk archive zips; shared helpers in
`ercot_common.py`. Large pulls run as batch jobs under `04_jobs/`. Mapping references in
[[load-zones]].

Extraction mechanics (auth, pitfalls, timeouts, EMIL, SLURM): [[data-extraction-guide]].
Pipeline from here to findings: [[analysis-workflow]].

> **Resolved 2026-07-10:** the 2026-07-06 raw drop (`01_data/1.1_raw_bulk/WindSolar Hourly Agg/`)
> now has a parser — see the "Renewable generation" row above. Output is a **system-wide,
> coarser-granularity** series (hourly, 2020–2026), distinct from the live by-geo wind/solar
> API pipeline already covered above and in [[wind-power-production]] (does not replace it).
>
> **Resolved 2026-07-17:** the downstream notebook that merges this renewable-gen series with
> load/price/capacity to compute the load-vs-firm-capacity ("spare capacity") metric
> (`(load − renewable_gen) / non_re_capacity`, [[sources/2026-07-06_weekly-meeting]]) is now
> `06_spare_capacity` (the earlier `06_metric_nonvariable_load_capacity`, broken on an
> incomplete-SQL cell, was deleted 2026-07-14 and replaced). The metric runs clean and
> correlates strongly with `log(rtm_price)` — see
> [[analysis/spare-capacity-correlates-with-rtm-price]], [[notebook-catalog]].

## Related
- [[ercot]] · [[rtm-dam]] · [[eia]] · [[ordc-price-adders]] · [[rtc-b-asdc]] · [[load-zones]]
- [[data-extraction-guide]] · [[analysis-workflow]] · [[notebook-catalog]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-07-06_weekly-meeting]] ·
  [[sources/2026-07-07_research-update]] · [[sources/2026-07-13_weekly-meeting-spare-capacity]]
- Outage-QC note (all thermal incl. coal vs. annual capacity; 1h-ahead only): [[sources/2026-09-30_meeting-notes]]
