#!/bin/zsh
set -e
cd "$(dirname "$0")"

if [[ ! -x .venv/bin/uvicorn ]]; then
  echo "Setting up the Python environment..."
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

if [[ ! -f artifacts/model.joblib ]]; then
  echo "Training the kiln energy model..."
  .venv/bin/python -m kiln_energy.pipeline
fi

echo "Starting Kilnwise at http://127.0.0.1:8000"
(.venv/bin/python -c 'import time; time.sleep(1.5)' && open "http://127.0.0.1:8000") &
exec .venv/bin/uvicorn kiln_energy.api:app --host 127.0.0.1 --port 8000
