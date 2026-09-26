"""The Pages demo's input (ROADMAP.md, F-12): the committed analysis in
examples/site/analyzed/, from which .github/workflows/pages.yml builds the
library's site at the demo's root. No test here runs Stockfish.

  examples/daily_games/       the five public-domain classic games, the demo's
                              own games (also the Markdown pipeline's input)
  examples/site/analyzed/     the same games as the library's analysis wrote
                              them, once, with Stockfish 19 at depth 22:
      .venv/bin/python -m pgn_postmortem analyze examples/daily_games \\
          --depth 22 --out examples/site/analyzed

A broken demo input is caught here, before the merge, and not only by the
post-merge deploy. Each check is also run on a scratch copy broken the way it
must catch (a game removed, a marker stripped, the depth changed, the evals
stripped, a game replaced, a game added).
"""

import re
import shutil
from pathlib import Path

import pytest

from pgn_postmortem import Collection
from pgn_postmortem.collection import ANALYSIS_HEADER
from tests.test_site import ANALYZED, build, check_links, parse

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_GAMES = REPO_ROOT / "examples" / "daily_games"
DEMO_ANALYZED = REPO_ROOT / "examples" / "site" / "analyzed"
GAMES = 5
ANALYSIS = "Stockfish 19, depth 22"  # the analysis the committed command wrote (review 028-01, finding 1)

# The options of the workflow's command (.github/workflows/pages.yml): no --player, so no quiz page.
WORKFLOW_OPTIONS = ("--title", "pgn-postmortem demo — five classic games", "--site-key", "pgn-postmortem-demo")


def check_analyzed(analyzed: Path) -> None:
    """Exactly five games, each carrying the analysis step's marker, reading
    the engine and depth of the committed command, and an [%eval] after every
    move that does not end the game."""
    games = Collection.read(analyzed, keep_analysis=True)
    assert len(games) == GAMES, f"{len(games)} games in {analyzed}, not five"
    for item in games:
        headers = item.game.headers
        assert ANALYSIS_HEADER in headers, f"{item.origin}: no {ANALYSIS_HEADER} marker"
        assert headers[ANALYSIS_HEADER] == ANALYSIS, f"{item.origin}: {headers[ANALYSIS_HEADER]!r}, not {ANALYSIS!r}"
        for node in item.game.mainline():
            if not node.board().is_game_over():
                assert node.eval() is not None, f"{item.origin}: no [%eval] after {node.san()} (ply {node.ply()})"


def check_same_games(analyzed: Path) -> None:
    """The analysis is of the demo's own games: the same PostmortemIds."""
    analyzed_ids = sorted(item.id for item in Collection.read(analyzed, keep_analysis=True))
    demo_ids = sorted(item.id for item in Collection.read(DEMO_GAMES))
    assert analyzed_ids == demo_ids, f"PostmortemIds {analyzed_ids} are not the demo games' {demo_ids}"


def check_site(analyzed: Path, out: Path) -> None:
    """The site the workflow builds: five articles, each listed once in the
    index, at least one critical moment (a question) among them, and every
    link passing check_links."""
    build([analyzed], out, *WORKFLOW_OPTIONS)
    articles = sorted(path.name for path in (out / "games").iterdir())
    assert len(articles) == GAMES, f"{len(articles)} articles, not five: {articles}"
    index = parse(out / "index.html")
    linked = sorted(a.attrs["href"] for a in index.find_all("a") if a.attrs["href"].startswith("games/"))
    assert linked == [f"games/{name}" for name in articles], "the index does not list each article once"
    pages = [parse(out / "games" / name) for name in articles]
    moments = [e for page in pages for e in page.iter() if e.attrs.get("id", "").startswith("moment-")]
    assert moments, "no critical moment in the site"
    check_links(out)


def test_the_committed_analysis_is_five_analyzed_games():
    check_analyzed(DEMO_ANALYZED)


def test_the_committed_analysis_is_of_the_demo_games():
    assert len(list(DEMO_GAMES.glob("*.pgn"))) == GAMES
    check_same_games(DEMO_ANALYZED)


def test_the_demo_site_has_five_articles_and_no_broken_links(tmp_path):
    check_site(DEMO_ANALYZED, tmp_path)
    assert not (tmp_path / "quiz.html").exists()


# --- each check fails what it must --------------------------------------------------------


def remove_a_game(copy: Path) -> None:
    sorted(copy.glob("*.pgn"))[0].unlink()


def strip_a_marker(copy: Path) -> None:
    path = sorted(copy.glob("*.pgn"))[0]
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    kept = [line for line in lines if not line.startswith(f"[{ANALYSIS_HEADER} ")]
    assert len(kept) == len(lines) - 1
    path.write_text("".join(kept), encoding="utf-8")


def change_the_depth(copy: Path) -> None:
    path = sorted(copy.glob("*.pgn"))[0]
    text = path.read_text(encoding="utf-8")
    assert text.count(f'[{ANALYSIS_HEADER} "{ANALYSIS}"]') == 1
    path.write_text(text.replace("depth 22", "depth 12"), encoding="utf-8")


def strip_the_evals(copy: Path) -> None:
    """Every [%eval] comment removed from every game; the headers kept."""
    for path in copy.glob("*.pgn"):
        text, count = re.subn(r"\s*\{ \[%eval [^\]]*\] \}", "", path.read_text(encoding="utf-8"))
        assert count > 0 and "%eval" not in text
        path.write_text(text, encoding="utf-8")


def add_another_game(copy: Path) -> None:
    """One analyzed game that is not a demo game (from the site fixture)."""
    other = sorted(ANALYZED.glob("*.pgn"))[0]
    shutil.copy(other, copy / other.name)


def replace_a_game(copy: Path) -> None:
    remove_a_game(copy)
    add_another_game(copy)


BREAKS = {
    "a game removed": (remove_a_game, check_analyzed, "4 games"),
    "a marker stripped": (strip_a_marker, check_analyzed, f"no {ANALYSIS_HEADER} marker"),
    "the depth changed": (change_the_depth, check_analyzed, "'Stockfish 19, depth 12', not"),
    "the evals stripped": (strip_the_evals, check_analyzed, r"no \[%eval\] after"),
    "the evals stripped, the site": (strip_the_evals, check_site, "no critical moment in the site"),
    "a game replaced": (replace_a_game, check_same_games, "are not the demo games'"),
    "a game added": (add_another_game, check_site, "6 articles, not five"),
}


@pytest.mark.parametrize(("breaking", "check", "message"), BREAKS.values(), ids=BREAKS.keys())
def test_each_check_fails_on_a_broken_copy_of_the_analysis(tmp_path, breaking, check, message):
    copy = tmp_path / "analyzed"
    shutil.copytree(DEMO_ANALYZED, copy)
    args = (copy, tmp_path / "site") if check is check_site else (copy,)
    check(*args)  # the unbroken copy passes
    shutil.rmtree(tmp_path / "site", ignore_errors=True)
    breaking(copy)
    with pytest.raises(AssertionError, match=message):
        check(*args)
