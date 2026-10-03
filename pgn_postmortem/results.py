"""The result of a game from its final position (ROADMAP.md, F-5 and F-14).

``decided_result`` is the one rule: the board decides first (checkmate gives
the mating side the win; stalemate and insufficient material a draw);
otherwise, for a game carrying the library's analysis, the ``[%eval]`` of its
final position gives a win to a side with at least ``presume_threshold`` (70
by default, 55 to 95) winning chances (``analysis.win_percent``, a forced
mate counts as 100) and a draw otherwise; otherwise there is no verdict. The
site uses it to show a result the source did not record (``site.shown_result``).

``correct_game``, ``correct_results`` and ``Collection.correct_results`` use it
to *write* the verdict into the ``Result`` header of a game the library
analyzed, also when the source recorded a result: a recorded decisive result
in a level position can be genuine (a time forfeit, a resignation, an
adjudication) and the library cannot know, so the correction is always
explicit, reported, and keeps the source's value:

- ``Result`` becomes the verdict; ``OriginalResult`` is the source's value,
  present exactly when it differs from ``Result``. Correcting again changes
  nothing; if the verdict changes (another threshold) ``OriginalResult``
  still holds the source's value, never a corrected one, and a verdict equal
  to the source's value restores it and removes ``OriginalResult``.
- ``game_id`` hashes the source's value (``collection.source_result``), so a
  correction changes no ``PostmortemId``, file name or match with the source.
- Only a game carrying the ``PostmortemAnalysis`` marker is touched. No engine
  runs: the final ``[%eval]`` is already in the file.
"""

from __future__ import annotations

import io
import os
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import chess
import chess.engine
import chess.pgn

from pgn_postmortem.analysis import win_percent
from pgn_postmortem.collection import (
    ANALYSIS_HEADER,
    ID_HEADER,
    ORIGINAL_RESULT_HEADER,
    CollectedGame,
    format_game,
    read_text,
    source_result,
)

NOT_RECORDED = "*"  # the PGN result of a game in progress or with an unknown result
PRESUME_THRESHOLD = 70.0  # the winning chances (%) that make a result a win (owner, 2026-09-24)
PRESUME_THRESHOLD_RANGE = (55.0, 95.0)


def check_presume_threshold(threshold: float) -> None:
    """Raise ``ValueError`` unless ``threshold`` is from 55 to 95."""
    low, high = PRESUME_THRESHOLD_RANGE
    if not low <= threshold <= high:  # also rejects NaN
        raise ValueError(
            f"presume_threshold must be from {low:g} to {high:g} (a side's winning chances in percent), "
            f"not {threshold!r}"
        )


def final_white_chances(game: chess.pgn.Game) -> float | None:
    """White's winning chances (0-100) in the final position of an analyzed
    game, from the ``[%eval]`` of its last move (a forced mate counts as 100
    for the side with the mate), or None: not analyzed, or no eval there."""
    if ANALYSIS_HEADER not in game.headers:
        return None
    score = game.end().eval()
    if score is None:
        return None
    white = score.white()
    if white.is_mate():
        return 100.0 if white > chess.engine.Cp(0) else 0.0
    return win_percent(white.score())


def decided_result(game: chess.pgn.Game, presume_threshold: float = PRESUME_THRESHOLD) -> str | None:
    """The result the final position gives ``game``, in PGN notation (the
    rule is in the module docstring), or None when it gives none: no board
    result and no final eval. ``game`` is not changed."""
    check_presume_threshold(presume_threshold)
    board = game.end().board()
    if board.is_checkmate():
        return "0-1" if board.turn == chess.WHITE else "1-0"
    if board.is_stalemate() or board.is_insufficient_material():
        return "1/2-1/2"
    white = final_white_chances(game)
    if white is None:
        return None
    if white >= presume_threshold:
        return "1-0"
    if 100 - white >= presume_threshold:
        return "0-1"
    return "1/2-1/2"


@dataclass(frozen=True)
class ResultChange:
    """One game's result changed. ``old`` and ``new`` are the ``Result``
    before and after; ``kind`` is ``corrected`` or ``restored`` (the verdict
    equals the source's value again, so ``OriginalResult`` was removed)."""

    path: str  # the file (or the game's file name for a collection)
    game_id: str
    white: str
    black: str
    old: str
    new: str
    kind: str

    def line(self) -> str:
        return f"{self.path}: {self.old} -> {self.new} ({self.white} vs. {self.black}, {self.kind})"


@dataclass
class CorrectionReport:
    changes: list[ResultChange] = field(default_factory=list)
    unchanged: int = 0  # analyzed games whose result already agrees
    no_verdict: int = 0  # analyzed games the final position gives no result for
    skipped: int = 0  # files or games that are not analyzed, have several games or do not parse
    warnings: list[str] = field(default_factory=list)
    dry_run: bool = False

    def summary(self) -> str:
        verb = "Would change" if self.dry_run else "Changed"
        return (
            f"{verb} {len(self.changes)} game(s); {self.unchanged} already agree, "
            f"{self.no_verdict} without a verdict from the final position, {self.skipped} skipped."
        )


def correct_game(
    game: chess.pgn.Game, presume_threshold: float = PRESUME_THRESHOLD, path: str = ""
) -> ResultChange | None:
    """Correct ``game``'s ``Result`` in place (the rule is in the module
    docstring) and return what changed, or None: not analyzed, no verdict, or
    already agreeing."""
    check_presume_threshold(presume_threshold)
    if ANALYSIS_HEADER not in game.headers:
        return None
    verdict = decided_result(game, presume_threshold)
    current = game.headers.get("Result", NOT_RECORDED)
    if verdict is None or verdict == current:
        return None
    original = source_result(game)
    if verdict == original:
        game.headers["Result"] = original
        game.headers.pop(ORIGINAL_RESULT_HEADER, None)
        kind = "restored"
    else:
        game.headers["Result"] = verdict
        game.headers[ORIGINAL_RESULT_HEADER] = original
        kind = "corrected"
    return ResultChange(
        path,
        game.headers.get(ID_HEADER, ""),
        game.headers.get("White", "?"),
        game.headers.get("Black", "?"),
        current,
        verdict,
        kind,
    )


def _tally(report: CorrectionReport, game: chess.pgn.Game, threshold: float, path: str) -> ResultChange | None:
    change = correct_game(game, threshold, path)
    if change:
        report.changes.append(change)
    elif decided_result(game, threshold) is None:
        report.no_verdict += 1
    else:
        report.unchanged += 1
    return change


def correct_collection(games: Iterable[CollectedGame], presume_threshold: float | None = None) -> CorrectionReport:
    """``Collection.correct_results``: each analyzed game of ``games``, in memory."""
    threshold = PRESUME_THRESHOLD if presume_threshold is None else presume_threshold
    check_presume_threshold(threshold)
    report = CorrectionReport()
    for item in games:
        if ANALYSIS_HEADER not in item.game.headers:
            report.skipped += 1
            continue
        _tally(report, item.game, threshold, item.filename)
    return report


def correct_results(
    path: str | Path, *, presume_threshold: float = PRESUME_THRESHOLD, dry_run: bool = False
) -> CorrectionReport:
    """Correct the result of every analyzed game in ``path`` (a PGN file, or a
    directory searched recursively for ``*.pgn``), rewriting only the files
    that change, atomically, under the same names. No engine is used. With
    ``dry_run`` nothing is written. A file that is not analyzed, holds several
    games or does not parse is skipped, with a warning. Raises
    ``FileNotFoundError`` for a missing ``path`` and ``ValueError`` for a
    threshold outside 55 to 95, before anything is read or written."""
    check_presume_threshold(presume_threshold)
    root = Path(path).expanduser()
    if root.is_dir():
        files = sorted(p for p in root.rglob("*.pgn") if p.is_file())
    elif root.is_file():
        files = [root]
    else:
        raise FileNotFoundError(f"no such file or directory: {path}")

    report = CorrectionReport(dry_run=dry_run)
    for file in files:
        handle = io.StringIO(read_text(file))
        game = chess.pgn.read_game(handle)
        if game is None or game.errors or chess.pgn.read_game(handle) is not None:
            report.skipped += 1
            report.warnings.append(f"skipping {file}: not a single parseable game")
            continue
        if ANALYSIS_HEADER not in game.headers:
            report.skipped += 1
            continue
        if _tally(report, game, presume_threshold, file.name) and not dry_run:
            partial = file.with_name(file.name + ".partial")
            partial.write_text(format_game(game), encoding="utf-8")
            os.replace(partial, file)
    return report
