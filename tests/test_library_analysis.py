"""The library's Stockfish step (pgn_postmortem.analysis). Every test that
runs Stockfish searches to a fixed depth, and is skipped when no Stockfish
binary is found (CI always installs one)."""

import io
import time
from pathlib import Path

import chess.engine
import chess.pgn
import pytest

from pgn_postmortem import CollectedGame, Collection, analysis, analyze_games
from pgn_postmortem.analysis import EngineFailure, default_engine_path
from pgn_postmortem.collection import ANALYSIS_HEADER, format_game

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
    # the mating move carries no eval at all, as in lichess's exports
    assert nodes[-1].board().is_checkmate()
    assert nodes[-1].comment == ""


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
def test_games_only_read_into_the_output_directory_are_still_analyzed(tmp_path):
    # `read --out games` then `analyze games --out games`: the stripped files have the
    # library's own file names, but nothing has analyzed them yet (review 006, finding 1).
    games = tmp_path / "games"
    Collection.read(FIXTURES, **PLAYER).write(games)
    report = Collection.read(games).analyze(games, depth=DEPTH, workers=2)
    assert (report.analyzed, report.skipped) == (3, 0)
    assert all("[%eval" in path.read_text(encoding="utf-8") for path in games.glob("*.pgn"))

    # Reading strips the analysis marker with everything else, so analyzed games read
    # into another directory are analyzed again there.
    elsewhere = tmp_path / "elsewhere"
    Collection.read(games).write(elsewhere)
    assert Collection.read(elsewhere).analyze(elsewhere, depth=DEPTH, workers=2).analyzed == 3


@needs_stockfish
def test_reading_again_into_an_analyzed_directory_keeps_the_analysis(tmp_path):
    # read, analyze in place, read again (with one new game), analyze again: only the new
    # game is analyzed, and the analyses already there survive (review 006, finding 9).
    games = tmp_path / "games"
    Collection.read(FIXTURES / "club", **PLAYER).write(games)
    assert Collection.read(games).analyze(games, depth=DEPTH, workers=2).analyzed == 2
    analyzed = contents(games)

    written = Collection.read(FIXTURES, **PLAYER).write(games)
    assert [path.name for path in written] == [name for name in contents(games) if name not in analyzed]
    assert {name: text for name, text in contents(games).items() if name in analyzed} == analyzed
    second = Collection.read(games).analyze(games, depth=DEPTH, workers=2)
    assert (second.analyzed, second.skipped) == (1, 2)

    # and once more: nothing is re-analyzed, and every game still has its [%eval] comments
    Collection.read(FIXTURES, **PLAYER).write(games)
    third = Collection.read(games).analyze(games, depth=DEPTH, engine_path="/nonexistent/stockfish")
    assert (third.analyzed, third.skipped) == (0, 3)
    assert all("[%eval" in text for text in contents(games).values())


def test_a_game_analyzed_under_an_unpadded_file_name_is_left_alone(tmp_path):
    # Before file names were zero-padded (review 006, round 03, finding 14), a Date of
    # 2019.3.14 was written to 2019-3-14-<id>.pgn. That analysis must still count: reading
    # the game into the directory again writes no second copy under the padded name, and
    # analyzing it again does nothing. No Stockfish needed: the engine is never started.
    source = tmp_path / "source.pgn"
    source.write_text(
        '[Date "2019.3.14"]\n[White "Ada Example"]\n[Black "Rival"]\n[Result "1-0"]\n\n'
        "1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0\n",
        encoding="utf-8",
    )
    (item,) = Collection.read(source)
    assert item.filename == f"2019-03-14-{item.id}.pgn"
    analyzed = chess.pgn.read_game(io.StringIO(format_game(item.game)))
    analyzed.headers[ANALYSIS_HEADER] = "Stockfish 16, depth 8"
    games = tmp_path / "games"
    games.mkdir()
    old = games / f"2019-3-14-{item.id}.pgn"
    old.write_text(format_game(analyzed), encoding="utf-8")
    before = old.read_text(encoding="utf-8")

    assert Collection.read(source).write(games) == []
    report = Collection.read(source).analyze(games, engine_path="/nonexistent/stockfish")
    assert (report.analyzed, report.skipped) == (0, 1)
    assert [path.name for path in games.iterdir()] == [old.name]
    assert old.read_text(encoding="utf-8") == before


@needs_stockfish
def test_two_workers_give_the_same_output_as_one(tmp_path):
    collection = Collection.read(FIXTURES, **PLAYER)
    collection.analyze(tmp_path / "one", depth=DEPTH, workers=1)
    collection.analyze(tmp_path / "two", depth=DEPTH, workers=2)
    one, two = contents(tmp_path / "one"), contents(tmp_path / "two")
    assert len(one) == 3
    assert one == two


def test_an_engine_failure_stops_the_run_at_the_first_failed_game(tmp_path, monkeypatch):
    # No Stockfish needed: a stand-in engine, and an analysis whose first game fails
    # the way a crashed engine does (review 006, finding 5).
    class StandInEngine:
        id = {"name": "Stand-in"}
        options = {}

        def configure(self, options):
            pass

        def quit(self):
            pass

    monkeypatch.setattr(chess.engine.SimpleEngine, "popen_uci", lambda *args, **kwargs: StandInEngine())
    started = []

    def analyze_game(engine, limit, source, engine_game, *args):
        started.append(engine_game)
        if len(started) == 1:
            raise chess.engine.EngineTerminatedError("engine process died unexpectedly (exit code: 1)")
        time.sleep(0.5)
        return source

    monkeypatch.setattr(analysis, "analyze_game", analyze_game)
    games = [CollectedGame(f"g{i:02d}", chess.pgn.Game(), f"fake.pgn#{i + 1}") for i in range(20)]
    with pytest.raises(EngineFailure, match="failed on fake.pgn#1"):
        analyze_games(games, tmp_path, workers=1)
    # the queued games are cancelled, not each tried against a dead engine first
    assert len(started) <= 2
