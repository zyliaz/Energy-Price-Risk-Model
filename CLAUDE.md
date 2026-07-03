# CLAUDE.md — ERCOT/PJM Research Wiki Operating Manual

This repository holds a personal research project plus a **persistent, LLM-maintained
wiki** about it. When you (the LLM agent) work in this repo, you are the wiki's
maintainer. The human curates sources and asks questions; you do all reading,
summarizing, cross-referencing, filing, and bookkeeping.

Read this whole file at the start of every session.

---

## 1. The research

**Question:** What drives wholesale price volatility in **ERCOT**? Decompose how
load (incl. variable data-center demand), wind/solar output, natural-gas (Waha)
prices, weather, and ORDC scarcity **price adders** each contribute to real-time
(RTM) and day-ahead (DAM) price volatility.

> Scope note: This project began as an ERCOT-vs-PJM (energy-only vs capacity market)
> comparison. It has since narrowed to **ERCOT-only**, focused on the *drivers* of
> price volatility. PJM material is retained only as background/contrast, not as a
> primary axis. Do not create new PJM-centric pages unless the human re-expands scope.

**Working thesis** lives in `00_knowledge_base/00_overview.md` and evolves as
sources accumulate. Never let the thesis drift silently — when a source changes it,
update that page and note the change in the log.

---

## 2. Repository layout (three layers)

```
ERCOT-Research/
├── CLAUDE.md                  ← this file (the SCHEMA layer)
├── 00_knowledge_base/         ← the WIKI layer (you own this entirely)
│   ├── 00_overview.md         ← research overview + evolving thesis
│   ├── index.md               ← content catalog (update every ingest)
│   ├── log.md                 ← chronological append-only record
│   ├── entities/              ← markets, institutions, data sources, hubs
│   ├── concepts/              ← mechanisms, metrics, methods
│   ├── sources/               ← one page per ingested source (note/data/paper)
│   ├── analysis/              ← filed answers to your own queries / findings
│   └── assets/                ← downloaded images, figures referenced by pages
├── 01_data/                   ← RAW SOURCES layer (immutable; read, never edit)
│   ├── 1.1_raw_bulk/          ← bulk downloads (ERCOT archives)
│   ├── 1.2_raw_api/           ← API pulls (ERCOT public API / EMIL)
│   ├── 1.3_raw_other/         ← EIA, weather, third-party
│   ├── 2_cleaned/             ← cleaned/processed datasets
│   └── 3_analysis/            ← analysis-ready / derived datasets
├── 02_scripts/                ← extraction & transformation code
│   ├── 1_scrapers/            ← ERCOT-API extractors (+ ercot_common core)
│   └── 2_parsers/             ← excel→parquet + adder parsers
├── 03_notebooks/              ← EDA & analysis notebooks
│   ├── 00_check/              ← prelim API-check notebooks (run before building any extractor)
│   ├── 01_eda/
│   └── 02_analysis/
└── 04_jobs/                   ← long-running batch jobs (downloads, archives)
```

The three layers from the LLM-wiki pattern map as:
- **Raw sources** = `01_data/` (+ notebooks/scripts as derived artifacts). Immutable.
- **Wiki** = `00_knowledge_base/`. You create, update, and maintain every file here.
- **Schema** = this `CLAUDE.md`. Co-evolve it with the human as conventions settle.

---

## 3. Page conventions

Every wiki page starts with YAML frontmatter so Obsidian Dataview can query it:

```markdown
---
title: ORDC Price Adders
type: concept            # one of: overview | entity | concept | source | analysis
tags: [pricing, scarcity, ercot]
status: stub             # stub | developing | stable
sources: 3               # how many ingested sources inform this page
updated: 2026-06-30
---

# ORDC Price Adders

One-paragraph definition / summary up top.

## ...sections...

## Related
- [[rtm-dam]]
- [[price-volatility]]

## Sources
- [[sources/2026-06-30_my-note-on-adder-spikes]]
```

Rules:
- **Filenames:** lowercase-kebab-case (`energy-only-vs-capacity.md`). Source pages:
  `YYYY-MM-DD_short-slug.md`.
- **Links:** use Obsidian wikilinks `[[page-slug]]`. Every page should have inbound
  AND outbound links — no orphans.
- **One concept/entity per page.** Split rather than let pages sprawl.
- **Cite everything.** Claims trace back to a `sources/` page or a named dataset/notebook
  in `01_data` / `03_notebooks`.
- **Flag contradictions inline** with `> ⚠️ CONTRADICTION:` and log them.

---

## 4. Operations

### Ingest (a new note, dataset, paper, or URL)
1. Read the source fully. If it's a dataset, inspect schema + a sample, don't ingest blindly.
2. Discuss key takeaways with the human before writing.
3. Create `sources/YYYY-MM-DD_slug.md` summarizing it (what it is, key facts, where the
   raw file lives, why it matters to the thesis).
4. Update every affected entity/concept page. A single source may touch 5–15 pages.
5. Note contradictions with prior claims; strengthen or revise the synthesis in `00_overview.md`.
6. Update `index.md`. Append one line to `log.md`.

### Query (the human asks a question)
1. Read `index.md` first to locate relevant pages, then drill in.
2. Synthesize an answer **with citations** to wiki pages and underlying data.
3. If the answer is reusable (a comparison, a finding, a connection), file it in
   `analysis/` as a new page so it compounds. Update index + log.

### Lint (periodic health check)
Scan for: contradictions, stale claims newer data supersedes, orphan pages, important
concepts mentioned but lacking a page, missing cross-references, and data gaps fillable
by a web search or a new ERCOT/EIA pull. Report findings + suggest next questions/sources.

---

## 5. Logging

`log.md` is append-only. Each entry begins with a consistent prefix so it's grep-able:

```
## [2026-06-30] ingest | Price-adder spike note (Apr 2026)
## [2026-06-30] query  | How do ORDC adders correlate with RTM load?
## [2026-06-30] lint   | Found 2 orphan pages, 1 stale NG-price claim
```

`grep "^## \[" 00_knowledge_base/log.md | tail -5` gives recent activity.

---

## 6. Domain glossary (so pages stay consistent)

- **RTM / DAM** — Real-Time Market (5-min/15-min) vs Day-Ahead Market.
- **LMP / SPP** — Locational Marginal Price (nodal) / Settlement Point Price.
- **LZ / Load Zone** — ERCOT settlement geography; also "FZN" (forecast zone).
- **WPP** — Wind Power Production (actual/forecast).
- **ORDC** — Operating Reserve Demand Curve; drives scarcity **price adders** (RTORPA/RTOLCAP).
- **Energy-only market** — ERCOT recovers fixed costs through scarcity energy prices
  (no capacity payments); makes ORDC adders central to volatility. (PJM's capacity
  market kept only as background contrast.)
- **Waha** — West Texas natural gas hub; NG price driver for ERCOT.
- **HDD / CDD** — Heating / Cooling Degree Days (weather → load).
- **EMIL / Public API** — ERCOT data delivery endpoints (report IDs like NP6-788-CD).

Keep this list current; add terms as the wiki grows.

---

## 7. House style
- Concise, evidence-first prose. Tables/charts where they clarify.
- Never edit `01_data/` raw files. Derived outputs go to `2_cleaned` / `3_analysis`.
- When unsure how to file something, ask — then write the convention into this file.
- **No redundancy.** One canonical home per fact; if two pages overlap, keep one and link.

## 8. Keep the wiki in sync (standing rule)
**Any addition or change to the repo updates the wiki in the same session** — no drift.
Triggers → what to update:
- New/changed **script** → [[extraction-scripts]] (+ [[ercot-data-products]] if a new dataset).
- New/changed **notebook** → [[notebook-catalog]].
- New **data source/file** → [[ercot-data-products]], [[analysis-workflow]] lineage, and the
  relevant driver page.
- New **finding** → the concept page + `00_overview` thesis if it shifts.
- New **data pipeline** (scraper/parser/job) → in the **same session**, append any caveats or
  mistakes-to-avoid discovered while building it to [[data-extraction-guide]] "Top pitfalls"
  (concise + precise; one canonical entry, no duplicates), and correct any coverage/schema
  claim the build disproved. Every pipeline starts with a `00_check` endpoint notebook the
  human reviews before the extractor is written.
- Structure/convention change → this `CLAUDE.md`.
Always finish by updating `index.md` and appending one line to `log.md`.

**Enforced by hooks** (`.claude/settings.json`):
- `SessionStart` → `wiki_drift_check.sh` compares the repo against the last-seen commit +
  working tree; if content dirs changed **outside a session**, it lists them and prompts a
  wiki reconcile. (Marker: `.claude/.wiki_sync_state`, gitignored.)
- `UserPromptSubmit` → `new_source_checklist.sh` injects [[new-source-checklist]] when a
  data-source task is detected.
- `PostToolUse` (Write/Edit) → `wiki_sync_reminder.sh` reminds you to sync the right catalog
  page + `index.md`/`log.md` after any change under `01_data/`, `02_scripts/`,
  `03_notebooks/`, or `04_jobs/`.

## 9. Sync Notion meeting notes → wiki (standing rule)
The human logs meetings in the Notion **Meeting Notes & Insights** ("Notes") database. Every
new note must be reconciled into the wiki. Detection is **self-tracking**: a note is "new" if
there is no `sources/YYYY-MM-DD_slug.md` page for it yet.

Procedure per new note:
1. `notion-search` (scoped to the Notes data source) to list notes; `notion-fetch` each
   note's full page (Notes / Insights / Action items).
2. Create `sources/YYYY-MM-DD_meeting-slug.md` summarizing it.
3. Push each **insight** into the relevant concept page(s) + revise `00_overview` thesis /
   open questions if direction shifts.
4. Mirror **action items** to the Notion **To-dos** database (map to an `Area`).
5. Update `index.md`; append one `log.md` line.

Runs at session start and/or via the scheduled task. Uses `notion-search`+`notion-fetch`
(the SQL `query-data-sources` tool needs a paid Notion plan).
