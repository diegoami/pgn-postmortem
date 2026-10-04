"""Customizable result correction (ROADMAP.md, F-15): the policies, the skip
rules, the reports, the manifest keys and the analysis option, on the
hand-written fixtures of F-14 (tests/fixtures/site/corrections/). No Stockfish.
"""

import itertools
import re
from pathlib import Path

import pytest

from pgn_postmortem import Collection, correct_results
from pgn_postmortem.cli import main
from pgn_postmortem.collection import game_id
from pgn_postmortem.results import (
    POLICIES,
    CorrectionReport,
    decide_game,
    header_skip,
    target_result,
)
from pgn_postmortem.workspace import CollectionProfile, Workspace, WorkspaceConfigError
from tests.test_result_correction import (
    CASES,
    analyzed,  # noqa: F401  (a fixture)
    fake_engine,
    load,
    results,
    run_cli,
    where,
)

W, B, D, U = "1-0", "0-1", "1/2-1/2", "*"

# Literal tables of the policies (docs/result-correction.md): for each policy, the original result and the
# verdict give the result the header holds. "-" keeps the original. Each row: original -> verdicts 1-0, 0-1, 1/2-1/2.
# The "board" policy's table is the "all" table, applied only when the board decided the verdict.
ALL = {W: (W, B, D), B: (W, B, D), D: (W, B, D), U: (W, B, D)}
TABLES = {
    "all": ALL,
    "contradictions": {W: (W, B, W), B: (W, B, B), D: (W, B, D), U: (U, U, U)},
    "unrecorded": {W: (W, W, W), B: (B, B, B), D: (D, D, D), U: (W, B, D)},
}
VERDICTS = (W, B, D)


@pytest.mark.parametrize(
    ("policy", "original", "verdict", "by_board"),
    list(itertools.product(POLICIES, (W, B, D, U), VERDICTS, (True, False))),
)
def test_every_recorded_result_and_verdict_gives_the_tabulated_outcome(policy, original, verdict, by_board):
    col = VERDICTS.index(verdict)
    if policy == "board":
        expected = ALL[original][col] if by_board else original
    else:
        expected = TABLES[policy][original][col]
    assert target_result(policy, original, verdict, by_board) == expected


@pytest.mark.parametrize("original", ["", "1/2", "unknown"])
def test_a_missing_or_odd_result_counts_as_unrecorded(original):
    assert target_result("unrecorded", original, B, False) == B
    assert target_result("all", original, B, False) == B
    assert target_result("contradictions", original, B, False) == original
    assert target_result("board", original, B, False) == original
    assert target_result("board", original, B, True) == B


def test_no_verdict_and_unknown_policies():
    for policy in POLICIES:
        assert target_result(policy, B, None, False) == B
    with pytest.raises(ValueError, match="result policy must be one of all, contradictions, unrecorded, board"):
        target_result("everything", B, W, True)


# --- each policy on the directory -------------------------------------------------

# fixture -> what each policy makes of it (None: left as recorded)
EXPECTED = {
    "all": {name: new for name, (_, new) in CASES.items()},
    "contradictions": {
        "loss-is-win.pgn": W,
        "draw-is-loss.pgn": B,
        "mate-score.pgn": B,
        "checkmate-is-draw.pgn": B,
    },
    "unrecorded": {"unrecorded-is-win.pgn": W},
    "board": {"checkmate-is-draw.pgn": B, "stalemate-is-win.pgn": D},
}


@pytest.mark.parametrize("policy", POLICIES)
def test_each_policy_corrects_what_it_says_and_nothing_else(analyzed, policy):  # noqa: F811
    report = correct_results(analyzed, policy=policy)
    after = results(analyzed)
    for name, (recorded, _) in CASES.items():
        if name in EXPECTED[policy]:
            assert after[name] == (EXPECTED[policy][name], recorded), name
        else:
            assert after[name] == (recorded, None), name
    assert {d.path for d in report.decisions if d.change} == {where(analyzed, n).name for n in EXPECTED[policy]}
    assert len(report.changes) == len(EXPECTED[policy])
    assert report.policy == policy
    assert report.kept_policy == len(CASES) - len(EXPECTED[policy])
    assert correct_results(analyzed, policy=policy).changes == []  # a second run changes nothing


def test_the_default_policy_is_all(analyzed):  # noqa: F811
    assert correct_results(analyzed, dry_run=True).policy == "all"
    assert len(correct_results(analyzed, dry_run=True).changes) == len(CASES)


def test_contradictions_never_makes_a_decisive_result_a_draw(analyzed):  # noqa: F811
    correct_results(analyzed, policy="contradictions")
    after = results(analyzed)
    assert after["win-is-draw.pgn"] == (W, None)  # recorded win, level position: kept
    assert after["stalemate-is-win.pgn"] == (W, None)  # a stalemate is for the board policy
    assert after["unrecorded-is-win.pgn"] == (U, None)  # and it does not fill in "*"


def test_a_narrower_policy_restores_what_it_would_not_correct(analyzed):  # noqa: F811
    correct_results(analyzed, policy="all")
    report = correct_results(analyzed, policy="board")
    after = results(analyzed)
    assert {c.kind for c in report.changes} == {"restored"}
    assert len(report.changes) == len(CASES) - len(EXPECTED["board"])
    for name, (recorded, _) in CASES.items():
        assert after[name] == ((EXPECTED["board"][name], recorded) if name in EXPECTED["board"] else (recorded, None))


def test_the_statuses_say_why(analyzed):  # noqa: F811
    correct_results(analyzed, policy="contradictions")
    report = correct_results(analyzed, policy="contradictions")
    status = {d.path: d.status for d in report.decisions}
    assert status[where(analyzed, "loss-is-win.pgn").name] == "kept: agrees"
    assert status[where(analyzed, "win-is-draw.pgn").name] == "kept: policy"
    assert status[where(analyzed, "no-final-eval.pgn").name] == "kept: no verdict"
    assert "not-analyzed.pgn" not in [p for p in status]  # not analyzed: a skipped file, not a decision
    assert (report.unchanged, report.kept_policy, report.no_verdict, report.excluded, report.skipped) == (5, 3, 1, 0, 1)
    assert "3 kept by the policy" in report.summary() and "excluded" not in report.summary()


# --- skipping -------------------------------------------------------------------------


def test_a_skip_callable_leaves_games_as_they_are(analyzed):  # noqa: F811
    seen = []

    def skip(game):
        seen.append(game.headers["Date"])
        return game.headers["Date"] in ("2013.01.01", "2013.01.02")

    report = correct_results(analyzed, skip=skip)
    after = results(analyzed)
    assert after["loss-is-win.pgn"] == (B, None) and after["win-is-draw.pgn"] == (W, None)
    assert after["draw-is-loss.pgn"] == (B, D)
    assert report.excluded == 2 and len(report.changes) == len(CASES) - 2
    assert sorted(seen) == sorted(d for d in seen if d != "2013.01.08")  # only analyzed games are offered
    assert "2013.01.08" not in seen
    assert [d.status for d in report.decisions if d.path == where(analyzed, "loss-is-win.pgn").name] == [
        "kept: skipped"
    ]
    assert "2 excluded by the skip rule" in report.summary()


def test_a_skipped_game_is_left_even_if_an_earlier_run_corrected_it(analyzed):  # noqa: F811
    correct_results(analyzed)
    report = correct_results(analyzed, skip=header_skip(["Date=^2013.01.01$"]), policy="board")
    after = results(analyzed)
    assert after["loss-is-win.pgn"] == (W, B)  # kept corrected, not restored
    assert report.excluded == 1


def test_header_rules(analyzed):  # noqa: F811
    game = load(where(analyzed, "loss-is-win.pgn"))
    assert header_skip([]) is None
    assert header_skip(["Site=Verona"])(game)
    assert header_skip(["Nope=x", "Site=^Ve"])(game)  # any rule
    assert not header_skip(["Site=verona"])(game)  # case sensitive
    assert header_skip(["Site=(?i)verona"])(game)
    assert not header_skip(["Termination=.*"])(game)  # a missing header never matches
    assert header_skip([f"PostmortemId=^{game.headers['PostmortemId']}$"])(game)
    for bad in ("Site", "=x", "Site=("):
        with pytest.raises(ValueError, match="skip rule"):
            header_skip([bad])


# --- the reports on the command line ------------------------------------------------


def test_the_command_reports_policy_reasons_and_skip_rules(analyzed):  # noqa: F811
    dry = run_cli(
        "correct-results", str(analyzed), "--policy", "contradictions", "--skip-header", "Date=^2013.01.03$",
        "--dry-run", "--explain", cwd=analyzed,
    )  # fmt: skip
    assert dry.returncode == 0, dry.stderr
    lines = dry.stdout.strip().splitlines()
    assert lines[0] == "Policy: contradictions, threshold 70."
    assert lines[1] == "Skip rules: Date=^2013.01.03$"
    assert any(re.search(r": 0-1 -> 1-0 \(.*, corrected\)$", line) for line in lines)
    assert any(line.endswith(": kept: policy (1-0, the final position says 1/2-1/2)") for line in lines)
    assert any(line.endswith(": kept: skipped (1/2-1/2)") for line in lines)
    assert any(line.endswith(": kept: no verdict (1-0)") for line in lines)
    assert lines[-1].startswith("Would change 3 game(s);") and "excluded by the skip rule" in lines[-1]
    assert results(analyzed)["loss-is-win.pgn"] == (B, None)  # a dry run writes nothing
    quiet = run_cli("correct-results", str(analyzed), "--policy", "board", cwd=analyzed)
    assert "kept:" not in quiet.stdout and quiet.stdout.splitlines()[0] == "Policy: board, threshold 70."
    assert results(analyzed)["stalemate-is-win.pgn"] == (D, W)


def test_the_command_rejects_bad_policies_and_rules(analyzed):  # noqa: F811
    before = {p.name: p.read_bytes() for p in analyzed.glob("*.pgn")}
    for args in (["--policy", "everything"], ["--skip-header", "Site"], ["--skip-header", "Site=("]):
        run = run_cli("correct-results", str(analyzed), *args, cwd=analyzed)
        assert run.returncode == 2, args
    run = run_cli("analyze", str(analyzed), "--out", "o", "--result-policy", "board", cwd=analyzed)
    assert run.returncode == 1 and "--result-policy only applies with --correct-results" in run.stderr
    run = run_cli("analyze", str(analyzed), "--out", "o", "--result-skip-header", "Site=x", cwd=analyzed)
    assert run.returncode == 1 and "--result-skip-header only applies with --correct-results" in run.stderr
    assert {p.name: p.read_bytes() for p in analyzed.glob("*.pgn")} == before and not (analyzed / "o").exists()


def test_the_help_explains_the_policies():
    for command in (["correct-results"], ["analyze"]):
        run = run_cli(*command, "--help", cwd=Path.cwd())
        for word in ("contradictions", "unrecorded", "board", "level position", "NAME=REGEX"):
            assert word in run.stdout.replace("\n", " ") or word in " ".join(run.stdout.split()), (command, word)


# --- at analysis time ---------------------------------------------------------------------


def test_analysis_applies_the_policy_and_the_skip_rule(tmp_path, monkeypatch):
    from tests.test_result_correction import FIXTURES

    source = FIXTURES / "loss-is-win.pgn"
    games = Collection.read(source)
    fake_engine(monkeypatch, source)
    board = games.analyze(tmp_path / "board", depth=1, workers=1, engine_path="x", correct_results=True,
                          result_policy="board")  # fmt: skip
    assert board.corrections == [] and results(tmp_path / "board") == {"loss-is-win.pgn": (B, None)}
    skipped = games.analyze(tmp_path / "skip", depth=1, workers=1, engine_path="x", correct_results=True,
                            result_skip=header_skip(["Site=Verona"]))  # fmt: skip
    assert skipped.corrections == [] and results(tmp_path / "skip") == {"loss-is-win.pgn": (B, None)}
    contra = games.analyze(tmp_path / "c", depth=1, workers=1, engine_path="x", correct_results=True,
                           result_policy="contradictions")  # fmt: skip
    assert [(c.old, c.new) for c in contra.corrections] == [(B, W)]
    with pytest.raises(ValueError, match="only apply with correct_results"):
        games.analyze(tmp_path / "x", result_policy="board")
    with pytest.raises(ValueError, match="only apply with correct_results"):
        games.analyze(tmp_path / "x", result_skip=lambda game: True)
    with pytest.raises(ValueError, match="result policy"):
        games.analyze(tmp_path / "x", correct_results=True, result_policy="nope")


# --- in memory ------------------------------------------------------------------------------


def test_a_collection_corrects_in_memory_under_a_policy_and_skip(analyzed):  # noqa: F811
    games = Collection.read(analyzed, keep_analysis=True)
    ids = [item.id for item in games]
    report = games.correct_results(policy="board", skip=lambda game: game.headers["Date"] == "2013.01.09")
    assert [item.id for item in games] == ids and all(item.id == game_id(item.game) for item in games)
    assert [c.new for c in report.changes] == [D] and report.excluded == 1
    assert isinstance(report, CorrectionReport) and report.policy == "board"
    assert results(analyzed)["stalemate-is-win.pgn"] == (W, None)  # nothing was written
    with pytest.raises(ValueError, match="result policy"):
        games.correct_results(policy="nope")


def test_decide_game_never_touches_a_game_without_the_marker(analyzed):  # noqa: F811
    game = load(where(analyzed, "not-analyzed.pgn"))
    assert decide_game(game, policy="all") is None and game.headers["Result"] == B


# --- the manifest ------------------------------------------------------------------------------


def manifest_for(tmp_path: Path, analyzed_dir: Path, extra: str = "") -> Path:
    path = tmp_path / "collections.toml"
    path.write_text(
        f'''[[collection]]
slug = "otb"
title = "Over-the-board games"
inputs = ["{analyzed_dir.as_posix()}"]
description = "OTB"
{extra}
''',
        encoding="utf-8",
    )
    return path


def article_html(site: Path, date: str) -> str:
    (page,) = [p for p in (site / "otb" / "games").glob(f"{date.replace('.', '-')}-*.html")]
    return page.read_text(encoding="utf-8")


def test_manifest_keys_correct_in_memory_without_writing_a_file(tmp_path, analyzed):  # noqa: F811
    before = {p.name: p.read_bytes() for p in analyzed.glob("*.pgn")}
    config = manifest_for(
        tmp_path, analyzed,
        'correct_results = "contradictions"\nresult_threshold = 70\nresult_skip_headers = ["Date=^2013.01.03$"]',
    )  # fmt: skip
    report = Workspace.from_toml(config).build(tmp_path / "site")
    assert {p.name: p.read_bytes() for p in analyzed.glob("*.pgn")} == before  # no input file was rewritten
    correction = report.corrections["otb"]
    assert (correction.policy, correction.excluded, len(correction.changes)) == ("contradictions", 1, 3)
    corrected = article_html(tmp_path / "site", "2013.01.01")
    assert "<th>Result</th><td>1–0</td>" in corrected and "<th>Source result</th><td>0–1</td>" in corrected
    kept = article_html(tmp_path / "site", "2013.01.03")  # skipped: the source's result as recorded
    assert "<th>Result</th><td>½–½</td>" in kept and "Source result" not in kept
    level = article_html(tmp_path / "site", "2013.01.02")  # contradictions leaves a win in a level position
    assert "<th>Result</th><td>1–0</td>" in level and "Source result" not in level


def test_manifest_without_the_keys_corrects_nothing(tmp_path, analyzed):  # noqa: F811
    report = Workspace.from_toml(manifest_for(tmp_path, analyzed)).build(tmp_path / "site")
    assert report.corrections == {}
    html = article_html(tmp_path / "site", "2013.01.01")
    assert "<th>Result</th><td>0–1</td>" in html and "Source result" not in html


def test_the_workspace_command_reports_the_correction(tmp_path, analyzed, capsys):  # noqa: F811
    config = manifest_for(tmp_path, analyzed, 'correct_results = "board"')
    assert main(["workspace", str(config), "--out", str(tmp_path / "site")]) == 0
    out = capsys.readouterr().out
    assert "otb: result correction in memory. Policy: board, threshold 70. Changed 2 game(s)" in out


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ('correct_results = "everything"', "result policy must be one of"),
        ("correct_results = true", "correct_results must be a policy name"),
        ('correct_results = "all"\nresult_threshold = 99', "presume_threshold must be from 55 to 95"),
        ('correct_results = "all"\nresult_threshold = "70"', "result_threshold must be a number"),
        ('correct_results = "all"\nresult_skip_headers = ["Site"]', "skip rule"),
        ('correct_results = "all"\nresult_skip_headers = ["Site=("]', "invalid regular expression"),
        ('correct_results = "all"\nresult_skip_headers = "Site=x"', "list of NAME=REGEX"),
        ("result_threshold = 70", "only apply with correct_results"),
        ('result_skip_headers = ["Site=x"]', "only apply with correct_results"),
    ],
)
def test_invalid_manifest_values_are_rejected_before_anything_is_written(tmp_path, analyzed, extra, message):  # noqa: F811
    with pytest.raises(WorkspaceConfigError, match=message):
        Workspace.from_toml(manifest_for(tmp_path, analyzed, extra)).build(tmp_path / "site")
    assert not (tmp_path / "site").exists()


def test_profiles_default_to_no_correction():
    profile = CollectionProfile("a", "A", ())
    assert (profile.correct_results, profile.result_threshold, profile.result_skip_headers) == (None, None, ())


@pytest.mark.parametrize("key", ["result_skip_header", "correct_result", "result_policy", "correct_results_policy"])
def test_a_misspelled_correction_key_is_rejected_before_anything_is_written(tmp_path, analyzed, key):  # noqa: F811
    config = manifest_for(tmp_path, analyzed, f'correct_results = "all"\n{key} = ["Site=x"]')
    message = f"unknown collection key '{key}'.*correct_results, result_threshold"
    with pytest.raises(WorkspaceConfigError, match=message):
        Workspace.from_toml(config).build(tmp_path / "site")
    assert not (tmp_path / "site").exists()


def test_other_unknown_manifest_keys_are_still_ignored(tmp_path, analyzed):  # noqa: F811
    config = manifest_for(tmp_path, analyzed, 'colour = "red"\nresults = 3')  # F-13's rule
    assert Workspace.from_toml(config).build(tmp_path / "site").corrections == {}


def test_a_skip_that_raises_leaves_every_file_unchanged(analyzed):  # noqa: F811
    before = {p.name: p.read_bytes() for p in analyzed.glob("*.pgn")}
    calls = []

    def skip(game):
        calls.append(game.headers["Date"])
        if len(calls) == 4:
            raise RuntimeError("boom")
        return False

    with pytest.raises(RuntimeError, match="boom"):
        correct_results(analyzed, skip=skip)
    assert len(calls) == 4 and {p.name: p.read_bytes() for p in analyzed.glob("*.pgn")} == before
    assert not list(analyzed.glob("*.partial"))


def test_the_feature_is_exported_from_the_package_root():
    import pgn_postmortem

    names = ["POLICIES", "check_policy", "header_skip", "GameDecision", "CorrectionReport", "ResultChange",
             "correct_results", "correct_game", "decided_result"]  # fmt: skip
    for name in names:
        assert name in pgn_postmortem.__all__ and hasattr(pgn_postmortem, name), name
    assert all(hasattr(pgn_postmortem, name) for name in pgn_postmortem.__all__)
    assert len(set(pgn_postmortem.__all__)) == len(pgn_postmortem.__all__)
