#!/usr/bin/env python3
"""Independently re-analyze a folder of PGN games with a local Stockfish
engine, regardless of where they came from or who played them.

Some PGN sources attach their own move-quality review, but it can be
inconsistent - e.g. chess.com's exports were found to attach side variations
to whichever move it felt like ($9 "Miss" instead of the move actually being
mistaken, punishment lines instead of alternatives, etc.), not reliable
enough to build blunder detection on. This script ignores any of that: it
takes the mainline moves only (the source's own variations and NAGs
stripped), runs Stockfish on every resulting position itself, and writes a
clean, consistently-annotated copy to analyzed_games/<id>.pgn:

  - every move gets an eval comment in pawns, from White's POV, e.g. {+0.23}
  - a move gets our own NAG ($2 Mistake / $4 Blunder / $6 Inaccuracy) when
    the centipawn loss for the side that played it crosses a threshold
  - when a move is flagged and Stockfish's own top choice at that point
    differed from what was played, that top choice's full line is attached
    as a sibling variation off the position *before* the move (same shape
    publish_games.py reads for "Better was: ...")
  - a flagged move also gets Stockfish's best continuation from the
    position that actually resulted, attached as a second sibling off the
    move's own node (what publish_games.py reads for "Best continuation:
    ..." - how the blunder should have been punished, in case the real
    opponent didn't find it)
  - the last move of each of those two attached lines gets a standard PGN
    position-evaluation NAG ($10/$14/$15/$16/$17/$18/$19, i.e. =, +=, =+,
    ±, ∓, +-, -+), read by publish_games.py to print the usual annotation
    symbol after the line

Reads <data-dir>/daily_games/*.pgn and writes <data-dir>/analyzed_games/*.pgn.
Each daily_games/<id>.pgn must hold exactly one game - see read_single_game()
in pgn_io.py for why. <data-dir> can be this same repo, or a separate
repo/directory holding just the games/analysis/docs, kept apart from these
scripts. Resolved as: --data-dir, else CHESS_DATA_DIR (from .env or the real
environment), else this repo's own checkout directory. See .env.example.

Usage:
    .venv/bin/python scripts/analyze_games.py [--time 0.3] [--depth 18]
    .venv/bin/python scripts/analyze_games.py --data-dir /path/to/games
    .venv/bin/python scripts/analyze_games.py   # reads CHESS_DATA_DIR from .env
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

import chess
import chess.engine
import chess.pgn

from pgn_io import load_dotenv, read_single_game

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = REPO_ROOT

ENGINE_PATH = shutil.which("stockfish") or "/usr/games/stockfish"

# Centipawn-loss thresholds for the side that played the move, roughly
# mirroring chess.com's own move-quality categories.
BLUNDER_CP = 300
MISTAKE_CP = 100
INACCURACY_CP = 50
MATE_SCORE = 100000


def sort_key(path: Path):
    stem = path.stem
    return (0, int(stem)) if stem.isdigit() else (1, stem)


def eval_white_cp(score: chess.engine.PovScore) -> int:
    return score.white().score(mate_score=MATE_SCORE)


def format_eval(cp_white: int) -> str:
    pawns = cp_white / 100
    return f"{'+' if pawns >= 0 else ''}{pawns:.2f}"


def classify(loss_cp: int) -> int | None:
    if loss_cp >= BLUNDER_CP:
        return chess.pgn.NAG_BLUNDER
    if loss_cp >= MISTAKE_CP:
        return chess.pgn.NAG_MISTAKE
    if loss_cp >= INACCURACY_CP:
        return chess.pgn.NAG_DUBIOUS_MOVE
    return None


# Standard PGN position-evaluation NAGs (always from White's POV, regardless
# of whose blunder is being described).
def classify_position(eval_cp_white: int) -> int:
    pawns = eval_cp_white / 100
    if pawns <= -3.0:
        return 19  # -+
    if pawns <= -1.0:
        return 17  # (black moderate advantage)
    if pawns <= -0.4:
        return 15  # =+
    if pawns < 0.4:
        return 10  # =
    if pawns < 1.0:
        return 14  # +=
    if pawns < 3.0:
        return 16  # (white moderate advantage)
    return 18  # +-


def attach_line(
    parent_node: chess.pgn.GameNode, parent_board: chess.Board, pv: list[chess.Move], pv_plies: int, final_eval_cp: int
) -> None:
    """Add pv (capped at pv_plies) as a new sibling variation chain off
    parent_node, tagging its last move with a position-evaluation NAG for
    final_eval_cp. Caller must ensure parent_node's real mainline child (if
    any) already exists - adding a variation to a node with no children yet
    would wrongly make it the mainline."""
    var_board = parent_board.copy()
    var_node = parent_node
    for move in pv[:pv_plies]:
        if move not in var_board.legal_moves:
            break
        var_node = var_node.add_variation(move)
        var_board.push(move)
    if var_node is not parent_node:
        var_node.nags.add(classify_position(final_eval_cp))


def analyze_game(
    engine: chess.engine.SimpleEngine, limit: chess.engine.Limit, source_game: chess.pgn.Game, pv_plies: int
) -> chess.pgn.Game:
    moves = list(source_game.mainline_moves())

    out_game = chess.pgn.Game()
    out_game.headers = source_game.headers.copy()
    out_game.headers.pop("CurrentPosition", None)

    board = out_game.board()
    node = out_game

    info = engine.analyse(board, limit)
    eval_cp = eval_white_cp(info["score"])
    pv = info.get("pv") or []

    # A flagged move's "punishment" line (Stockfish's best continuation from
    # the position that actually resulted) can only be attached to that
    # move's own node once *that* node's real mainline child (the actual
    # next move played) exists - otherwise it would wrongly become the
    # mainline itself. So it's queued here and attached one iteration later.
    pending_punishment: tuple[chess.pgn.GameNode, chess.Board, list[chess.Move], int] | None = None

    for move in moves:
        mover = board.turn
        eval_before = eval_cp
        pv_before = pv

        node = node.add_variation(move)

        if pending_punishment is not None:
            punish_node, punish_board, punish_pv, punish_eval = pending_punishment
            attach_line(punish_node, punish_board, punish_pv, pv_plies, punish_eval)
            pending_punishment = None

        board.push(move)

        info = engine.analyse(board, limit)
        eval_cp = eval_white_cp(info["score"])
        pv = info.get("pv") or []

        node.comment = format_eval(eval_cp)

        loss = (eval_before - eval_cp) if mover == chess.WHITE else (eval_cp - eval_before)
        nag = classify(max(loss, 0))
        if nag is not None:
            node.nags.add(nag)
            if pv_before and pv_before[0] != move:
                attach_line(node.parent, node.parent.board(), pv_before, pv_plies, eval_before)
            if pv:
                pending_punishment = (node, board.copy(), pv, eval_cp)

    return out_game


def main() -> None:
    load_dotenv(REPO_ROOT / ".env")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--time", type=float, default=0.3, help="seconds of search per position (default 0.3)")
    parser.add_argument("--depth", type=int, default=None, help="fixed search depth instead of a time limit")
    parser.add_argument(
        "--pv-length", type=int, default=8, help="max half-moves of the refutation line to attach (default 8)"
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help=f"directory holding daily_games/ and analyzed_games/ - your own repo, or a "
        f"separate data repo (default: CHESS_DATA_DIR from .env or the real environment, "
        f"else this repo's own checkout, currently {DEFAULT_DATA_DIR})",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir or os.environ.get("CHESS_DATA_DIR") or DEFAULT_DATA_DIR).resolve()
    if not data_dir.is_dir():
        print(
            f"error: data dir not found: {data_dir}\nPass --data-dir, or set CHESS_DATA_DIR in .env.",
            file=sys.stderr,
        )
        sys.exit(1)
    games_src_dir = data_dir / "daily_games"
    games_out_dir = data_dir / "analyzed_games"

    limit = chess.engine.Limit(depth=args.depth) if args.depth else chess.engine.Limit(time=args.time)

    pgn_paths = sorted(games_src_dir.glob("*.pgn"), key=sort_key)
    if not pgn_paths:
        print(f"No PGN files found in {games_src_dir}", file=sys.stderr)
        sys.exit(1)

    games_out_dir.mkdir(exist_ok=True)

    with chess.engine.SimpleEngine.popen_uci(ENGINE_PATH) as engine:
        for pgn_path in pgn_paths:
            source_game = read_single_game(pgn_path)
            if source_game is None:
                continue
            print(f"Analyzing {pgn_path.name}...")
            out_game = analyze_game(engine, limit, source_game, args.pv_length)
            out_path = games_out_dir / pgn_path.name
            out_path.write_text(str(out_game) + "\n", encoding="utf-8")
            print(f"  -> {out_path}")


if __name__ == "__main__":
    main()
