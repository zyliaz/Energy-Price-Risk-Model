# ERCOT Research — Drivers of Price Volatility

Research repo + LLM-maintained wiki on what drives wholesale price volatility in ERCOT
(load, wind/solar, natural gas, weather, ORDC/ASDC scarcity adders).

- **Wiki:** `00_knowledge_base/` — start at `index.md` and `00_overview.md`.
- **Operating manual:** `CLAUDE.md` (how the wiki is structured & maintained).

## Layout
```
00_knowledge_base/  wiki (overview, concepts, sources, analysis)
01_data/            1.1_raw_bulk · 1.2_raw_api · 1.3_raw_other · 2_cleaned · 3_analysis
02_scripts/         1_scrapers · 2_parsers
03_notebooks/       00_check · 01_eda · 02_analysis
04_jobs/            individual SLURM/HPC jobs
```

## Quickstart
```bash
bash setup_env.sh && source .venv/bin/activate
cp .env.example .env            # fill in ERCOT_USERNAME / PASSWORD / SUBSCRIPTION_KEY
set -a && source .env && set +a
cd 02_scripts/1_scrapers && python ercot_load_by_fzn.py --trial-only
```

## Adding a new data source
Follow the 5-step pipeline — inspect → extract → aggregate → analyze single → merge across.
See `00_knowledge_base/concepts/analysis-workflow.md` and `data-extraction-guide.md`
(auth, endpoints, pitfalls, timeouts, EMIL, jobs convention). Use
`03_notebooks/00_check/00_emil_api_check.ipynb` for step-1 inspection and
`02_scripts/1_scrapers/ercot_load_by_fzn.py` as the extractor template (shared client/writer
live in `ercot_common.py`).
