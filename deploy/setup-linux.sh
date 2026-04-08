#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "[AnderBot] create venv"
"$PYTHON_BIN" -m venv .venv

source .venv/bin/activate

echo "[AnderBot] install package"
pip install --upgrade pip
pip install -e .

if [ ! -f .env ]; then
  cp .env.example .env
  echo "[AnderBot] created .env from .env.example"
fi

echo "[AnderBot] done"
echo "Run: source .venv/bin/activate && python -m anderbot.main run"
