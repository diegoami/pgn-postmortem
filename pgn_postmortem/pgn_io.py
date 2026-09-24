"""Small helpers shared by analyze_games.py and publish_games.py: loading
per-user config from a local .env file, and reading a PGN file that's
required to hold exactly one game.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import chess.pgn

_ENV_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def load_dotenv(path: Path) -> None:
    """Populate os.environ from a simple KEY=VALUE .env file (quotes
    around the value are stripped, '#' starts a comment line). Never
    overrides a variable already set in the real environment. Does
    nothing if the file doesn't exist - .env is optional, not required."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = _ENV_LINE_RE.match(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


def read_single_game(pgn_path: Path) -> chess.pgn.Game | None:
    """Read a PGN file that's expected to hold exactly one game.

    Every output path this project generates (docs/games/<id>.md,
    docs/games/<id>/blunder_*.svg, analyzed_games/<id>.pgn, ...) is derived
    from just the source filename - there's no second index for "which
    game within the file". python-chess's read_game() would otherwise
    silently read only the first game and drop the rest of a multi-game
    file with no warning at all, so this checks for and flags that case
    instead of losing games silently.

    Returns None (after printing a warning) if the file has no game, or
    more than one.
    """
    with pgn_path.open(encoding="utf-8") as fh:
        game = chess.pgn.read_game(fh)
        if game is None:
            print(f"warning: no game found in {pgn_path}, skipping", file=sys.stderr)
            return None
        extra = chess.pgn.read_game(fh)
        if extra is not None:
            print(
                f"warning: {pgn_path} contains more than one game - skipping it entirely. "
                "Each PGN file here must hold exactly one game; split multi-game files up.",
                file=sys.stderr,
            )
            return None
    return game
