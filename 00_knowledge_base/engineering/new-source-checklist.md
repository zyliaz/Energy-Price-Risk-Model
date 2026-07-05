---
title: New-Source Checklist
type: concept
tags: [methods, workflow, checklist]
status: stable
updated: 2026-06-30
---

# New-Source Checklist

Copy-paste todo for adding a data source. Detail: [[data-extraction-guide]] ·
[[analysis-workflow]] · [[extraction-scripts]].

```
[ ] 1 INSPECT   00_check/ — EMIL Phase 1: GET product → GET endpoint → fields/type/hasRange/range
[ ] 2 EXTRACT   1_scrapers/ercot_<name>.py (copy a template; use ercot_common) → 1.2_raw_api/*.parquet
                 live=single-pass paginate · archive=list+download · big=04_jobs/ SLURM --auto
[ ] 3 AGGREGATE 01_eda cleaning cell or 2_parsers/ → 2_cleaned/*.csv  (one source; time/space aggregate)
[ ] 4 EDA       01_eda/NN_<name>.ipynb — distribution, tail, seasonality (single source)
[ ] 5 MERGE     02_analysis/NN_<name>.ipynb — merge on datetime → 3_analysis/*.csv
```

**Check every source (pitfalls):**
```
[ ] auth uses id_token (not access_token) + Ocp-Apim-Subscription-Key
[ ] range strategy right (monthly-chunk LMP · single-pass load/wind/solar)
[ ] timestamps: ISO vs MM/DD/YYYY · 24:00→next day · sub-minute LMP→resample hourly
[ ] DST: repeatHourFlag/DSTFlag=FALSE; row count sane (~8760/yr hourly)
[ ] zones: price LZ ≠ forecast ≠ wind ≠ solar — resolve by county mapping
[ ] archive: normalize columns/flags to live schema; keep price extremes
```

**Conventions:** files `*_YYYYMMDD_YYYYMMDD`; raw immutable; read from `01_data/{1.2_raw_api,
2_cleaned,3_analysis}`; register the source in [[ercot-data-products]]; log it.

> Auto-surfaced by the `UserPromptSubmit` hook (`.claude/hooks/new_source_checklist.sh`) when
> a data-source task is detected. The `PostToolUse` hook reminds you to sync the wiki after
> file additions (CLAUDE.md §8).

## Related
- [[analysis-workflow]] · [[data-extraction-guide]] · [[extraction-scripts]] · [[ercot-data-products]]
