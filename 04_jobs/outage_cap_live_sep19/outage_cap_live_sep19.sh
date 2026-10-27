#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=36:00:00
#SBATCH --partition=week
#SBATCH --mem=9000m
#SBATCH --chdir=/work/users/z/y/zylia/
set -euo pipefail
module purge
module add anaconda
export ERCOT_USERNAME=zyliduck4758@gmail.com
export ERCOT_PASSWORD=nMzjXcDL9YNut3s
export ERCOT_SUBSCRIPTION_KEY=785acf313e33461497f7ba49bfcf5a43
python -c "import pandas, requests, pyarrow" >/dev/null
# Attempt 2: resume from page 835 (att1 timed out at page 835 after 10 retries).
# Reads the partial parquet from att1, fetches remaining pages, writes one combined file.
# Actual pace ~21s/page → remaining ~3817 pages ≈ 22 hrs.
# Auto-discovers the att1 partial parquet via OUT_DIR glob.
python ercot_outage_cap_att2.py \
    --start-page 835 \
    --from 2023-12-10
