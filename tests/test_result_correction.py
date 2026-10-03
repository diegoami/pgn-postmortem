"""Correcting the recorded result from the final position (ROADMAP.md, F-14),
on the hand-written fixtures in tests/fixtures/site/corrections/ (their README
says what each game is). No test here runs Stockfish: the correction reads
the final [%eval] already in each analyzed file, and the analysis option is
tested with the engine stubbed.
"""

import os
import subprocess
import sys
from pathlib import Path

import chess.pgn
import pytest

import pgn_postmortem.analysis as analysis
from pgn_postmortem import Collection, correct_results, decided_result
from pgn_postmortem.analysis import win_percent
from pgn_postmortem.collection import ANALYSIS_HEADER, ID_HEADER, ORIGINAL_RESULT_HEADER, format_game, game_id
from pgn_postmortem.results import correct_game, final_white_chances
from pgn_postmortem.site import build_site

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "site" / "corrections"

# file -> (recorded, corrected); None: left as recorded
CASES = {
    "loss-is-win.pgn": ("0-1", "1-0"),
    "win-is-draw.pgn": ("1-0", "1/2-1/2"),
    "draw-is-loss.pgn": ("1/2-1/2", "0-1"),
    "unrecorded-is-win.pgn": ("*", "1-0"),
    "mate-score.pgn": ("1/2-1/2", "0-1"),
    "checkmate-is-draw.pgn": ("1/2-1/2", "0-1"),
    "stalemate-is-win.pgn": ("1-0", "1/2-1/2"),
}
UNTOUCHED = ["agrees.pgn", "no-final-eval.pgn", "not-analyzed.pgn"]


def load(path: Path) -> chess.pgn.Game:
    with open(path, encoding="utf-8") as handle:
        return chess.pgn.read_game(handle)


DATES = {  # each fixture's date, which is how its copy in the analysis directory is found
    "2013.01.01": "loss-is-win.pgn",
    "2013.01.02": "win-is-draw.pgn",
    "2013.01.03": "draw-is-loss.pgn",
    "2013.01.04": "agrees.pgn",
    "2013.01.05": "unrecorded-is-win.pgn",
    "2013.01.06": "mate-score.pgn",
    "2013.01.07": "no-final-eval.pgn",
    "2013.01.08": "not-analyzed.pgn",
    "2013.01.09": "checkmate-is-draw.pgn",
    "2013.01.10": "stalemate-is-win.pgn",
}


@pytest.fixture
def analyzed(tmp_path) -> Path:
    """The fixtures as an analysis directory: each game under the file name
    and with the ``PostmortemId`` the analysis step gives it (``<date>-<id>.pgn``)."""
    out = tmp_path / "analyzed"
    out.mkdir()
    for item in Collection.read(FIXTURES, keep_analysis=True):
        (out / item.filename).write_text(format_game(item.game), encoding="utf-8")
    return out


def where(directory: Path, name: str) -> Path:
    """The file of fixture ``name`` in ``directory``."""
    (path,) = [p for p in directory.glob("*.pgn") if DATES[load(p).headers["Date"]] == name]
    return path


def results(directory: Path) -> dict[str, tuple[str, str | None]]:
    """Fixture name -> (Result, OriginalResult) of its copy in ``directory``."""
    out = {}
    for path in sorted(directory.glob("*.pgn")):
        headers = load(path).headers
        out[DATES[headers["Date"]]] = (headers["Result"], headers.get(ORIGINAL_RESULT_HEADER))
    return out


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "pgn_postmortem", *args], cwd=cwd, env=env, capture_output=True, text=True, timeout=120
    )


# --- the rule ---------------------------------------------------------------------


@pytest.mark.parametrize(("name", "expected"), [(n, v[1]) for n, v in CASES.items()])
def test_the_rule_gives_the_verdict(name, expected):
    assert decided_result(load(FIXTURES / name)) == expected


def test_no_verdict_without_a_board_result_or_a_final_eval():
    assert decided_result(load(FIXTURES / "no-final-eval.pgn")) is None
    assert decided_result(load(FIXTURES / "not-analyzed.pgn")) is None  # an eval is not trusted without the marker


def test_the_board_decides_before_the_eval():
    # stalemate-is-win carries an eval of 5.00 (86%): still a draw
    assert final_white_chances(load(FIXTURES / "stalemate-is-win.pgn")) > 80
    assert decided_result(load(FIXTURES / "stalemate-is-win.pgn")) == "1/2-1/2"


def test_the_threshold_edge_counts_as_a_win_for_either_side():
    game = load(FIXTURES / "loss-is-win.pgn")
    chances = win_percent(275)
    assert decided_result(game, chances) == "1-0"
    assert decided_result(game, chances + 0.001) == "1/2-1/2"
    black = load(FIXTURES / "draw-is-loss.pgn")
    assert decided_result(black, win_percent(275)) == "0-1"
    assert decided_result(black, win_percent(275) + 0.001) == "1/2-1/2"
    assert decided_result(game, 80) == "1/2-1/2"  # the parameter is used


@pytest.mark.parametrize("bad", [54.9, 95.1, float("nan"), 0, 100])
def test_a_threshold_outside_55_to_95_is_rejected(bad, analyzed):
    before = results(analyzed)
    with pytest.raises(ValueError, match="presume_threshold"):
        decided_result(load(FIXTURES / "loss-is-win.pgn"), bad)
    with pytest.raises(ValueError, match="presume_threshold"):
        correct_results(analyzed, presume_threshold=bad)
    assert results(analyzed) == before


# --- correcting a directory ---------------------------------------------------------


def test_a_directory_is_corrected_and_reported(analyzed):
    report = correct_results(analyzed)
    after = results(analyzed)
    for name, (recorded, corrected) in CASES.items():
        assert after[name] == (corrected, recorded), name
    for name in UNTOUCHED:
        assert after[name][1] is None, name
    assert after["agrees.pgn"][0] == "1-0"
    assert after["no-final-eval.pgn"][0] == "1-0"
    assert after["not-analyzed.pgn"][0] == "0-1"
    assert len(report.changes) == len(CASES)
    assert (report.unchanged, report.no_verdict, report.skipped) == (1, 1, 1)
    assert {(c.path, c.old, c.new) for c in report.changes} == {
        (where(analyzed, name).name, recorded, corrected) for name, (recorded, corrected) in CASES.items()
    }
    assert "Changed 7 game(s); 1 already agree, 1 without a verdict" in report.summary()
    line = next(c.line() for c in report.changes if c.path == where(analyzed, "loss-is-win.pgn").name)
    assert line.endswith(": 0-1 -> 1-0 (Ada Example vs. Bert Sample, corrected)")


def test_the_file_changes_only_in_its_headers_and_a_second_run_changes_nothing(analyzed):
    path = where(analyzed, "loss-is-win.pgn")
    original = path.read_text(encoding="utf-8").splitlines()
    correct_results(analyzed)
    corrected = path.read_text(encoding="utf-8").splitlines()
    assert [line for line in corrected if line not in original][:2] == ['[Result "1-0"]', '[OriginalResult "0-1"]']
    assert [line for line in original if line not in corrected][:1] == ['[Result "0-1"]']
    assert path.read_text(encoding="utf-8").count("[%eval") == 6 and original[-1].endswith("0-1")
    snapshot = {p.name: p.read_bytes() for p in analyzed.glob("*.pgn")}
    again = correct_results(analyzed)
    assert again.changes == []
    assert (again.unchanged, again.no_verdict, again.skipped) == (len(CASES) + 1, 1, 1)
    assert {p.name: p.read_bytes() for p in analyzed.glob("*.pgn")} == snapshot
    assert not list(analyzed.glob("*.partial"))


def test_dry_run_reports_and_writes_nothing(analyzed):
    snapshot = {p.name: p.read_bytes() for p in analyzed.glob("*.pgn")}
    report = correct_results(analyzed, dry_run=True)
    assert len(report.changes) == len(CASES)
    assert report.summary().startswith("Would change 7 game(s)")
    assert {p.name: p.read_bytes() for p in analyzed.glob("*.pgn")} == snapshot


def test_a_missing_path_is_an_error():
    with pytest.raises(FileNotFoundError):
        correct_results("no/such/directory")


def test_a_file_with_two_games_or_none_is_skipped_with_a_warning(tmp_path):
    two = tmp_path / "two.pgn"
    text = (FIXTURES / "loss-is-win.pgn").read_text(encoding="utf-8")
    two.write_text(text + "\n" + text, encoding="utf-8")
    (tmp_path / "empty.pgn").write_text("", encoding="utf-8")
    report = correct_results(tmp_path)
    assert (report.skipped, report.changes) == (2, [])
    assert len(report.warnings) == 2
    assert two.read_text(encoding="utf-8") == text + "\n" + text


def test_the_original_is_never_overwritten_by_a_corrected_value(analyzed):
    correct_results(analyzed)  # 0-1 -> 1-0 at 70
    report = correct_results(analyzed, presume_threshold=60)  # 73% is still a win at 60: nothing changes
    assert report.changes == []
    # at 80 the verdict becomes a draw: the original stays the source's 0-1, not the corrected 1-0
    report = correct_results(analyzed, presume_threshold=80)
    changed = {c.path: c for c in report.changes}[where(analyzed, "loss-is-win.pgn").name]
    assert (changed.old, changed.new) == ("1-0", "1/2-1/2")
    assert results(analyzed)["loss-is-win.pgn"] == ("1/2-1/2", "0-1")


def test_a_verdict_equal_to_the_source_restores_it_and_drops_the_header(analyzed):
    correct_results(analyzed)  # win-is-draw: 1-0 recorded, now 1/2-1/2
    game = load(where(analyzed, "win-is-draw.pgn"))
    game.end().comment = "[%eval 2.75]"  # now the final position says a win again
    change = correct_game(game)
    assert change is not None and change.kind == "restored"
    assert game.headers["Result"] == "1-0"
    assert ORIGINAL_RESULT_HEADER not in game.headers


# --- identity -------------------------------------------------------------------------


def test_a_correction_changes_no_id_no_file_name_and_no_match_with_the_source(analyzed, tmp_path):
    source = tmp_path / "source"
    # the source: the same games, stripped, as read from an export
    Collection.read(FIXTURES / "loss-is-win.pgn").write(source)
    (stripped,) = Collection.read(source)
    before = Collection.read(analyzed, keep_analysis=True)
    ids_before = {item.filename: item.id for item in before}
    correct_results(analyzed)
    after = Collection.read(analyzed, keep_analysis=True)
    assert {item.filename: item.id for item in after} == ids_before
    assert sorted(p.name for p in analyzed.glob("*.pgn")) == sorted(ids_before)  # file names are unchanged
    assert all(name.endswith(f"-{gid}.pgn") for name, gid in ids_before.items())
    (item,) = [i for i in after if i.filename == stripped.filename]
    assert item.game.headers["Result"] == "1-0"  # the analyzed copy is corrected...
    assert item.id == stripped.id and game_id(item.game) == stripped.id  # ...and has the source's id
    assert stripped.game.headers["Result"] == "0-1"
    # read with its source, they are one game, and the analyzed copy is the one kept
    both = Collection.read([source, where(analyzed, "loss-is-win.pgn")], keep_analysis=True)
    assert len(both) == 1 and both.report.duplicates == 1
    assert ANALYSIS_HEADER in both.games[0].game.headers
    # and the analysis step would not redo it: reading the source in does not overwrite it
    assert Collection.read(source).write(analyzed) == []
    assert results(analyzed)["loss-is-win.pgn"] == ("1-0", "0-1")


def test_reading_without_the_analysis_restores_the_source_result(analyzed):
    correct_results(analyzed)
    # read stripped, the analysis and its correction are dropped
    (item,) = Collection.read(where(analyzed, "loss-is-win.pgn"))
    assert item.game.headers["Result"] == "0-1"
    assert ORIGINAL_RESULT_HEADER not in item.game.headers
    assert ANALYSIS_HEADER not in item.game.headers
    assert "[%eval" not in str(item.game)


def test_an_original_result_header_of_a_source_game_is_not_believed(tmp_path):
    text = (FIXTURES / "not-analyzed.pgn").read_text(encoding="utf-8").replace(
        '[Result "0-1"]', '[Result "0-1"]\n[OriginalResult "1-0"]'
    )
    path = tmp_path / "g.pgn"
    path.write_text(text, encoding="utf-8")
    plain = load(FIXTURES / "not-analyzed.pgn")
    assert Collection.read(path).games[0].id == game_id(plain)  # the id still hashes Result
    assert correct_game(load(path)) is None


# --- in memory, and at analysis time ----------------------------------------------------


def test_a_collection_corrects_in_memory_and_keeps_ids(analyzed):
    games = Collection.read(analyzed, keep_analysis=True)
    ids = [item.id for item in games]
    report = games.correct_results()
    assert [item.id for item in games] == ids
    assert len(report.changes) == len(CASES) and report.skipped == 1
    assert sorted(c.new for c in report.changes) == sorted(v[1] for v in CASES.values())
    assert games.correct_results().changes == []  # idempotent
    assert results(analyzed)["loss-is-win.pgn"] == ("0-1", None)  # nothing was written
    with pytest.raises(ValueError):
        games.correct_results(40)


def fake_engine(monkeypatch, source: Path):
    """No Stockfish: the analysis of every game is the hand-written fixture."""
    started = []

    class Engine:
        options = {}

        def configure(self, options):
            pass

        def quit(self):
            pass

    monkeypatch.setattr(analysis.chess.engine.SimpleEngine, "popen_uci", lambda path: started.append(path) or Engine())
    monkeypatch.setattr(analysis, "describe_analysis", lambda engine, limit: "stub")

    def analyze_game(engine, limit, game, engine_game, pv_plies, thresholds):
        out = load(source)
        out.headers[ANALYSIS_HEADER] = "stub"
        out.headers["Result"] = game.headers["Result"]  # as the real step copies the source's headers
        out.headers[ID_HEADER] = game.headers[ID_HEADER]
        return out

    monkeypatch.setattr(analysis, "analyze_game", analyze_game)
    return started


def test_analysis_corrects_new_games_when_asked(tmp_path, monkeypatch):
    source = FIXTURES / "loss-is-win.pgn"
    games = Collection.read(source)
    gid = games.games[0].id
    started = fake_engine(monkeypatch, source)
    games.analyze(tmp_path / "off", depth=1, workers=1, engine_path="x")
    assert results(tmp_path / "off") == {"loss-is-win.pgn": ("0-1", None)}
    games.analyze(tmp_path / "on", depth=1, workers=1, engine_path="x", correct_results=True)
    assert results(tmp_path / "on") == {"loss-is-win.pgn": ("1-0", "0-1")}
    assert len(started) == 2
    # the file name and id are those of the source, and the game is then "already analyzed"
    assert (tmp_path / "on" / games.games[0].filename).exists()
    assert analysis.analyzed_ids(tmp_path / "on") == {gid}
    report = games.analyze(tmp_path / "on", depth=1, workers=1, engine_path="x", correct_results=True)
    assert (report.analyzed, report.skipped) == (0, 1)
    assert len(started) == 2


def test_analysis_validates_the_threshold_before_any_engine_starts(tmp_path, monkeypatch):
    started = fake_engine(monkeypatch, FIXTURES / "loss-is-win.pgn")
    games = Collection.read(FIXTURES / "loss-is-win.pgn")
    with pytest.raises(ValueError, match="presume_threshold"):
        games.analyze(tmp_path / "out", correct_results=True, presume_threshold=40)
    with pytest.raises(ValueError, match="presume_threshold"):
        Collection([]).analyze(tmp_path / "out", correct_results=True, presume_threshold=96)  # even when empty
    assert started == [] and not (tmp_path / "out").exists()


# --- the command line ---------------------------------------------------------------------


def test_the_command_line_lists_corrects_and_is_idempotent(analyzed):
    dry = run_cli("correct-results", str(analyzed), "--dry-run", cwd=analyzed)
    assert dry.returncode == 0, dry.stderr
    assert ": 0-1 -> 1-0 (Ada Example vs. Bert Sample, corrected)" in dry.stdout
    assert dry.stdout.strip().splitlines()[-1].startswith("Would change 7 game(s); 1 already agree")
    assert results(analyzed)["loss-is-win.pgn"] == ("0-1", None)

    run = run_cli("correct-results", str(analyzed), cwd=analyzed)
    assert run.returncode == 0, run.stderr
    assert ": 1-0 -> 1/2-1/2 (Ada Example vs. Bert Sample, corrected)" in run.stdout
    assert run.stdout.strip().splitlines()[-1].startswith("Changed 7 game(s)")
    assert results(analyzed)["loss-is-win.pgn"] == ("1-0", "0-1")
    again = run_cli("correct-results", str(analyzed), cwd=analyzed)
    assert again.stdout.strip().splitlines() == [
        "Changed 0 game(s); 8 already agree, 1 without a verdict from the final position, 1 skipped."
    ]


def test_the_command_line_rejects_a_bad_threshold_before_writing(analyzed):
    before = {p.name: p.read_bytes() for p in analyzed.glob("*.pgn")}
    run = run_cli("correct-results", str(analyzed), "--threshold", "99", cwd=analyzed)
    assert run.returncode == 1 and "presume_threshold must be from 55 to 95" in run.stderr
    run = run_cli("analyze", str(analyzed), "--out", "o", "--correct-results", "--result-threshold", "10", cwd=analyzed)
    assert run.returncode == 1 and "presume_threshold must be from 55 to 95" in run.stderr
    assert {p.name: p.read_bytes() for p in analyzed.glob("*.pgn")} == before
    assert not (analyzed / "o").exists()
    missing = run_cli("correct-results", "nowhere", cwd=analyzed)
    assert missing.returncode == 1 and "no such file or directory" in missing.stderr


# --- the site -------------------------------------------------------------------------------


def article(site: Path, games: Collection, name: str) -> str:
    item = next(i for i in games if i.filename == name)
    return (site / "games" / f"{item.filename[:-4]}.html").read_text(encoding="utf-8")


def test_the_site_shows_the_corrected_result_and_says_the_source_recorded_another(analyzed, tmp_path):
    correct_results(analyzed)
    games = Collection.read(analyzed, keep_analysis=True)
    site = tmp_path / "site"
    build_site(games, site)
    html = article(site, games, next(i.filename for i in games if i.game.headers["Date"] == "2013.01.01"))
    assert "<th>Result</th><td>1–0</td>" in html
    assert "<th>Source result</th><td>0–1</td>" in html
    assert "The source recorded 0–1; the result was corrected from the final position." in html
    assert "came from outside the position" not in html
    agrees = article(site, games, next(i.filename for i in games if i.game.headers["Date"] == "2013.01.04"))
    assert "Source result" not in agrees and "corrected from the final position" not in agrees
    unrecorded = article(site, games, next(i.filename for i in games if i.game.headers["Date"] == "2013.01.05"))
    assert "<th>Source result</th><td>Not recorded</td>" in unrecorded
    assert "The source recorded no result;" in unrecorded


def test_the_site_builds_the_same_without_a_correction_for_games_that_were_not_corrected(analyzed, tmp_path):
    games = Collection.read(analyzed, keep_analysis=True)
    build_site(games, tmp_path / "plain")  # without a correction: F-5's behaviour, a source's result as recorded
    html = article(tmp_path / "plain", games, next(i.filename for i in games if i.game.headers["Date"] == "2013.01.01"))
    assert "<th>Result</th><td>0–1</td>" in html and "Source result" not in html
