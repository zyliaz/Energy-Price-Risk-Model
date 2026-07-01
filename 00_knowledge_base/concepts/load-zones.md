---
title: Load Zones & Settlement Geography
type: concept
tags: [geography, settlement, ercot]
status: stub
sources: 0
updated: 2026-06-30
---

# Load Zones & Settlement Geography

ERCOT prices are spatial. Key geographies:
- **Load Zones (LZ)** — settlement zones for [[rtm-dam]] SPP.
- **Forecast Zones (FZN)** — geography for load forecasting.
- **Nodes** — granular LMP points (congestion shows up here).

Node→zone mapping is a real ETL step in this project (legacy `data/mapping`,
notebook `03_ercot_LZ_price_cleaning`). Getting the mapping right is a prerequisite for
clean zonal price/volatility series.

## Spatial price patterns
- **North LZ:** high price mean & variance (congestion + high demand).
- **West LZ:** low mean (low demand).
Congestion is the locational part of [[lmp-spp|LMP]]; aggregated into SPP by geography.

## Mapping references
- Wind/solar **region → county**: ERCOT "Wind and Solar Regions to County Mapping.xlsx" (2024-05).
- **Load zone → county**: from Victoria Farella.
- **Load zone → plant-level generation** (2021–2024): from Victoria Farella.
- ERCOT **load-zone shapefiles**.

## Related
- [[rtm-dam]] · [[lmp-spp]] · [[wind-power-production]] · [[load-and-demand]]

## Sources
- [[sources/2026-06-30_data-and-eda-notes]] · [[sources/2026-06-30_ercot-market-concepts]]
