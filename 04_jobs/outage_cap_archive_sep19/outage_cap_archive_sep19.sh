#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=2:00:00
#SBATCH --mem=9000m
#SBATCH --chdir=/work/users/z/y/zylia/
set -euo pipefail
module purge
module add anaconda
# Copy credential exports from an existing job script (e.g. wpp_archive_apr21.sh)
export ERCOT_USERNAME=zyliduck4758@gmail.com
export ERCOT_PASSWORD=nMzjXcDL9YNut3s
export ERCOT_SUBSCRIPTION_KEY=785acf313e33461497f7ba49bfcf5a43
python -c "import pandas, requests, pyarrow" >/dev/null
# Archive backfill: 2021-01-01 → 2023-12-09 (~25,746 docs, batch_size=100)
# Stores ALL postings (no dedup). Two CSV formats: 2021 (system-wide) and 2022+ (per-zone).
# Estimated runtime: ~43 min.
# ercot_common.py must be at the chdir root.
python ercot_outage_cap_archive.py --auto --from 2021-01-01 --to 2023-12-09
