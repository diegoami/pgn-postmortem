"""The command line end to end, as a user runs it: `read` a fixture
collection into a directory, then `analyze` that directory, each as a
separate process."""

import os
import subprocess
import sys
from pathlib import Path

import chess.pgn
import pytest

from pgn_postmortem.analysis import default_engine_path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "collection"


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "pgn_postmortem", *args], cwd=cwd, env=env, capture_output=True, text=True, timeout=300
    )


@pytest.mark.skipif(not Path(default_engine_path()).exists(), reason="needs stockfish")
def test_read_then_analyze_a_fixture_collection(tmp_path):
    player = ["--player", "Ada Example", "--alias", "adaex", "--alias", "Example, Ada"]

    read = run_cli("read", f"{FIXTURES}/**/*.pgn", *player, "--out", "games", cwd=tmp_path)
    assert read.returncode == 0, read.stderr
    assert "Read 5 game(s) from 2 file(s): 1 not the player's, 1 duplicate(s)" in read.stdout
    games = sorted((tmp_path / "games").glob("*.pgn"))
    assert len(games) == 3
    assert not any("[%eval" in path.read_text(encoding="utf-8") for path in games)

    analyze = run_cli("analyze", "games", "--out", "analyzed", "--depth", "8", "--workers", "2", cwd=tmp_path)
    assert analyze.returncode == 0, analyze.stderr
    assert "Analyzed 3 game(s) into analyzed; 0 already there." in analyze.stdout
    analyzed = sorted((tmp_path / "analyzed").glob("*.pgn"))
    assert [path.name for path in analyzed] == [path.name for path in games]
    for path in analyzed:
        with path.open(encoding="utf-8") as fh:
            game = chess.pgn.read_game(fh)
        assert all(node.eval() is not None or node.board().is_checkmate() for node in game.mainline()), path.name

    again = run_cli("analyze", "games", "--out", "analyzed", "--depth", "8", cwd=tmp_path)
    assert again.returncode == 0, again.stderr
    assert "Analyzed 0 game(s) into analyzed; 3 already there." in again.stdout


def test_a_missing_input_fails_with_a_message(tmp_path):
    result = run_cli("read", "no-such-dir", cwd=tmp_path)
    assert result.returncode == 1
    assert "error: no such file or directory: no-such-dir" in result.stderr
