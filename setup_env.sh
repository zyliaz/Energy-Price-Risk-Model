#!/usr/bin/env bash
# Bootstrap a portable Python virtual environment for this project.
# Works on any Linux/macOS server with Python 3.8+.
#
# Usage:
#   bash setup_env.sh
#   source .venv/bin/activate
#   cp .env.example .env   # then fill in ERCOT credentials
#   set -a && source .env && set +a
#   cd 02_scripts/1_scrapers && python ercot_load_by_fzn.py --trial-only

set -e
VENV_DIR=".venv"

echo "[setup] Creating virtual environment in ${VENV_DIR}/ ..."
python3 -m venv "${VENV_DIR}"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip --quiet
pip install -r requirements.txt

echo ""
echo "Environment ready. Next:"
echo "  source ${VENV_DIR}/bin/activate"
echo "  cp .env.example .env   # fill in credentials, then: set -a && source .env && set +a"
echo "  cd 02_scripts/1_scrapers && python ercot_load_by_fzn.py --trial-only"
