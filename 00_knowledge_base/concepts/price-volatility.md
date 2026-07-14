---
title: Price Volatility
type: concept
tags: [pricing, metric, core]
status: developing
sources: 0
updated: 2026-06-30
---

# Price Volatility

The central dependent variable of this research: variation in ERCOT wholesale prices
over time. "Volatility" needs an explicit operational definition before analysis.

## Candidate measures (decide & document)
- Rolling standard deviation / coefficient of variation of [[rtm-dam]] prices.
- Spike frequency & magnitude (e.g. share of intervals above $/MWh thresholds).
- RTM–DAM spread and its dispersion.
- Realized volatility from high-frequency (5/15-min) SCED prices.

## Drivers (per EIA "Sources of Price Volatility in the ERCOT Market")
1. **Energy cost, esp. natural gas** — [[natural-gas-prices]] (marginal fuel).
2. **Growth in peak demand** — [[load-and-demand]].
3. **Availability of renewables (wind)** — [[wind-power-production]].

Plus the project's mechanism-level drivers:
- [[ordc-price-adders]] — discrete scarcity spikes (suspected dominant driver; ORDC pre-2025,
  [[rtc-b-asdc|ASDC]] post-2025).
- [[weather-hdd-cdd]] — upstream load driver.
- [[lmp-spp]] — congestion/locational component.

## Spatial & temporal patterns (concept note)
- **North LZ:** high mean & variance (congestion + high demand); **West LZ:** low (low demand).
- Online-reserve adders fire under **low-wind / high-demand**; **minimal adders on summer
  days** even at high demand. See [[load-zones]].

## Notes
- Distinguish *fundamental* volatility (smooth load/fuel) from *scarcity* volatility
  (adder-driven jumps); the thesis is that the latter dominates. See [[00_overview]].
- **Regime break Dec 2025** (RTC+B): treat pre/post separately. See [[rtc-b-asdc]].
- **Extreme outlier Feb 2021**: [[winter-storm-uri]] dominates the right tail of any
  pre-2025 volatility measure; handle explicitly.

## Related
- [[ordc-price-adders]] · [[rtm-dam]] · [[load-and-demand]] · [[wind-power-production]] · [[lmp-spp]] · [[rtc-b-asdc]]

## Sources
- [[sources/2026-06-30_ercot-market-concepts]] · [[sources/2026-06-30_data-and-eda-notes]]
