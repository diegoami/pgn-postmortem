"""The separate F-1.3 Capablanca book demo, without Stockfish."""

from pathlib import Path

from pgn_postmortem import Collection
from pgn_postmortem.collection import ANALYSIS_HEADER
from pgn_postmortem.site import build_site
from tests.test_site import check_links

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "examples" / "book_demo" / "source"
ANALYZED = REPO_ROOT / "examples" / "book_demo" / "analyzed"
PLAYER = "Capablanca, Jose Raul"
ANALYSIS = "Stockfish 19, depth 22"


def test_the_committed_book_demo_has_five_complete_analyses():
    games = Collection.read(ANALYZED, player=PLAYER, keep_analysis=True)
    assert len(games) == 5
    assert {item.game.headers[ANALYSIS_HEADER] for item in games} == {ANALYSIS}
    assert sorted(item.id for item in games) == sorted(item.id for item in Collection.read(SOURCE, player=PLAYER))


def test_the_book_demo_builds_the_career_and_three_chapters(tmp_path):
    games = Collection.read(ANALYZED, player=PLAYER, keep_analysis=True)
    report = build_site(games, tmp_path, title="Jose Raul Capablanca")
    assert report.articles and report.quiz == tmp_path / "quiz.html"
    assert (tmp_path / "career.html").is_file()
    assert all((tmp_path / "chapters" / f"best-{chapter}.html").is_file() for chapter in ("wins", "losses", "draws"))
    assert check_links(tmp_path).total > 0
