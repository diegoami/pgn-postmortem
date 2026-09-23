"""Opening-theory lookup, used to find where a game left known book lines.

Backed by the lichess-org/chess-openings dataset (data/openings/*.tsv):
plain-text TSV files of eco, name, pgn (the exact move sequence for each
named line), downloaded from
https://github.com/lichess-org/chess-openings (CC0 public domain).

A game position counts as "in book" if the exact move sequence played so
far is a prefix of at least one row's move sequence - not just an exact
match of a named row, since most positions along a known line don't have
their own dedicated name.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OPENINGS_DIR = REPO_ROOT / "data" / "openings"

_MOVE_NUMBER_RE = re.compile(r"^\d+\.+$")


def _tokenize(pgn: str) -> tuple[str, ...]:
    return tuple(tok for tok in pgn.split() if not _MOVE_NUMBER_RE.match(tok))


class OpeningBook:
    def __init__(self, prefixes: set[tuple[str, ...]], named: dict[tuple[str, ...], tuple[str, str]]):
        self._prefixes = prefixes
        self._named = named

    def find_deviation(self, moves_san: list[str]) -> dict:
        """Given the SAN moves actually played (in order), return how far
        the game matches known theory.

        Returns a dict with:
          in_book_plies   - how many leading moves matched a known line (0 if none)
          opening         - (eco, name) of the deepest named entry within
                             those plies, or None if none matched at all
          left_book       - True if the game has moves beyond in_book_plies
        """
        in_book_plies = 0
        for k in range(len(moves_san), 0, -1):
            if tuple(moves_san[:k]) in self._prefixes:
                in_book_plies = k
                break

        opening = None
        for k in range(in_book_plies, 0, -1):
            key = tuple(moves_san[:k])
            if key in self._named:
                opening = self._named[key]
                break

        return {
            "in_book_plies": in_book_plies,
            "opening": opening,
            "left_book": in_book_plies < len(moves_san),
        }

    def continuations(self, prefix: list[str], limit: int = 3) -> list[tuple[str, str, tuple[str, ...]]]:
        """Return up to `limit` example named lines that extend `prefix`
        (a list/tuple of SAN moves), one per distinct immediate next move,
        preferring the shortest available example for each so the lines
        stay readable.

        Each result is (eco, name, remaining_moves) where remaining_moves
        are just the moves after `prefix`.
        """
        prefix = tuple(prefix)
        plen = len(prefix)
        best_by_next_move: dict[str, tuple[str, str, tuple[str, ...]]] = {}
        for moves, (eco, name) in self._named.items():
            if len(moves) <= plen or moves[:plen] != prefix:
                continue
            next_move = moves[plen]
            candidate = (eco, name, moves[plen:])
            existing = best_by_next_move.get(next_move)
            if existing is None or len(moves) < len(existing[2]) + plen:
                best_by_next_move[next_move] = candidate
        examples = sorted(best_by_next_move.values(), key=lambda c: (len(c[2]), c[2]))
        return examples[:limit]


def load_book(data_dir: Path = OPENINGS_DIR) -> OpeningBook:
    prefixes: set[tuple[str, ...]] = set()
    named: dict[tuple[str, ...], tuple[str, str]] = {}

    for tsv_path in sorted(data_dir.glob("*.tsv")):
        with tsv_path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                moves = _tokenize(row["pgn"])
                if not moves:
                    continue
                named[moves] = (row["eco"], row["name"])
                for i in range(1, len(moves) + 1):
                    prefixes.add(moves[:i])

    return OpeningBook(prefixes, named)
