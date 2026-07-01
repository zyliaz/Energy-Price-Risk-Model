---
title: ERCOT Data Extraction Skill Reference
type: source
tags: [data, extraction, api, methods]
status: stable
date_ingested: 2026-06-30
source_kind: note
raw_path: old repo — ercot_data_extraction_skill.md (+ .claude/.../memory/, worktree CLAUDE.md)
updated: 2026-06-30
---

# ERCOT Data Extraction Skill Reference

Project know-how distilled from the old repo's `ercot_data_extraction_skill.md` (462 lines),
the agent **memory** (`MEMORY.md`, HPS-jobs feedback), and the legacy worktree `CLAUDE.md`.
Captures the extraction patterns and hard-won pitfalls so they survive the migration.

## What it is
A non-member-tier playbook for ERCOT Public API extraction (price, load, wind/solar), 2021–
present, zone/system resolution. Twelve sections: auth, trial-first, pagination, timestamp/DST,
zone mapping, archive-vs-live, memory-efficient writes, quality checks, source quick-reference,
timeouts/estimation, lessons learned, and the EMIL self-describing two-phase + SLURM workflow.

## Key facts distilled (full playbook → [[data-extraction-guide]])
- **Auth:** B2C ROPC → **`id_token`** (not `access_token`) + `Ocp-Apim-Subscription-Key`.
- **Endpoints:** RTM LMP NP6-788-CD (live Dec-2023+, archive 2021–23); load NP6-346-CD,
  wind NP4-742-CD, solar NP4-745-CD (all live 2021+); bulk SPP 13060/13061; adders NP6-793-ER.
- **Pitfalls:** zone systems don't align; archive≠live (US dates, `Y/N` flags, nested zips,
  cased columns); `24:00` hour-ending; monthly-chunk returns 0 on load/wind/solar; DST
  missing/dup hour; sub-minute LMP offsets; keep price extremes.
- **Ops:** stream pages→parquet (chunk writer); timeouts 10/60/180/240 s; raise sleep not
  timeout on 429; EMIL self-describes via 2 GETs; SLURM jobs self-contained + `--auto`.
- **Memory convention:** all HPC scripts live in `jobs/` (now `04_jobs/`), one `.sh` per job,
  named `<dataset>_<date>.sh`, co-located with their Python extractor.
- **Legacy focus:** old work centered on `LZ_NORTH`; stack is Python · DuckDB · pandas · pyarrow.

## Naming correction logged
`ercot_spp_by_geo.py` = **Solar Power Production** (NP4-745-CD), not Settlement Point Price —
"SPP" is overloaded. Price SPP lives in [[lmp-spp]].

## Why it matters to the thesis
Extraction quality (DST, zone mapping, archive normalization) directly determines whether the
volatility series are trustworthy. This is the methods backbone for every [[price-volatility]]
driver dataset.

## Affected wiki pages
[[data-extraction-guide]], [[analysis-workflow]], [[ercot-data-products]], [[load-zones]],
[[notebook-catalog]]
