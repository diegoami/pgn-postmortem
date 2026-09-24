"""The Stockfish step: analyze every game of a collection and write it, with
standard ``[%eval]`` comments, to an output directory.

For every move of a game (the mainline only; the collection has already
stripped whatever the source attached):

- the move gets the position's evaluation after it as a standard
  ``[%eval ...]`` comment, from White's point of view: ``[%eval 0.23]`` in
  pawns, or ``[%eval #3]`` / ``[%eval #-2]`` for a forced mate. A move that
  gives checkmate gets none, as in lichess's exports: there is nothing left
  to evaluate.
- a move is flagged with a NAG ($6 inaccuracy, $2 mistake, $4 blunder) by the
  *win percentage* its side lost, not by raw centipawns (CLAUDE.md, *decided*):
  a centipawn eval becomes a 0-100 win chance through lichess's logistic fit
  (https://lichess.org/page/accuracy), and the thresholds default to lichess's
  own 10/20/30 points.
- a flagged move gets two engine lines as variations: Stockfish's preferred
  move from the position before it, when that differs from the move played
  ("better was"), and Stockfish's best continuation from the position after it
  ("how to punish it"). Each line's last move carries a position NAG ($10 to
  $19: =, +=, =+, and so on).

The step is incremental: a game already analyzed into the output directory
is not analyzed again. "Analyzed" means a file there carries the game's
``PostmortemId`` and the ``PostmortemAnalysis`` header, which only this step
writes (the engine and the search limit, e.g. ``Stockfish 16, depth 18``).
The file name alone is not enough: ``Collection.write`` uses the same
``<date>-<id>.pgn`` names for games it has only stripped, so reading into a
directory and then analyzing in place analyzes every game. It runs one
single-threaded Stockfish process per worker, and each game starts with a
fresh engine state (``ucinewgame``), so a game's output does not depend on
which worker analyzed it or on what that worker analyzed before.
"""

from __future__ import annotations

import math
import os
import queue
import shutil
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

import chess
import chess.engine
import chess.pgn

from pgn_postmortem.collection import ANALYSIS_HEADER, CollectedGame, analyzed_id, format_game

FALLBACK_ENGINE_PATH = "/usr/games/stockfish"  # where Debian and Ubuntu install it, off the default PATH

MATE_SCORE = 100000
WIN_PCT_LOGISTIC_SCALE = 0.00368208
DEFAULT_TIME = 0.3
DEFAULT_PV_PLIES = 8


class Thresholds(NamedTuple):
    """Win-percentage points a move must lose to be flagged."""

    inaccuracy: float = 10.0
    mistake: float = 20.0
    blunder: float = 30.0


LICHESS_THRESHOLDS = Thresholds()


class EngineFailure(RuntimeError):
    """The engine could not be started, or failed while analyzing a game.
    The run stops at the first failure; the games already written stay, and
    a rerun picks up the rest."""


ENGINE_ERRORS = (chess.engine.EngineError, chess.engine.EngineTerminatedError)


@dataclass
class AnalysisReport:
    analyzed: int = 0
    skipped: int = 0
    written: list[Path] = field(default_factory=list)


def default_engine_path() -> str:
    return shutil.which("stockfish") or FALLBACK_ENGINE_PATH


def win_percent(cp_white: int) -> float:
    """White's winning chances (0-100) for a White-POV centipawn eval."""
    return 50 + 50 * (2 / (1 + math.exp(-WIN_PCT_LOGISTIC_SCALE * cp_white)) - 1)


def classify(loss_pct: float, thresholds: Thresholds) -> int | None:
    if loss_pct >= thresholds.blunder:
        return chess.pgn.NAG_BLUNDER
    if loss_pct >= thresholds.mistake:
        return chess.pgn.NAG_MISTAKE
    if loss_pct >= thresholds.inaccuracy:
        return chess.pgn.NAG_DUBIOUS_MOVE
    return None


def classify_position(cp_white: int) -> int:
    """The standard position-evaluation NAG for a White-POV eval."""
    pawns = cp_white / 100
    if pawns <= -3.0:
        return 19  # -+
    if pawns <= -1.0:
        return 17  # -/+
    if pawns <= -0.4:
        return 15  # =+
    if pawns < 0.4:
        return 10  # =
    if pawns < 1.0:
        return 14  # +=
    if pawns < 3.0:
        return 16  # +/-
    return 18  # +-


def attach_line(
    parent: chess.pgn.GameNode, board: chess.Board, pv: list[chess.Move], pv_plies: int, final_cp_white: int
) -> None:
    """Add ``pv`` (at most ``pv_plies`` moves) as a variation off ``parent``,
    its last move tagged with a position NAG. ``parent``'s mainline child must
    already exist, or the line would become the mainline."""
    board = board.copy()
    node = parent
    for move in pv[:pv_plies]:
        if move not in board.legal_moves:
            break
        node = node.add_variation(move)
        board.push(move)
    if node is not parent:
        node.nags.add(classify_position(final_cp_white))


def analyze_game(
    engine: chess.engine.SimpleEngine,
    limit: chess.engine.Limit,
    source: chess.pgn.Game,
    engine_game: object,
    pv_plies: int = DEFAULT_PV_PLIES,
    thresholds: Thresholds = LICHESS_THRESHOLDS,
) -> chess.pgn.Game:
    """The analyzed copy of ``source`` (its headers, its mainline, our
    comments, NAGs and lines, and the ``PostmortemAnalysis`` marker).
    ``engine_game`` identifies the game to the engine: a new value makes
    python-chess send ``ucinewgame`` first."""
    out = chess.pgn.Game()
    out.headers = source.headers.copy()
    out.headers[ANALYSIS_HEADER] = describe_analysis(engine, limit)
    board = out.board()
    node: chess.pgn.GameNode = out

    def search(position: chess.Board) -> tuple[chess.engine.PovScore, list[chess.Move]]:
        info = engine.analyse(position, limit, game=engine_game)
        return info["score"], info.get("pv") or []

    score, pv = search(board)
    # A flagged move's punishment line hangs off that move's own node, which
    # must first get its mainline child (the next move played), so it is
    # attached one move later.
    pending: tuple[chess.pgn.GameNode, chess.Board, list[chess.Move], int] | None = None

    for move in source.mainline_moves():
        mover = board.turn
        cp_before = score.white().score(mate_score=MATE_SCORE)
        pv_before = pv

        node = node.add_variation(move)
        if pending is not None:
            attach_line(*pending[:3], pv_plies, pending[3])
            pending = None
        board.push(move)

        score, pv = search(board)
        cp_after = score.white().score(mate_score=MATE_SCORE)
        node.set_eval(score)

        loss = win_percent(cp_before) - win_percent(cp_after)
        if mover == chess.BLACK:
            loss = -loss
        nag = classify(max(loss, 0.0), thresholds)
        if nag is not None:
            node.nags.add(nag)
            if pv_before and pv_before[0] != move:
                attach_line(node.parent, node.parent.board(), pv_before, pv_plies, cp_before)
            if pv:
                pending = (node, board.copy(), pv, cp_after)

    # A pending line left after the last move is dropped: with no next move,
    # it would become the game's mainline.
    return out


def describe_analysis(engine: chess.engine.SimpleEngine, limit: chess.engine.Limit) -> str:
    budget = f"depth {limit.depth}" if limit.depth else f"{limit.time:g}s per position"
    return f"{engine.id.get('name', 'UCI engine')}, {budget}"


def analyzed_ids(out_dir: Path) -> set[str]:
    """The ids of the games already analyzed into ``out_dir``: the
    ``PostmortemId`` of each file there whose first game carries the
    ``PostmortemAnalysis`` marker. A file without it (a game that was only
    stripped, or anything else) does not count."""
    return {gid for path in out_dir.glob("*.pgn") if (gid := analyzed_id(path))}


def analyze_games(
    games: Iterable[CollectedGame],
    out_dir: str | Path,
    *,
    depth: int | None = None,
    time: float = DEFAULT_TIME,
    workers: int = 0,
    engine_path: str | None = None,
    pv_plies: int = DEFAULT_PV_PLIES,
    thresholds: Thresholds = LICHESS_THRESHOLDS,
    progress: Callable[[int, int, CollectedGame], None] | None = None,
) -> AnalysisReport:
    """Analyze every game not yet in ``out_dir`` into ``out_dir/<date>-<id>.pgn``.

    ``depth`` searches each position to a fixed depth (reproducible);
    otherwise each position gets ``time`` seconds. ``workers`` Stockfish
    processes run side by side (0: one per CPU). No engine is started when
    there is nothing to analyze. ``progress(done, total, game)`` is called
    after each game.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    done_ids = analyzed_ids(out_dir)
    games = list(games)
    todo = [g for g in games if g.id not in done_ids]
    report = AnalysisReport(skipped=len(games) - len(todo))
    if not todo:
        return report

    limit = chess.engine.Limit(depth=depth) if depth else chess.engine.Limit(time=time)
    workers = max(1, min(workers or os.cpu_count() or 1, len(todo)))
    engines: queue.Queue[chess.engine.SimpleEngine] = queue.Queue()

    def run(item: CollectedGame) -> Path:
        engine = engines.get()
        try:
            analyzed = analyze_game(engine, limit, item.game, item.id, pv_plies, thresholds)
        except ENGINE_ERRORS as err:
            raise EngineFailure(f"the engine failed on {item.origin}: {err}") from err
        finally:
            engines.put(engine)
        path = out_dir / item.filename
        partial = path.with_name(path.name + ".partial")
        partial.write_text(format_game(analyzed), encoding="utf-8")
        os.replace(partial, path)  # a run that is interrupted never leaves a half-written game behind
        return path

    engine_path = engine_path or default_engine_path()
    try:
        for _ in range(workers):
            try:
                engine = chess.engine.SimpleEngine.popen_uci(engine_path)
            except FileNotFoundError as err:
                raise EngineFailure(f"Stockfish not found at {engine_path} (install it, or pass its path)") from err
            except (OSError, *ENGINE_ERRORS) as err:
                raise EngineFailure(f"could not start the engine {engine_path}: {err}") from err
            engines.put(engine)
            # only the options this engine has: another UCI engine may lack Stockfish's
            engine.configure({k: v for k, v in {"Threads": 1, "Hash": 64}.items() if k in engine.options})
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(run, item): item for item in todo}
            try:
                for done, future in enumerate(as_completed(futures), start=1):
                    report.written.append(future.result())
                    report.analyzed += 1
                    if progress:
                        progress(done, len(todo), futures[future])
            except BaseException:
                # Fail fast: drop the queued games instead of trying each one first.
                pool.shutdown(wait=True, cancel_futures=True)
                raise
    finally:
        while not engines.empty():
            engine = engines.get()
            try:
                engine.quit()
            except ENGINE_ERRORS:
                pass  # it already died
    report.written.sort()
    return report
