---
title: Research Meeting (advisor)
type: source
tags: [meeting, direction, modeling, net-load]
status: developing
date_ingested: 2026-07-01
source_kind: note
raw_path: Notion — Meeting Notes & Insights ("research meeting", 2026-07-01)
updated: 2026-07-01
---

# Research Meeting (advisor) — 2026-07-01

Direction-setting meeting. Synced from the Notion Meeting Notes DB.

## Notes
- **Direction:** stats model first, for **scenario identification**.
- **Deliverable:** academic paper or white paper / conference poster / git repo.
- **Modeling discussion:** load prediction; load vs `log(rtm price)`; load vs temperature.

## Insights
- **Forecast puzzle:** load-forecast **over-prediction coinciding with high prices doesn't
  make sense** — investigate. (cf. [[mid-term-load-forecast]] finding that log(price) vs
  forecast error is weak.)
- **Total load is increasing significantly** — HDD EDA shows load vs temp with a quadratic
  fit trending up over the years. See [[weather-hdd-cdd]], [[load-and-demand]].
- **Monthly slices:** `log(price)` vs load correlates more strongly in **summer months**
  (ref notebook `05_load_rtm_price_plot`). See [[load-and-demand]], [[price-volatility]].
- **Net load:** add a **renewable generation pipeline** — modeling on **load − solar − wind**
  should perform better than raw load. See [[feature-engineering]], [[wind-power-production]].

## Action items
- [ ] Build **solar + wind generation pipeline** (→ net load). [[extraction-scripts]]
- [ ] **Day-ahead** correlation analysis. [[rtm-dam]]
- Mirrored to the Notion To-dos database.

## Why it matters to the thesis
Shifts the modeling target toward **net load** and **monthly/seasonal** structure, sets a
stats-first, scenario-identification framing, and fixes the deliverable. Updates
[[00_overview]].

## Affected wiki pages
[[00_overview]], [[load-and-demand]], [[mid-term-load-forecast]], [[weather-hdd-cdd]],
[[wind-power-production]], [[feature-engineering]], [[rtm-dam]]
