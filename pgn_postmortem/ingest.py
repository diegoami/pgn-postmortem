"""Collect the player's games from every configured source into games/,
one normalized PGN per game.

Normalizing means: mainline moves only (every comment, variation and NAG
from the source is dropped - old engine annotations are replaced by our own
Stockfish pass), headers kept apart from stale analysis ones, plus two of our
own: PostmortemId and PostmortemSource.

Games are identified by their content rather than by where they came from,
so the same game found in two places (say, a chess.com game that is also in
an old PGN collection) is only kept once, and re-running ingest only adds
games it hasn't seen.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import chess
import chess.pgn

from pgn_postmortem.config import Config
from pgn_postmortem.sources import describe, iter_source

DROPPED_HEADERS = {"Annotator", "PlyCount", "CurrentPosition"}

# Below this many half-moves, the moves alone aren't distinctive enough to
# identify a game (the same short trap can be played in many games), so the
# date and players become part of the identity too.
SHORT_GAME_PLIES = 20


@dataclass
class IngestReport:
    read: int = 0
    not_player: int = 0
    empty: int = 0
    duplicates: int = 0
    new: int = 0
    per_source: dict[str, int] = field(default_factory=dict)


def game_id(game: chess.pgn.Game) -> str:
    moves = [move.uci() for move in game.mainline_moves()]
    headers = game.headers
    parts = [headers.get("FEN", ""), headers.get("Result", "*"), " ".join(moves)]
    if len(moves) < SHORT_GAME_PLIES:
        parts += [headers.get("Date", ""), headers.get("White", "").lower(), headers.get("Black", "").lower()]
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:10]


def file_stem(game: chess.pgn.Game, gid: str) -> str:
    """<date>-<id>, so a plain directory listing is chronological."""
    date = game.headers.get("Date", "")
    y, m, d = (date.split(".") + ["", "", ""])[:3]
    if not y.isdigit():
        return f"undated-{gid}"
    return f"{y}-{m if m.isdigit() else '00'}-{d if d.isdigit() else '00'}-{gid}"


def normalize(game: chess.pgn.Game, gid: str, source_label: str) -> chess.pgn.Game:
    out = chess.pgn.Game()
    for key, value in game.headers.items():
        if key not in DROPPED_HEADERS:
            out.headers[key] = value
    if "FEN" in game.headers:
        out.setup(chess.Board(game.headers["FEN"]))
    out.headers["PostmortemId"] = gid
    out.headers["PostmortemSource"] = source_label

    node = out
    for move in game.mainline_moves():
        node = node.add_variation(move)
    return out


def existing_ids(games_dir: Path) -> set[str]:
    return {path.stem.rsplit("-", 1)[-1] for path in games_dir.glob("*.pgn")}


def ingest(config: Config) -> IngestReport:
    config.games_dir.mkdir(parents=True, exist_ok=True)
    seen = existing_ids(config.games_dir)
    report = IngestReport()

    for source in config.sources:
        label = describe(source)
        print(f"Reading {label}...")
        added = 0
        for _origin, game in iter_source(source, config.cache_dir, config.workspace):
            report.read += 1
            if not (config.is_player(game.headers.get("White")) or config.is_player(game.headers.get("Black"))):
                report.not_player += 1
                continue
            if game.next() is None:
                report.empty += 1
                continue
            gid = game_id(game)
            if gid in seen:
                report.duplicates += 1
                continue
            seen.add(gid)
            out = normalize(game, gid, label)
            path = config.games_dir / f"{file_stem(game, gid)}.pgn"
            path.write_text(str(out) + "\n", encoding="utf-8")
            added += 1
        report.per_source[label] = added
        report.new += added
        print(f"  {added} new game(s)")

    return report
