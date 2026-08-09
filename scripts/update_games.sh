#!/usr/bin/env bash
# One-line entry point for the common case: new PGNs were dropped into
# daily_games/, now analyze whatever's new and republish docs/.
#
# Equivalent to running these two separately (see their --help for flags
# like --force or --depth that this wrapper doesn't expose):
#   .venv/bin/python scripts/analyze_games.py
#   .venv/bin/python scripts/publish_games.py --source analyzed_games
#
# Player/data-dir come from .env (see .env.example) - configure that once,
# no flags needed here.
set -euo pipefail
cd "$(dirname "$0")/.."

.venv/bin/python scripts/analyze_games.py
.venv/bin/python scripts/publish_games.py --source analyzed_games
