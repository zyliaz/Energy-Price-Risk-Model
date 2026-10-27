#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=3:00:00
#SBATCH --mem=9000m
#SBATCH --chdir=/work/users/z/y/zylia/
set -euo pipefail
module purge
module add anaconda
export ERCOT_USERNAME=zyliduck4758@gmail.com
export ERCOT_PASSWORD=nMzjXcDL9YNut3s
export ERCOT_SUBSCRIPTION_KEY=785acf313e33461497f7ba49bfcf5a43
python -c "import pandas, requests, pyarrow" >/dev/null
# Attempt 3: att2 crashed at page 4513/4661 with 400 Bad Request.
# 149 pages remain (~100 min at ~40s/page). Reuses att2.py which
# auto-discovers the att2 partial parquet via OUT_DIR glob.
python ercot_outage_cap_att2.py \
    --start-page 4513 \
    --from 2023-12-10
