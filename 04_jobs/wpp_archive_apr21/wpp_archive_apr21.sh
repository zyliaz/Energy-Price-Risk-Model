#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=2:00:00
#SBATCH --mem=9000m
#SBATCH --chdir=/work/users/z/y/zylia/
set -euo pipefail
module purge
module add anaconda
export ERCOT_USERNAME=zyliduck4758@gmail.com
export ERCOT_PASSWORD=nMzjXcDL9YNut3s
export ERCOT_SUBSCRIPTION_KEY=785acf313e33461497f7ba49bfcf5a43
python -c "import pandas, requests, pyarrow" >/dev/null
# Archive backfill: 2021-01-01 → 2023-11-30 (~743 docs/month × 35 months ≈ 26k docs)
# Est. runtime: ~16–21 min. Deduplicates in-process (no _raw intermediate).
# ercot_common.py is at the cluster root (/work/users/z/y/zylia/) — no copy needed.
python ercot_wpp_archive.py --auto --from 2021-01-01 --to 2023-11-30
