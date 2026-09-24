"""The library's Stockfish step (pgn_postmortem.analysis). Every test here
searches to a fixed depth, and is skipped when no Stockfish binary is found
(CI always installs one)."""

from pathlib import Path

import chess.pgn
import pytest

from pgn_postmortem import Collection, analyze_games
from pgn_postmortem.analysis import default_engine_path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "collection"
PLAYER = {"player": "Ada Example", "aliases": ["adaex", "Example, Ada"]}
DEPTH = 8

needs_stockfish = pytest.mark.skipif(not Path(default_engine_path()).exists(), reason="needs stockfish")


def read_pgn(path: Path) -> chess.pgn.Game:
    with path.open(encoding="utf-8") as fh:
        return chess.pgn.read_game(fh)


def contents(directory: Path) -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(directory.iterdir())}


@needs_stockfish
def test_a_forced_mate_is_flagged_with_eval_comments(tmp_path):
    # 3... Nf6?? walks into 4. Qxf7#
    collection = Collection.read(FIXTURES / "online" / "2020" / "games.pgn", player="AdaEx")
    scholars = [item for item in collection if item.game.headers["Black"] == "AdaEx"]
    report = analyze_games(scholars, tmp_path, depth=10, workers=1)
    assert report.analyzed == 1

    game = read_pgn(report.written[0])
    nodes = list(game.mainline())
    blunder = nodes[5]
    assert blunder.san() == "Nf6"
    assert chess.pgn.NAG_BLUNDER in blunder.nags
    assert blunder.comment == "[%eval #1]"  # White mates in one, in the standard notation
    assert blunder.eval().white().mate() == 1
    # "Better was" hangs off the position before the blunder, the punishment off the blunder itself
    assert len(blunder.parent.variations) == 2
    assert blunder.variations[1].san() == "Qxf7#"
    # every move but the mating one carries a standard eval, and nothing else is a comment
    assert all(node.eval() is not None for node in nodes[:-1])
    assert all(node.comment.startswith("[%eval ") and node.comment.endswith("]") for node in nodes[:-1])


@needs_stockfish
def test_a_second_run_over_the_same_games_analyzes_nothing(tmp_path):
    collection = Collection.read(FIXTURES, **PLAYER)
    first = collection.analyze(tmp_path, depth=DEPTH, workers=2)
    assert first.analyzed == 3
    before = {path.name: path.stat().st_mtime_ns for path in tmp_path.iterdir()}

    # An engine that does not exist: the run fails if it tries to start one.
    second = Collection.read(FIXTURES, **PLAYER).analyze(tmp_path, depth=DEPTH, engine_path="/nonexistent/stockfish")
    assert (second.analyzed, second.skipped) == (0, 3)
    assert {path.name: path.stat().st_mtime_ns for path in tmp_path.iterdir()} == before

    # The library's own output, read back as a collection, is also already analyzed.
    third = Collection.read(tmp_path).analyze(tmp_path, depth=DEPTH, engine_path="/nonexistent/stockfish")
    assert (third.analyzed, third.skipped) == (0, 3)


@needs_stockfish
def test_two_workers_give_the_same_output_as_one(tmp_path):
    collection = Collection.read(FIXTURES, **PLAYER)
    collection.analyze(tmp_path / "one", depth=DEPTH, workers=1)
    collection.analyze(tmp_path / "two", depth=DEPTH, workers=2)
    one, two = contents(tmp_path / "one"), contents(tmp_path / "two")
    assert len(one) == 3
    assert one == two
