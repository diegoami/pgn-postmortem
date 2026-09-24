import shutil
import subprocess
import sys
from pathlib import Path

import chess.pgn
import pytest

from pgn_postmortem.analysis import (
    DEFAULT_BLUNDER_PCT,
    DEFAULT_INACCURACY_PCT,
    DEFAULT_MISTAKE_PCT,
    ENGINE_PATH,
    Thresholds,
    classify,
    classify_position,
    format_eval,
    win_percent,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
LICHESS_THRESHOLDS = Thresholds(DEFAULT_INACCURACY_PCT, DEFAULT_MISTAKE_PCT, DEFAULT_BLUNDER_PCT)


def test_win_percent_is_even_at_zero_and_symmetric():
    assert win_percent(0) == pytest.approx(50)
    for cp in (35, 150, 400, 1200):
        assert win_percent(cp) + win_percent(-cp) == pytest.approx(100)
        assert win_percent(cp) > 50


def test_same_cp_swing_matters_less_in_decided_positions():
    near_equal = win_percent(0) - win_percent(-300)
    already_lost = win_percent(-900) - win_percent(-1200)
    assert near_equal > 20
    assert already_lost < 5


@pytest.mark.parametrize(
    ("loss_pct", "expected"),
    [
        (0, None),
        (9.9, None),
        (10, chess.pgn.NAG_DUBIOUS_MOVE),
        (20, chess.pgn.NAG_MISTAKE),
        (29.9, chess.pgn.NAG_MISTAKE),
        (30, chess.pgn.NAG_BLUNDER),
        (100, chess.pgn.NAG_BLUNDER),
    ],
)
def test_classify_uses_lichess_thresholds(loss_pct, expected):
    assert classify(loss_pct, LICHESS_THRESHOLDS) == expected


@pytest.mark.parametrize(
    ("cp", "nag"),
    [(-500, 19), (-150, 17), (-50, 15), (0, 10), (39, 10), (50, 14), (150, 16), (500, 18)],
)
def test_classify_position(cp, nag):
    assert classify_position(cp) == nag


def test_format_eval():
    assert format_eval(23) == "+0.23"
    assert format_eval(0) == "+0.00"
    assert format_eval(-150) == "-1.50"


@pytest.mark.skipif(shutil.which("stockfish") is None and not Path(ENGINE_PATH).exists(), reason="needs stockfish")
def test_analyze_flags_a_mate_in_one_blunder(tmp_path):
    (tmp_path / "daily_games").mkdir()
    # 3... Nf6?? walks into 4. Qxf7#
    (tmp_path / "daily_games" / "1.pgn").write_text(
        '[White "A"]\n[Black "B"]\n[Result "1-0"]\n\n1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0\n'
    )
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "analyze_games.py"), "--data-dir", str(tmp_path), "--depth", "10"],
        check=True,
        capture_output=True,
    )
    with (tmp_path / "analyzed_games" / "1.pgn").open() as fh:
        game = chess.pgn.read_game(fh)

    nodes = list(game.mainline())
    blunder = nodes[5]
    assert blunder.san() == "Nf6"
    assert chess.pgn.NAG_BLUNDER in blunder.nags
    # "Better was" hangs off the position before the blunder, "Best continuation" off the blunder itself
    assert len(blunder.parent.variations) == 2
    assert blunder.variations[1].san() == "Qxf7#"
    assert all(n.comment for n in nodes)
