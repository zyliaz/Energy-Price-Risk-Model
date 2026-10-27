#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=6:00:00
#SBATCH --mem=9000m
#SBATCH --chdir=/work/users/z/y/zylia/
set -euo pipefail
module purge
module add anaconda
export ERCOT_USERNAME=zyliduck4758@gmail.com
export ERCOT_PASSWORD=nMzjXcDL9YNut3s
export ERCOT_SUBSCRIPTION_KEY=785acf313e33461497f7ba49bfcf5a43
python -c "import pandas, requests, pyarrow" >/dev/null
# Full-range archive: 2021-01-01 -> 2026-09-24 (~51k docs, 69 months, batch_size=100).
# Replaces both the corrupt sep19 archive run and the live Dec-2023+ pull.
# Estimated runtime: ~1-1.5 h (local test: ~3 s per 24-doc download).
# Resumable: monthly parts go to OUT_DIR/outage_cap_archive_parts/; if the job dies,
# resubmit this same script and finished months are skipped.
# ercot_common.py must be at the chdir root.
python ercot_outage_cap_archive_full.py --from 2021-01-01 --to 2026-09-24
