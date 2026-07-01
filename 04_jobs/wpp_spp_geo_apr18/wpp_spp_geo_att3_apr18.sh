#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=120:00:00
#SBATCH --mem=9000m
#SBATCH --chdir=/work/users/z/y/zylia/wpp_spp_geo_apr18/
set -euo pipefail
module purge
module add anaconda
export ERCOT_USERNAME=zyliduck4758@gmail.com
export ERCOT_PASSWORD=nMzjXcDL9YNut3s
export ERCOT_SUBSCRIPTION_KEY=785acf313e33461497f7ba49bfcf5a43
python -c "import pandas, requests, pyarrow" >/dev/null
# WPP: writes _raw.parquet (all revisions), then deduplicates to clean parquet.
# Assertion checkpoints: trial schema, zero rows, past-date nulls (DST/boundary warned; unexplained raised).
python ercot_wpp_by_geo.py --auto --from 2021-01-01
# SPP: same snapshot/revision model as WPP — same dedup and assertion logic.
python ercot_spp_by_geo.py --auto --from 2021-01-01
