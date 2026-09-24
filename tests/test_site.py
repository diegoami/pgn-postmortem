"""The static site (pgn_postmortem.site), built from committed fixtures, so
no test here runs Stockfish.

  tests/fixtures/site/games.pgn   six of Ada Example's games (as "Ada Example",
                                  "AdaEx" and "Example, Ada"), 2019 to 2021 and
                                  one undated; four have a critical moment,
                                  one of them by White, one also an inaccuracy
  tests/fixtures/site/analyzed/   the same games as the library's analysis
                                  wrote them, once, with Stockfish 16:
      .venv/bin/python -m pgn_postmortem analyze tests/fixtures/site/games.pgn \\
          --out tests/fixtures/site/analyzed --depth 12 --workers 1
  tests/golden/site/              the site built from them, byte for byte.
                                  After an intended change to the pages,
                                  regenerate it with the command in REGENERATE.
"""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from pgn_postmortem import Collection, critical_moments
from pgn_postmortem.cli import main
from pgn_postmortem.collection import file_stem
from pgn_postmortem.site import move_label

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"
SITE_GAMES = FIXTURES / "site" / "games.pgn"
ANALYZED = FIXTURES / "site" / "analyzed"
COLLECTION = FIXTURES / "collection"
GOLDEN = REPO_ROOT / "tests" / "golden" / "site"
PLAYER = ["--player", "Ada Example", "--alias", "adaex", "--alias", "Example, Ada"]

# Run from the repository root; it rewrites tests/golden/site/ in place.
REGENERATE = (
    ".venv/bin/python -m pgn_postmortem site tests/fixtures/site/analyzed "
    '--player "Ada Example" --alias adaex --alias "Example, Ada" --out tests/golden/site'
)

# The critical moments of the analyzed fixture, worked out by hand from its [%eval]
# comments: the moves that cost their side at least 20 points of winning chances.
EXPECTED_MOMENTS = {
    "2019-03-14-bf58e2afa0": [],
    "2019-04-02-5d1415e1ac": [],
    "2020-06-01-9705c13f05": ["3... Nf6"],  # 53% -> 0%, allows 4. Qxf7#
    "2021-09-10-a9c90416b2": ["5... Bxd1"],  # 33% -> 0%, allows mate in 2
    "2021-12-24-9137b96576": ["5. Nxf7"],  # 43% -> 15%, White's mistake; 4. Nxe5 (-15) only an inaccuracy
    "undated-5ce208cdcb": ["2... Ke7"],  # allows 3. Qxe5#
}


def build(inputs, out: Path, *extra: str) -> None:
    """The site as the command line builds it."""
    assert main(["site", *map(str, inputs), *extra, "--out", str(out)]) == 0


def files(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


# --- a small DOM, enough to check structure -----------------------------------

VOID = {"meta", "link", "br", "img", "input", "hr"}


class Element:
    def __init__(self, tag: str, attrs: dict[str, str | None], parent: "Element | None"):
        self.tag, self.attrs, self.parent = tag, attrs, parent
        self.children: list[Element | str] = []

    def text(self, skip: str | None = None) -> str:
        """The text inside, leaving out the elements with the tag ``skip``."""
        return "".join(
            c if isinstance(c, str) else c.text(skip)
            for c in self.children
            if not (isinstance(c, Element) and c.tag == skip)
        )

    def iter(self):
        yield self
        for child in self.children:
            if isinstance(child, Element):
                yield from child.iter()

    def find_all(self, tag: str, cls: str | None = None) -> list["Element"]:
        return [
            e for e in self.iter() if e.tag == tag and (cls is None or cls in (e.attrs.get("class") or "").split())
        ]


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element("#document", {}, None)
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        element = Element(tag, dict(attrs), self.current)
        self.current.children.append(element)
        if tag not in VOID:
            self.current = element

    def handle_endtag(self, tag):
        assert self.current.tag == tag, f"</{tag}> closes <{self.current.tag}>"
        self.current = self.current.parent

    def handle_data(self, data):
        self.current.children.append(data)


def parse(path: Path) -> Element:
    builder = TreeBuilder()
    builder.feed(path.read_text(encoding="utf-8"))
    builder.close()
    assert builder.current is builder.root, f"{path.name}: <{builder.current.tag}> is never closed"
    return builder.root


# --- the golden files -----------------------------------------------------------


def test_the_fixture_site_renders_to_the_golden_pages_byte_for_byte(tmp_path):
    build([ANALYZED], tmp_path, *PLAYER)
    built, golden = files(tmp_path), files(GOLDEN)
    hint = f"if the change to the pages is intended, regenerate the golden files: {REGENERATE}"
    assert sorted(built) == sorted(golden), hint
    for name in built:
        assert built[name] == golden[name], f"{name} differs; {hint}"


def test_building_twice_into_the_same_directory_changes_nothing(tmp_path):
    build([ANALYZED], tmp_path, *PLAYER)
    first = files(tmp_path)
    build([ANALYZED], tmp_path, *PLAYER)
    assert files(tmp_path) == first


# --- one article per game, no broken links ----------------------------------------


def check_links(site: Path) -> int:
    """Every href and src in every page is relative, names a file in the
    site, and any #fragment is an id in that file. Returns the links checked."""
    site = site.resolve()
    pages = {path: parse(path) for path in site.rglob("*.html")}
    ids = {path: {e.attrs["id"] for e in dom.iter() if e.attrs.get("id")} for path, dom in pages.items()}
    checked = 0
    for path, dom in pages.items():
        for element in dom.iter():
            for key in ("href", "src"):
                link = element.attrs.get(key)
                if link is None:
                    continue
                parts = urlsplit(link)
                where = f"{path.relative_to(site)}: {key}={link!r}"
                assert not parts.scheme and not parts.netloc and not link.startswith("/"), f"not relative: {where}"
                target = (path.parent / parts.path).resolve() if parts.path else path
                assert target.is_file(), f"broken: {where}"
                assert site in target.parents, f"outside the site: {where}"
                if parts.fragment:
                    assert parts.fragment in ids[target], f"no such anchor: {where}"
                checked += 1
    return checked


@pytest.mark.parametrize(
    ("inputs", "games"),
    [([ANALYZED], 6), ([SITE_GAMES], 6), ([COLLECTION], 3)],
    ids=["analyzed", "not-analyzed", "collection"],
)
def test_the_site_has_one_article_per_game_and_no_broken_links(tmp_path, inputs, games):
    collection = Collection.read(inputs, player="Ada Example", aliases=["adaex", "Example, Ada"])
    assert len(collection) == games
    expected = {f"{file_stem(item.game, item.id)}.html" for item in collection}
    build(inputs, tmp_path, *PLAYER)

    assert {path.name for path in (tmp_path / "games").iterdir()} == expected
    index = parse(tmp_path / "index.html")
    linked = [a.attrs["href"] for a in index.find_all("a") if a.attrs["href"].startswith("games/")]
    assert sorted(linked) == sorted(f"games/{name}" for name in expected)  # each game listed exactly once
    for name in expected:
        assert len(parse(tmp_path / "games" / name).find_all("article")) == 1
    assert check_links(tmp_path) > len(expected) * 3


def test_an_earlier_build_leaves_no_stale_article(tmp_path):
    (tmp_path / "games").mkdir()
    stale = tmp_path / "games" / "2000-01-01-0123456789.html"
    stale.write_text("an article of a game no longer in the collection", encoding="utf-8")
    mine = tmp_path / "games" / "notes.html"
    mine.write_text("not an article", encoding="utf-8")
    build([ANALYZED], tmp_path, *PLAYER)
    assert not stale.exists()
    assert mine.exists()  # only files named like articles are removed


# --- the revision mode --------------------------------------------------------------


def test_the_critical_moments_of_the_fixture_are_the_expected_ones():
    collection = Collection.read(ANALYZED, keep_analysis=True)
    found = {
        file_stem(item.game, item.id): [move_label(r.board_before, r.node.move) for r in critical_moments(item.game)]
        for item in collection
    }
    assert found == EXPECTED_MOMENTS


def test_every_critical_moment_has_its_question_and_a_hidden_answer(tmp_path):
    build([ANALYZED], tmp_path, *PLAYER)
    total = 0
    for stem, moves in EXPECTED_MOMENTS.items():
        dom = parse(tmp_path / "games" / f"{stem}.html")
        moments = dom.find_all("div", "moment")
        assert [m.attrs["id"] for m in moments] == [f"moment-{i}" for i in range(1, len(moves) + 1)], stem
        for moment, move in zip(moments, moves, strict=True):
            (figure,) = moment.find_all("figure")
            assert figure.find_all("div", "board"), f"{stem}: no diagram"
            assert "What would you play?" in figure.find_all("figcaption")[0].text()
            (details,) = moment.find_all("details")
            assert "open" not in details.attrs, f"{stem}: the answer is not hidden"
            summary = next(c for c in details.children if isinstance(c, Element))
            assert summary.tag == "summary" and summary.text() == "Show the answer"
            answer = details.text()[len(summary.text()) :]
            assert "Best was" in answer and f"played {move}" in answer, f"{stem}: {answer!r}"
            # the engine's move is only in the answer, never in the page around it
            best = answer.split("Best was ", 1)[1].split(",", 1)[0]
            assert best not in dom.text(skip="details"), f"{stem}: {best} is shown outside the answer"
            total += 1
        # no question anywhere else in the page
        assert len(dom.find_all("details")) == len(moves), stem
    assert total == sum(len(moves) for moves in EXPECTED_MOMENTS.values()) == 4


# --- games not analyzed ---------------------------------------------------------------


@pytest.mark.parametrize("inputs", [[SITE_GAMES], [COLLECTION]], ids=["site-games", "collection"])
def test_games_without_analysis_get_articles_with_no_critical_moments(tmp_path, inputs):
    # tests/fixtures/collection/club/2019.pgn carries a source [%eval]: it must not count as analysis
    assert "[%eval" in (COLLECTION / "club" / "2019.pgn").read_text(encoding="utf-8")
    collection = Collection.read(inputs, player="Ada Example", aliases=["adaex", "Example, Ada"], keep_analysis=True)
    assert all(not critical_moments(item.game) for item in collection)

    build(inputs, tmp_path, *PLAYER)
    articles = sorted((tmp_path / "games").iterdir())
    assert len(articles) == len(collection) > 0
    for path in articles:
        dom = parse(path)
        assert not dom.find_all("div", "moment"), path.name
        assert not dom.find_all("details"), path.name
        assert not dom.find_all("span", "note"), path.name
        assert "It has not been analyzed yet" in dom.find_all("p", "lead")[0].text(), path.name
    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert index.count("not analyzed") == len(collection)


# --- reading games with their analysis -------------------------------------------------


@pytest.mark.parametrize("order", ["games-first", "analyzed-first"])
def test_the_analyzed_copy_of_a_game_is_the_one_kept(order):
    inputs = [SITE_GAMES, ANALYZED] if order == "games-first" else [ANALYZED, SITE_GAMES]
    collection = Collection.read(inputs, keep_analysis=True)
    assert len(collection) == 6
    assert collection.report.duplicates == 6
    assert all("PostmortemAnalysis" in item.game.headers for item in collection)
    assert [file_stem(item.game, item.id) for item in collection] == [
        file_stem(item.game, item.id) for item in Collection.read(inputs[0])
    ]  # in the place of the first copy read


def test_without_keep_analysis_the_analysis_is_stripped():
    collection = Collection.read(ANALYZED)
    assert all("PostmortemAnalysis" not in item.game.headers for item in collection)
    assert all(not critical_moments(item.game) for item in collection)
