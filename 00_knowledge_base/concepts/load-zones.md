---
title: Zone Geographies (LZ, weather, forecast, wind/solar regions)
aliases: [weather-zones, forecast-zones, wind-solar-regions, zone-geographies, settlement-geography]
type: concept
tags: [geography, settlement, ercot]
status: developing
sources: 0
updated: 2026-07-04
---

# Zone Geographies (LZ, weather, forecast, wind/solar regions)

**Canonical home for ALL ERCOT zone systems** — kept at the `load-zones` slug for link
stability; find it via the aliases above. ERCOT prices are spatial. Key geographies:
- **Load Zones (LZ)** — settlement zones for [[rtm-dam]] SPP (8 incl. NOIE).
- **Weather Zones** — geography for [[mid-term-load-forecast|MTLF]] (8, different boundaries).
- **Forecast Zones (FZN)** — geography for actual-load reporting (only 4).
- **Wind/Solar Regions** — geography for [[wind-power-production]] (6 wind / 7 solar).
- **Nodes** — granular LMP points (congestion shows up here).

Node→zone mapping is a real ETL step in this project (reference files under
`01_data/1.3_raw_other/mapping/`). Getting the mapping right is a prerequisite for clean
zonal price/volatility series.

⚠️ **Gap:** the new repo has no node→zone cleaning notebook — old `03_LZ_price_cleaning` was
dropped during migration, not renamed/kept. Rebuild if a fresh mapping-cleaning step is needed.

## Spatial price patterns
- **North LZ:** high price mean & variance (congestion + high demand).
- **West LZ:** low mean (low demand).
Congestion is the locational part of [[lmp-spp|LMP]]; aggregated into SPP by geography.

## Mapping references (inventoried 2026-07-03; all under `01_data/1.3_raw_other/mapping/`)
| File | Maps | Fields | Coverage |
|---|---|---|---|
| `ercot.gpkg` (layer `texas_county_loadzones`) | **LZ → county** (canonical) | `Counties`, `Load Zones`, `geom`, county codes (`FIPS_ST_CNTY_CD`, `CNTY_NBR`, TxDOT) | Complete: 214 counties × 8 zones — LZ_NORTH 52, LZ_SOUTH 57, LZ_WEST 80, LZ_HOUSTON 9 + NOIE LZ_AEN 1, LZ_CPS 2, LZ_LCRA 6, LZ_RAYB 7 |
| `LZ to Country Mapping.xlsx` | LZ → county (partial) | `Load Zone`, `County`, `Shared` | ⚠️ North only (55 counties, 13 shared); 2nd column block is an unlabeled 254-county list. Superseded by `ercot.gpkg` — don't use |
| `Wind and Solar Regions to County Mapping.xlsx` | wind/solar **region → county** | `Wind Region`\|`County`; `Solar Region`\|`County` (one sheet each) | Complete (source of the LZ_NORTH↔FarEast+CenterEast solar proxy) |
| `LZ-county-mapping.pdf`, `ERCOT-Maps_*.jpg` | visual reference maps | — | — |

- **Load zone → plant-level generation** (2021–2024): from Victoria Farella
  (`01_data/1.3_raw_other/Plant-level Generation/`).

> ⚠️ **Gap:** no **weather zone → county** mapping on record. The 8 weather zones (coast,
> east, farwest, ncent, north, scent, south, west) exist only as column names in the MTLF
> parquet. Fillable from ERCOT's published weather-zone county map — needed before joining
> [[mid-term-load-forecast]] / [[weather-hdd-cdd]] to LZ prices at county resolution.
> ⚠️ **Three distinct geographies — don't conflate:** load zones (8 incl. NOIE) ≠ weather
> zones (8, different boundaries) ≠ wind/solar regions (6 wind / 7 solar). MTLF is by weather
> zone; wind/solar production is by wind/solar region; SPP prices are by LZ. Actual load adds
> a fourth: **forecast zones** (only 4).

## Parquet schemas by geography (verified 2026-07-03, `01_data/1.2_raw_api/`)

**Weather zones (8)** — wide, one column per zone:
- `mid_term_load_forecast_20220201_20251130.parquet`: `operatingDay`, `hourEnding`,
  `forecast_{coast,east,farwest,ncent,north,scent,south,west,ercot}` (ercot = system total).
- `mid_term_load_forecast_error_20220201_20251130.parquet`: same layout, `error_*` columns.

**Load zones (8) + hubs (7)** — long, zone is a *value* in `settlement_point`:
- `rtm_lzhb_spp_2021_2026mar.parquet`: `delivery_date`, `hour_ending`, `delivery_interval`,
  `repeated_hour_flag`, `settlement_point`, `settlement_point_type`, `price`.
- `dam_lzhb_spp_2021_2025.parquet`: same minus `delivery_interval`, `settlement_point_type`.
- `settlement_point` values: `LZ_{NORTH,SOUTH,WEST,HOUSTON,AEN,CPS,LCRA,RAYBN}`,
  `HB_{NORTH,SOUTH,WEST,HOUSTON,PAN,BUSAVG,HUBAVG}`;
  `settlement_point_type` ∈ {LZ, LZEW, HU, SH, AH}.

**Forecast zones (4)** — wide:
- `load_fzn_20201231_20260526.parquet`: `timestamp`, `operatingDay`, `hourEnding`,
  `north`, `south`, `west`, `houston`, `total`, `DSTFlag`.

> ⚠️ **Join caveat:** the gpkg spells Rayburn `LZ_RAYB`; the price parquets use `LZ_RAYBN`.
> Same zone — normalize before any county-level join. And FZN load (4 zones) joins to LZ
> prices (8) or weather-zone forecasts (8) only approximately.

## Related
- [[rtm-dam]] · [[lmp-spp]] · [[wind-power-production]] · [[load-and-demand]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-06-30_ercot-market-concepts]]
