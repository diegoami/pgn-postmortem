"""The separate F-1.3 Capablanca book demo, without Stockfish."""

from pathlib import Path

from pgn_postmortem import Collection
from pgn_postmortem.collection import ANALYSIS_HEADER
from pgn_postmortem.selection import SelectionOptions, select_chapters
from pgn_postmortem.site import build_site, make_articles
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
    articles = make_articles(games)
    chapters = select_chapters(articles, {PLAYER.casefold()}, SelectionOptions(chapter_size=1))
    selected = [article.item.id for entries in chapters.values() for article, _ in entries]
    assert all(len(entries) <= 1 for entries in chapters.values())
    assert len(selected) == len(set(selected))
    assert not any(select_chapters(articles, {PLAYER.casefold()}, SelectionOptions(minimum_length=100)).values())
    report = build_site(games, tmp_path, title="Jose Raul Capablanca")
    assert report.articles and report.quiz == tmp_path / "quiz.html"
    assert (tmp_path / "career.html").is_file()
    assert all((tmp_path / "chapters" / f"best-{chapter}.html").is_file() for chapter in ("wins", "losses", "draws"))
    career = (tmp_path / "career.html").read_text(encoding="utf-8")
    assert "Notable games" in career and "selection score" in career
    assert all(
        "../games/" in (tmp_path / "chapters" / f"best-{chapter}.html").read_text(encoding="utf-8")
        for chapter in ("wins", "losses", "draws")
    )
    for chapter in ("wins", "losses", "draws"):
        chapter_text = (tmp_path / "chapters" / f"best-{chapter}.html").read_text(encoding="utf-8")
        game_link = chapter_text.split('href="../', 1)[1].split('"', 1)[0]
        assert f'href="{game_link}"' in career
    assert check_links(tmp_path).total > 0


def test_unanalyzed_rebuild_removes_generated_chapters_but_keeps_authored_page(tmp_path):
    analyzed = Collection.read(ANALYZED, player=PLAYER, keep_analysis=True)
    build_site(analyzed, tmp_path, title="Jose Raul Capablanca")
    authored = tmp_path / "chapters" / "best-losses.html"
    authored.write_text("author page", encoding="utf-8")
    source = Collection.read(SOURCE, player=PLAYER)
    build_site(source, tmp_path, title="Jose Raul Capablanca")
    assert not (tmp_path / "chapters" / "best-wins.html").exists()
    assert not (tmp_path / "chapters" / "best-draws.html").exists()
    assert authored.read_text(encoding="utf-8") == "author page"


def test_index_links_only_to_available_chapters(tmp_path):
    collection = Collection.read(ANALYZED, player=PLAYER, keep_analysis=True)
    win = next(item for item in collection if item.game.headers["Result"] == "1-0")
    build_site([win], tmp_path, player=PLAYER, title="Jose Raul Capablanca")
    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "chapters/best-wins.html" in index
    assert "chapters/best-losses.html" not in index
    assert "chapters/best-draws.html" not in index
