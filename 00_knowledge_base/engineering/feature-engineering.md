---
title: Feature Engineering
type: engineering
tags: [methods, features]
status: developing
sources: 6
updated: 2026-10-02
---

# Feature Engineering

Derived variables used in the volatility analysis. Keep definitions here so notebooks stay
consistent.

| Feature | Definition | Notes |
|---|---|---|
| **Adder demand** | load forecast − actual load | Available from 2021. Proxy for unexpected tightness. See [[mid-term-load-forecast]]. ⚠️ No correlation with RTM price (dropped from modeling 2026-07-27). |
| **CDD / HDD** | actual temp − 65°F (cooling) / 65°F − actual temp (heating) | Must use **hourly resolution, full decimal precision** (not rounded). See [[weather-hdd-cdd]]. |
| **Capacity factor (C.F.)** | wind/solar production ÷ capacity | From production series. See [[wind-power-production]]. |
| **Net load** | load − (wind + solar) | **Preferred modeling target (2026-07-01)** — expected to model price better than raw load. Combined wind+solar series now exists ([[ercot-data-products]]) but no notebook has computed net load from it yet. |
| **Time of day** | hour-of-day, categorical (discrete factor) | Added 2026-07-21. Retained as factor (not continuous) for modeling — captures time-of-day peak/off-peak effects. |
| **NG price (monthly)** | Henry Hub natural gas $/MMBtu | **Renamed 2026-07-31** to `ng_price_monthly` to clarify intra-daily constancy (monthly settlements); was `ng_price`. See [[natural-gas-prices]]. |
| **Spare capacity (v1)** | `(load − renewable_gen) / non_re_capacity` | v1 (2026-07-14). Correlates strongly with log(price) (R²=0.552 OLS, spare_capacity coef ≈+115). Computed in `06_spare_capacity`. **Uri excluded** because load curtailment breaks the metric. ⚠️ Caveat: ~25% of thermal capacity (coal/nuclear/diesel) excluded; see [[sources/2026-07-07_research-update]]. |
| **Spare capacity (v2)** | `(load − renewable_gen) / (thermal_capacity − outage_MW)` | ⭐ v2 (2026-09-17). Incorporates hourly resource outage capacity (**NP3-233-CD**, "Total Resource" category only — excludes IRR/new-equipment). **Resolves the Uri exclusion:** during the storm, massive outages collapsed effective capacity harder than load curtailment reduced the numerator, so the metric spikes correctly at extreme prices. Enables modeling the full 2021–present range without excluding Uri. |
| **Cap threshold** | `spare_capacity > 0.9`, categorical binary | Added 2026-07-27. Captures adder activation effect; avoids modeling adders explicitly (pre-Dec-2025 adders built-in at threshold). |

## Datetime convention — project standard: **hour-ending (HE)**
Every hourly/merged series uses **hour-ending** timestamps. A row stamped `HH:00` covers the
interval **ending** at that clock time (`05:00` = the 04:00–05:00 hour). This is the single
join key across load, RTM price, MTLF, generation, and price adders — merge on the raw clock
value, no shifting.

Native ERCOT feeds are almost all already HE: the `HourEnding` field (load, forecasts, WPP/SPP)
and the HE-numbered `Delivery Hour` 1–24 (RTM LMP/adders, where Hour 1 = the hour ending 01:00).
The **only** hour-starting raw source is the 2020–2022 fuel-mix generation file
(`IntGenbyFuel20YY.xlsx`), shifted `+1h` in `hourly_solar_wind_generation_2021_2025`.

Conversion recipes (date + HE → datetime):
- **HE string** `"HH:00"`/`"H:00"`: `date + pd.to_timedelta(HE.str.split(':').str[0].astype(int), 'h')`
  (or use the source's native `timestamp` column, as the load parquet does).
- **HE-numbered index** (RTM `Delivery Hour`): hourly HE = `date + DeliveryHour·1h`. Keep the
  15-min series as interval-**beginning** atomic truth
  (`date + (DeliveryHour−1)·60min + (DeliveryInterval−1)·15min`), then label the hourly
  aggregate HE with `DATE_TRUNC('hour', ts) + INTERVAL 1 HOUR`.
- **Hour-starting raw** (2020–22 fuel mix): build the HS timestamp, then add `+1h`.
- Always drop DST duplicates first (`repeatHourFlag`/`DSTFlag = False`); see
  [[data-extraction-guide]] pitfalls #5–6.

**Standardization (2026-07-23):** RTM price adders and RTM LZ/HB SPP were previously
hour-**starting**, which forced a manual `−1h` patch in `02_price_adder_activation` /
`03_new_pa_activation` and silently misaligned `04_price_adder_rtm_load_correlation` by one hour.
Resolved: adder hourly aggregation now emits HE (`+ INTERVAL 1 HOUR` in the `04`/`06` cleaning
notebooks); `organize_rtm_lmp_2026.py` builds `date + DeliveryHour` (not `−1`); the `−1h` patches
were removed from notebooks 02/03. The 15-min adder parquet is unchanged (interval-beginning).
Aligned adder-vs-RTM correlation sits at its shift maximum (0.831), confirming alignment.

## Features evaluated and removed

**Dropped 2026-08-03:**
- **`total_load` and `perc_load`:** Both highly correlated with `spare_capacity` (which itself is `(load − renewable_gen) / capacity`). Removed to avoid multicollinearity in regression; spare_capacity alone captures load effects.

## Modeling refinements (deferred)

Per [[sources/2026-08-03_research-meeting]], experimental tweaks proposed for future exploration:

- **Binary heating/cooling variable:** Categorical indicator (heating months vs. cooling months) to try in place of the multi-category `season` variable.
- **Tail-behavior models:** Explore logistic, polynomial, or piecewise regression for lower price tail.
- **Log-10 loss function:** Alternative to log-scale linear regression.
- **Year baseline (2025):** Use 2025 as the reference year.

## Open / to-add
- Price-volatility target definition (see [[price-volatility]]) — rolling std, spike flags.
- Region/zone aggregation using mappings in [[load-zones]].
- **Alt-forecast-model columns (2026-07-03):** 7 alt MTLF models (A3/A6/E/E1/E2/E3/M) parsed
  per zone as raw load-prediction columns — see [[mid-term-load-forecast]]. Previously EDA'd
  in `09_mtlf_models_eda` (exported ERCOT-only as `Hourly_ERCOT_all_models_*.csv`); that
  notebook was **deleted** as of this session (2026-07-24, uncommitted working-tree change).
  **Reason (human, 2026-07-24): a different data source will be used for this** — not
  simply dropped, superseded by a planned replacement (not yet built). Not currently used
  downstream in any `02_analysis` notebook.
- **Spare-capacity ratio (`spare_capacity`, resolved 2026-07-17; v2 2026-09-17):**
  - **v1:** `(load − renewable_gen) / non_re_capacity`, proposed in
    [[sources/2026-07-06_weekly-meeting]], refined in
    [[sources/2026-07-13_weekly-meeting-spare-capacity]]. Computed cleanly (Uri excluded) in
    `06_spare_capacity` and correlates strongly with `log(rtm_price)`. ⚠️ Caveat (2026-07-07,
    still open): `non_re_capacity` covers gas-CC + gas-other only — coal/nuclear/diesel (~25%
    of thermal capacity) are excluded.
  - ⭐ **v2 (2026-09-17):** `(load − renewable_gen) / (thermal_capacity − outage_MW)`.
    Hourly outage data from **NP3-233-CD** ("Total Resource" category, the system-wide
    **`totalResourceMW`** column, since the zone columns are NaN before 2021-05-27 17:01)
    enters the denominator. **Resolves the Uri exclusion problem:** v1 had to drop
    Feb 2021 because load curtailment broke the load→price relationship (load dropped but
    prices were at the $9,000/MWh cap). In v2, the denominator collapses during Uri (roughly
    half of generation offline), so the metric spikes correctly even with reduced load. The
    full 2021–present dataset can now be modeled without excluding Uri. Posting selection:
    the **1-hour-ahead** posting for every (date, HE), consistently across all years
    (advisor-approved Option A, 2026-09-19). This supersedes the hour-23-report rule in
    [[sources/2026-09-16_np3-233-cd-outage-data]], which fails for 2021 (the hour-23 doc
    holds only HE 24 of its own day). See [[ercot-data-products]].
    **1h-ahead selection as implemented** (`01_eda/09_outage_eda`, 2026-09-26):
    - `datetime = operatingDate + hourEnding h` (HE end; HE 24 → next-day 00:00).
    - Keep the **latest posting with `postedDatetime < datetime`**. Postings from 2022 on
      repeat earlier hours of their own day, and later postings re-list hours that have
      passed, so without this cutoff the selection picks after-the-fact values.
    - Trim to `datetime ≤ ceil(last posting)`. Without it, the last posting's 7-day forecast
      tail adds 180 hours at up to ~181 h lead.
    - Drop the all-zero posting first (see [[ercot-data-products]]).

    Result: 50,219 hours (2021-01-01 01:00 → 2026-09-24 11:00), no gaps or duplicates, and an
    independent rebuild matches exactly. Lead time: median 58.2 min, std 1.8. 29 hours
    exceed 61 min (skipped ERCOT postings; max 178 min at 2021-05-26 HE 18); 6 are under
    30 min (late postings; min 7 min). Output:
    `2_cleaned/outage/archive_1h_ahead_outage_20210101_2026_0924.parquet`
    (`datetime`, `totalResourceMW`). As of 2026-09-26 that file still has 0 MW at
    2024-07-23 HE 17 (the zero posting was not yet excluded). Monthly means peak in the
    shoulder seasons (Apr 26.9k, Nov 22.5k MW) and bottom out in summer (Aug 7.4k MW).
    Uri 1h-ahead peak: 32,379 MW at 2021-02-16 HE 8.
  - **Regression status (updated 2026-09-02):** `01_regression_data.ipynb` is a
    **dataset-export + correlation-plot** notebook (duckdb merge via hourly ERCOT data sources;
    exports `01_data/4_model/raw_model_dataset.csv`; re-verified PASS 2026-08-07). Companion R script `02_linear_regression.Rmd`
    performs exploratory correlation/year-stratified analysis. Load features (`total_load`, `perc_load`) removed
    2026-08-03 due to high collinearity with spare_capacity.
  - **Data cutoff (2026-09-02):** modeling uses **2021–2025 only**, with the **pre-Dec-2025
    (ORDC) adder scheme**. The post-Dec-2025 RTC+B adder data exists (cleaned in
    `06_new_pa_cleaning`, EDA'd in `07_new_pa_distribution` / `03_new_pa_activation`) but is
    excluded from regression because several upstream inputs lack 2026 coverage: generation
    (solar+wind parquet ends Dec 2025), non-RE capacity (no 2026 row), ERA5 hourly temperature
    (ends Jan 2026), peak hours (ends Dec 2025), and NG price (partial, only Jan–Feb 2026).
    Extending to the post-2025 regime requires re-running those scrapers / adding 2026 data
    first.
  - ⚠️ **Degree-days / spare-capacity collinearity (flagged 2026-07-20, open):** both
    `degree_days` and `spare_capacity` are driven by load, so they're correlated with each
    other, not just with price. Per [[sources/2026-07-20_meeting-notes]], because the model
    is meant for **scenario simulation**, this confound needs to be isolated (e.g.
    orthogonalized or interaction-modeled) before the coefficients can be read as
    independent causal effects — not yet implemented in `mod1`.
  - ✅ **Timezone bug affecting `degree_days` (found and fixed 2026-07-24):** the ERA5
    hourly temperature feed used for `degree_days` in `06_spare_capacity` and
    `01_regression_data` is natively **UTC**; both notebooks now convert `df_temp`'s
    `datetime` to `America/Chicago` (matching the project's hour-ending Central convention
    below) immediately after loading and before the join — the raw ERA5 scraper/files stay
    UTC, unchanged, per the human's request not to re-touch already-scraped data. Re-verified
    via fresh `nbconvert --execute`, both PASS. `degree_days`↔`rtm_price` correlation:
    0.184 overall; `degree_days`↔`spare_capacity`: 0.579 (both driven by load, per the
    collinearity note below). See [[weather-hdd-cdd]].

## Outage denominator mismatch (2026-09-30)
Per [[sources/2026-09-30_meeting-notes]]: the NP3-233-CD outage series covers all thermal capacity including coal, but the annual `non_re_capacity` table does not, so `thermal_capacity − outage_MW` can understate effective capacity. To check: that retired plants do not appear as outage (baseline level + retirements). The outage input is the 1h-ahead archive series only. Notebooks `02_analysis/06.1`, `06.2` and `03_model/01.1_model_data_v2` implement the outage-aware metric (see [[notebook-catalog]]).

## Related
- [[load-and-demand]] · [[weather-hdd-cdd]] · [[wind-power-production]] · [[price-volatility]]
- [[analysis/spare-capacity-correlates-with-rtm-price]] · [[notebook-catalog]]

## Sources
- [[sources/2026-07-01_research-meeting]] · [[sources/2026-07-07_research-update]] ·
  [[sources/2026-07-13_weekly-meeting-spare-capacity]] ·
  [[sources/2026-07-14_capacity-model-research-update]] ·
  [[sources/2026-07-20_meeting-notes]] · [[sources/2026-07-27_modeling-strategy-update]] ·
  [[sources/2026-08-03_research-meeting]]
