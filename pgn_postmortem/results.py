"""The result of a game from its final position (ROADMAP.md, F-5, F-14, F-15).

**Optional.** Nothing here runs unless asked for: reading, analyzing without
``correct_results``, building a site and a manifest without ``correct_results``
never touch a result.

``decided_result`` is the one rule: the board decides first (checkmate gives
the mating side the win; stalemate and insufficient material a draw);
otherwise, for a game carrying the library's analysis, the ``[%eval]`` of its
final position gives a win to a side with at least ``presume_threshold`` (70
by default, 55 to 95) winning chances (``analysis.win_percent``, a forced
mate counts as 100) and a draw otherwise; otherwise there is no verdict. The
site uses it to show a result the source did not record (``site.shown_result``).

``correct_game``, ``correct_results`` and ``Collection.correct_results`` use it
to *write* the verdict into the ``Result`` header of a game the library
analyzed, also when the source recorded a result. A recorded decisive result
in a level position can be genuine (a time forfeit, a resignation, an
adjudication) and the library cannot know, so the correction is explicit,
reported game by game, keeps the source's value, and is **customizable**:

- the **policy** (``POLICIES``, ``target_result``) says which verdicts may
  overrule which recorded results: ``all`` (F-14, the default: the verdict
  whenever there is one), ``contradictions`` (a recorded win or loss reversed,
  or a recorded draw made decisive; never a decisive result made a draw because
  the position is level), ``unrecorded`` (only ``*`` or a missing result) and
  ``board`` (only what the board itself decides);
- the **threshold** (one value, 55 to 95);
- a **skip** rule: a callable ``skip(game) -> bool`` or, declaratively,
  ``NAME=REGEX`` header rules (``header_skip``), whose games are left exactly
  as they are and reported ``kept: skipped``.

``Result`` becomes the target the policy gives; ``OriginalResult`` is the
source's value, present exactly when it differs from ``Result``. Correcting
again changes nothing; if the target changes (another threshold or policy)
``OriginalResult`` still holds the source's value, never a corrected one, and
a target equal to the source's value restores it and removes
``OriginalResult``. ``game_id`` hashes the source's value
(``collection.source_result``), so a correction changes no ``PostmortemId``,
file name or match with the source. Only a game carrying the
``PostmortemAnalysis`` marker is touched. No engine runs: the final
``[%eval]`` is already in the file.

The full reference, with the policies table and worked examples, is in
``docs/result-correction.md``.
"""

from __future__ import annotations

import io
import os
import re
from collections.abc import Callable, Iterable
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


POLICIES = ("all", "contradictions", "unrecorded", "board")
DEFAULT_POLICY = "all"
RECORDED = ("1-0", "0-1", "1/2-1/2")  # the results a source can record; anything else counts as unrecorded
DECISIVE = ("1-0", "0-1")

Skip = Callable[[chess.pgn.Game], bool]


def check_policy(policy: str) -> str:
    """Return ``policy`` if it is one of ``POLICIES``, else raise ``ValueError``."""
    if policy not in POLICIES:
        raise ValueError(f"result policy must be one of {', '.join(POLICIES)}, not {policy!r}")
    return policy


def verdict(game: chess.pgn.Game, presume_threshold: float = PRESUME_THRESHOLD) -> tuple[str | None, bool]:
    """The final position's verdict on ``game`` and whether the **board**
    decided it: ``("0-1", True)`` for a checkmate by Black, ``("1-0", False)``
    for a win from the eval, ``(None, False)`` when there is none. The rule
    is ``decided_result``'s. ``game`` is not changed."""
    check_presume_threshold(presume_threshold)
    board = game.end().board()
    if board.is_checkmate():
        return ("0-1" if board.turn == chess.WHITE else "1-0"), True
    if board.is_stalemate() or board.is_insufficient_material():
        return "1/2-1/2", True
    white = final_white_chances(game)
    if white is None:
        return None, False
    if white >= presume_threshold:
        return "1-0", False
    if 100 - white >= presume_threshold:
        return "0-1", False
    return "1/2-1/2", False


def decided_result(game: chess.pgn.Game, presume_threshold: float = PRESUME_THRESHOLD) -> str | None:
    """The result the final position gives ``game``, in PGN notation (the
    rule is in the module docstring), or None when it gives none: no board
    result and no final eval. ``game`` is not changed."""
    return verdict(game, presume_threshold)[0]


def target_result(policy: str, original: str, decided: str | None, by_board: bool) -> str:
    """The result a game's header should hold under ``policy``.

    ``original`` is the source's result, ``decided`` the final position's
    verdict (None: none) and ``by_board`` whether the board decided it. The
    policies (the table is in ``docs/result-correction.md``):

    - ``all``: ``decided`` whenever there is one;
    - ``board``: ``decided`` only when the board decided it;
    - ``unrecorded``: ``decided`` only when ``original`` is not a recorded
      result (``*``, missing or other text);
    - ``contradictions``: ``decided`` only when ``original`` is recorded,
      ``decided`` is decisive and differs from it.

    Otherwise ``original``. Raises ``ValueError`` for an unknown policy."""
    check_policy(policy)
    if decided is None:
        return original
    if policy == "all":
        return decided
    if policy == "board":
        return decided if by_board else original
    if policy == "unrecorded":
        return original if original in RECORDED else decided
    return decided if (original in RECORDED and decided in DECISIVE and decided != original) else original


def header_skip(rules: Iterable[str]) -> Skip | None:
    """A ``skip`` callable from ``NAME=REGEX`` rules (None when there are
    none): a game is skipped when any rule's header ``NAME`` exists and the
    regular expression is found (``re.search``, case sensitive; ``(?i)`` for
    insensitive) in its value. Raises ``ValueError`` before anything is read
    for a rule without ``=``, with an empty name or with an invalid regular
    expression."""
    compiled = []
    for rule in rules:
        name, sep, pattern = str(rule).partition("=")
        if not sep or not name.strip():
            raise ValueError(f"a skip rule must be NAME=REGEX, not {rule!r}")
        try:
            compiled.append((name.strip(), re.compile(pattern)))
        except re.error as err:
            raise ValueError(f"invalid regular expression in skip rule {rule!r}: {err}") from err
    if not compiled:
        return None

    def skip(game: chess.pgn.Game) -> bool:
        return any(
            name in game.headers and regex.search(game.headers[name]) is not None for name, regex in compiled
        )

    return skip


KEPT_STATUSES = ("kept: agrees", "kept: policy", "kept: skipped", "kept: no verdict")


@dataclass(frozen=True)
class ResultChange:
    """One game's result changed. ``old`` and ``new`` are the ``Result``
    before and after; ``kind`` is ``corrected`` or ``restored`` (the target
    equals the source's value again, so ``OriginalResult`` was removed)."""

    path: str  # the file (or the game's file name for a collection)
    game_id: str
    white: str
    black: str
    old: str
    new: str
    kind: str

    def line(self) -> str:
        """``<file>: 0-1 -> 1-0 (White vs. Black, corrected)``."""
        return f"{self.path}: {self.old} -> {self.new} ({self.white} vs. {self.black}, {self.kind})"


@dataclass(frozen=True)
class GameDecision:
    """What was decided for one analyzed game and why. ``status`` is
    ``corrected`` or ``restored`` (``change`` is set), or one of
    ``KEPT_STATUSES``: ``kept: agrees`` (the result already is what the
    policy gives), ``kept: policy`` (the policy does not let the final
    position's verdict overrule it), ``kept: skipped`` (the skip rule), or
    ``kept: no verdict`` (the final position gives none). ``result`` is the
    ``Result`` after, ``verdict`` the final position's (None: none)."""

    path: str
    game_id: str
    white: str
    black: str
    status: str
    result: str
    verdict: str | None
    change: ResultChange | None = None

    def line(self) -> str:
        """The change's line, or ``<file>: kept: policy (1-0, the final
        position says 1/2-1/2)``."""
        if self.change:
            return self.change.line()
        if self.status == "kept: skipped":
            return f"{self.path}: {self.status} ({self.result})"
        said = f", the final position says {self.verdict}" if self.verdict else ""
        return f"{self.path}: {self.status} ({self.result}{said})"


@dataclass
class CorrectionReport:
    """What a correction did. ``changes`` are the games whose result
    changed; ``decisions`` has every analyzed game, with its reason.
    ``unchanged`` counts ``kept: agrees``, ``no_verdict`` ``kept: no verdict``,
    ``kept_policy`` ``kept: policy`` and ``excluded`` ``kept: skipped``;
    ``skipped`` counts files or games that are not analyzed, hold several
    games or do not parse. ``policy`` and ``threshold`` are those used."""

    changes: list[ResultChange] = field(default_factory=list)
    unchanged: int = 0
    no_verdict: int = 0
    skipped: int = 0
    warnings: list[str] = field(default_factory=list)
    dry_run: bool = False
    policy: str = DEFAULT_POLICY
    threshold: float = PRESUME_THRESHOLD
    kept_policy: int = 0
    excluded: int = 0
    decisions: list[GameDecision] = field(default_factory=list)

    def header(self) -> str:
        """``Policy: all, threshold 70.``"""
        return f"Policy: {self.policy}, threshold {self.threshold:g}."

    def summary(self) -> str:
        """``Changed N game(s); ...`` (``Would change`` for a dry run); the
        kept-by-policy and excluded counts only when not zero."""
        verb = "Would change" if self.dry_run else "Changed"
        extra = ""
        if self.kept_policy:
            extra += f", {self.kept_policy} kept by the policy"
        if self.excluded:
            extra += f", {self.excluded} excluded by the skip rule"
        return (
            f"{verb} {len(self.changes)} game(s); {self.unchanged} already agree, "
            f"{self.no_verdict} without a verdict from the final position{extra}, {self.skipped} skipped."
        )

    def explain(self) -> list[str]:
        """One line for every analyzed game that was kept, with its reason."""
        return [d.line() for d in self.decisions if d.change is None]


def decide_game(
    game: chess.pgn.Game,
    presume_threshold: float = PRESUME_THRESHOLD,
    path: str = "",
    *,
    policy: str = DEFAULT_POLICY,
    skip: Skip | None = None,
) -> GameDecision | None:
    """Correct ``game``'s ``Result`` in place under ``policy`` and return the
    decision, or None for a game without the analysis marker (never touched).

    ``skip(game)`` is called first, for an analyzed game, with the game as
    read (it must not change it); a true result leaves the game as it is.
    Then the verdict of the final position and the policy give the target
    (``target_result``), and the header is written as the module docstring
    says. Raises ``ValueError`` for an invalid threshold or policy."""
    check_presume_threshold(presume_threshold)
    check_policy(policy)
    if ANALYSIS_HEADER not in game.headers:
        return None
    current = game.headers.get("Result", NOT_RECORDED)
    ident = (path, game.headers.get(ID_HEADER, ""), game.headers.get("White", "?"), game.headers.get("Black", "?"))
    decided, by_board = verdict(game, presume_threshold)
    if skip is not None and skip(game):
        return GameDecision(*ident, "kept: skipped", current, decided)
    if decided is None:
        return GameDecision(*ident, "kept: no verdict", current, None)
    original = source_result(game)
    target = target_result(policy, original, decided, by_board)
    if target == current:
        return GameDecision(*ident, "kept: agrees" if target == decided else "kept: policy", current, decided)
    if target == original:
        game.headers["Result"] = original
        game.headers.pop(ORIGINAL_RESULT_HEADER, None)
        kind = "restored"
    else:
        game.headers["Result"] = target
        game.headers[ORIGINAL_RESULT_HEADER] = original
        kind = "corrected"
    change = ResultChange(*ident, current, target, kind)
    return GameDecision(*ident, kind, target, decided, change)


def correct_game(
    game: chess.pgn.Game,
    presume_threshold: float = PRESUME_THRESHOLD,
    path: str = "",
    *,
    policy: str = DEFAULT_POLICY,
    skip: Skip | None = None,
) -> ResultChange | None:
    """``decide_game``, returning only the change: None when nothing changed
    (not analyzed, skipped, no verdict, kept by the policy or already
    agreeing)."""
    decision = decide_game(game, presume_threshold, path, policy=policy, skip=skip)
    return decision.change if decision else None


def _tally(
    report: CorrectionReport, game: chess.pgn.Game, threshold: float, path: str, policy: str, skip: Skip | None
) -> ResultChange | None:
    decision = decide_game(game, threshold, path, policy=policy, skip=skip)
    report.decisions.append(decision)
    if decision.change:
        report.changes.append(decision.change)
    elif decision.status == "kept: no verdict":
        report.no_verdict += 1
    elif decision.status == "kept: skipped":
        report.excluded += 1
    elif decision.status == "kept: policy":
        report.kept_policy += 1
    else:
        report.unchanged += 1
    return decision.change


def correct_collection(
    games: Iterable[CollectedGame],
    presume_threshold: float | None = None,
    *,
    policy: str = DEFAULT_POLICY,
    skip: Skip | None = None,
) -> CorrectionReport:
    """``Collection.correct_results``: each analyzed game of ``games``, in memory."""
    threshold = PRESUME_THRESHOLD if presume_threshold is None else presume_threshold
    check_presume_threshold(threshold)
    check_policy(policy)
    report = CorrectionReport(policy=policy, threshold=threshold)
    for item in games:
        if ANALYSIS_HEADER not in item.game.headers:
            report.skipped += 1
            continue
        _tally(report, item.game, threshold, item.filename, policy, skip)
    return report


def correct_results(
    path: str | Path,
    *,
    presume_threshold: float = PRESUME_THRESHOLD,
    dry_run: bool = False,
    policy: str = DEFAULT_POLICY,
    skip: Skip | None = None,
) -> CorrectionReport:
    """Correct the result of every analyzed game in ``path`` (a PGN file, or a
    directory searched recursively for ``*.pgn``) under ``policy`` (one of
    ``POLICIES``; ``all`` by default), rewriting only the files that change,
    atomically, under the same names. No engine is used.

    ``presume_threshold`` is the winning chances in percent (55 to 95) that
    make a win. ``skip(game) -> bool`` is called for each analyzed game (see
    ``decide_game``); build one from header rules with ``header_skip``. With
    ``dry_run`` nothing is written; otherwise files are written only after
    every game has been decided, so an exception (a ``skip`` that raises)
    leaves every file unchanged. A file that is not analyzed, holds several
    games or does not parse is skipped, with a warning. Returns the
    ``CorrectionReport``. Raises ``FileNotFoundError`` for a missing ``path``
    and ``ValueError`` for an invalid threshold or policy, before anything is
    read or written."""
    check_presume_threshold(presume_threshold)
    check_policy(policy)
    root = Path(path).expanduser()
    if root.is_dir():
        files = sorted(p for p in root.rglob("*.pgn") if p.is_file())
    elif root.is_file():
        files = [root]
    else:
        raise FileNotFoundError(f"no such file or directory: {path}")

    report = CorrectionReport(dry_run=dry_run, policy=policy, threshold=presume_threshold)
    changed: list[tuple[Path, chess.pgn.Game]] = []
    for file in files:
        handle = io.StringIO(read_text(file))
        game = chess.pgn.read_game(handle)
        if game is None or game.errors or chess.pgn.read_game(handle) is not None:
            report.skipped += 1
            report.warnings.append(f"skipping {file}: not a single parseable game")
            continue
        if ANALYSIS_HEADER not in game.headers:
            report.skipped += 1
            report.warnings.append(f"skipping {file}: not analyzed")
            continue
        if _tally(report, game, presume_threshold, file.name, policy, skip):
            changed.append((file, game))
    # Every decision is made (and every ``skip`` called) before the first file is written, so a ``skip``
    # that raises leaves every file as it was.
    if not dry_run:
        for file, game in changed:
            partial = file.with_name(file.name + ".partial")
            partial.write_text(format_game(game), encoding="utf-8")
            os.replace(partial, file)
    return report
