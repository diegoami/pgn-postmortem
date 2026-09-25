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
  tests/golden/site/              the site built from them, byte for byte, with
                                  the reading history (the default). After an
                                  intended change to the pages, regenerate it
                                  with the command in REGENERATE. The same site
                                  without the history is in
                                  tests/golden/site-no-history/ (test_history.py).
  tests/fixtures/site/odd.pgn     three unanalyzed games with awkward headers:
                                  <, >, & and quotes in the names, event, site
                                  and more; a Date whose year starts with a
                                  superscript digit (²019); a three-digit month
                                  (2019.123.05)
"""

import shutil
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from pgn_postmortem import Collection, critical_moments
from pgn_postmortem.cli import main
from pgn_postmortem.collection import file_stem
from pgn_postmortem.site import build_site, move_label

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"
SITE_GAMES = FIXTURES / "site" / "games.pgn"
ODD = FIXTURES / "site" / "odd.pgn"
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


LICHESS = "https://lichess.org/analysis/"  # a position: LICHESS + the FEN with its spaces as "_"
LICHESS_GAME = LICHESS + "pgn/"  # a whole game: LICHESS_GAME + its moves, URL-encoded
NEW_TAB = {"target": "_blank", "rel": "noopener noreferrer"}


@dataclass(frozen=True)
class Checked:
    """The links ``check_links`` checked: the relative ones, and the lichess
    game and position links (ROADMAP.md, F-10)."""

    relative: int = 0
    games: int = 0
    positions: int = 0

    @property
    def total(self) -> int:
        return self.relative + self.games + self.positions


def inside(element: Element, tag: str, cls: str) -> bool:
    """Whether ``element`` is inside an element ``<tag class="cls">``."""
    parent = element.parent
    while parent is not None:
        if parent.tag == tag and cls in (parent.attrs.get("class") or "").split():
            return True
        parent = parent.parent
    return False


def lichess_kind(element: Element, key: str, link: str) -> str | None:
    """``games`` or ``positions`` for an absolute link that the pages may
    carry, else None: an ``<a href>`` to ``LICHESS_GAME`` inside an article's
    infobox, or to ``LICHESS`` (not ``pgn/``) inside a critical moment's answer,
    with something after the prefix and no query or fragment."""
    if element.tag != "a" or key != "href" or "?" in link or "#" in link:
        return None
    if link.startswith(LICHESS_GAME):
        where, rest = ("table", "infobox"), link[len(LICHESS_GAME) :]
        kind = "games"
    elif link.startswith(LICHESS):
        where, rest = ("details", "answer"), link[len(LICHESS) :]
        kind = "positions"
    else:
        return None
    return kind if rest and inside(element, *where) else None


def check_links(site: Path) -> Checked:
    """Every href and src in every page is relative, names a file in the
    site, and any #fragment is an id in that file; except the lichess links
    (ROADMAP.md, F-10), which are absolute, of one of the two forms
    ``lichess_kind`` accepts, each in its place, and open in a new tab with
    ``rel="noopener noreferrer"``. ``target`` appears on no other element.
    Returns the links checked."""
    site = site.resolve()
    pages = {path: parse(path) for path in site.rglob("*.html")}
    ids = {path: {e.attrs["id"] for e in dom.iter() if e.attrs.get("id")} for path, dom in pages.items()}
    counts = {"relative": 0, "games": 0, "positions": 0}
    for path, dom in pages.items():
        for element in dom.iter():
            lichess = None
            for key in ("href", "src"):
                link = element.attrs.get(key)
                if link is None:
                    continue
                parts = urlsplit(link)
                where = f"{path.relative_to(site)}: {key}={link!r}"
                if parts.scheme or parts.netloc or link.startswith("/"):
                    lichess = lichess_kind(element, key, link)
                    assert lichess, f"not relative, and not a lichess link in its place: {where}"
                    for name, value in NEW_TAB.items():
                        assert element.attrs.get(name) == value, f"no {name}={value!r}: {where}"
                    counts[lichess] += 1
                    continue
                target = (path.parent / parts.path).resolve() if parts.path else path
                assert target.is_file(), f"broken: {where}"
                assert site in target.parents, f"outside the site: {where}"
                if parts.fragment:
                    assert parts.fragment in ids[target], f"no such anchor: {where}"
                counts["relative"] += 1
            if "target" in element.attrs:
                assert lichess, f"{path.relative_to(site)}: target on <{element.tag} {element.attrs}>"
    return Checked(**counts)


# --- the check fails what it must (ROADMAP.md, F-10) ---------------------------------------


@pytest.fixture(scope="module")
def analyzed_site(tmp_path_factory) -> Path:
    """The fixture site, as the command line builds it."""
    site = tmp_path_factory.mktemp("analyzed")
    build([ANALYZED], site, *PLAYER)
    return site


GOOD = 'target="_blank" rel="noopener noreferrer"'
POSITION = LICHESS + "3r2k1/5pp1/7p/8/8/8/R4PPP/6K1_w_-_-_0_31"
# An absolute link, or a target, that the check must fail: (where it is put, the markup).
BAD = {
    "another site": ("lead", f'<a href="https://example.org/" {GOOD}>x</a>'),
    "http, not https": ("infobox", f'<a href="http://lichess.org/analysis/pgn/e4" {GOOD}>x</a>'),
    "protocol-relative": ("infobox", f'<a href="//lichess.org/analysis/pgn/e4" {GOOD}>x</a>'),
    "root-relative": ("infobox", f'<a href="/analysis/pgn/e4" {GOOD}>x</a>'),
    "another lichess page": ("answer", f'<a href="https://lichess.org/study/abc" {GOOD}>x</a>'),
    "lichess without analysis": ("infobox", f'<a href="https://lichess.org/pgn/e4" {GOOD}>x</a>'),
    "a game link in an answer": ("answer", f'<a href="{LICHESS_GAME}e4" {GOOD}>x</a>'),
    "a game link in the lead": ("lead", f'<a href="{LICHESS_GAME}e4" {GOOD}>x</a>'),
    "a position link in the infobox": ("infobox", f'<a href="{POSITION}" {GOOD}>x</a>'),
    "a position link in the lead": ("lead", f'<a href="{POSITION}" {GOOD}>x</a>'),
    "a game link with a query": ("infobox", f'<a href="{LICHESS_GAME}e4?color=black" {GOOD}>x</a>'),
    "a position link with a fragment": ("answer", f'<a href="{POSITION}#x" {GOOD}>x</a>'),
    "an empty game link": ("infobox", f'<a href="{LICHESS_GAME}" {GOOD}>x</a>'),
    "an empty position link": ("answer", f'<a href="{LICHESS}" {GOOD}>x</a>'),
    "no target": ("infobox", f'<a href="{LICHESS_GAME}e4" rel="noopener noreferrer">x</a>'),
    "another target": ("infobox", f'<a href="{LICHESS_GAME}e4" target="lichess" rel="noopener noreferrer">x</a>'),
    "no noreferrer": ("answer", f'<a href="{POSITION}" target="_blank" rel="noopener">x</a>'),
    "an image": ("infobox", f'<img src="{LICHESS_GAME}e4" {GOOD}>'),
    "a stylesheet": ("head", f'<link rel="stylesheet" href="{LICHESS}style.css">'),
    "a target on a relative link": ("lead", '<a href="../index.html" target="_blank">x</a>'),
}
PLACES = {  # the text each markup goes next to, and how
    "lead": ('<p class="lead">', '<p class="lead">{}'),
    "infobox": ("</table>", "{}</table>"),
    "answer": ("</details>", "{}</details>"),
    "head": ("</head>", "{}</head>"),
}


def plant(site: Path, tmp_path: Path, place: str, markup: str) -> Path:
    """A copy of ``site`` with ``markup`` put into one article with a critical
    moment: in its lead, its infobox, its answer or its head."""
    copy = tmp_path / "site"
    shutil.copytree(site, copy)
    page = copy / "games" / "2020-06-01-9705c13f05.html"
    text = page.read_text(encoding="utf-8")
    anchor, planted = PLACES[place]
    assert text.count(anchor) == 1
    text = text.replace(anchor, planted.format(markup))
    page.write_text(text, encoding="utf-8")
    return copy


@pytest.mark.parametrize(("place", "markup"), BAD.values(), ids=BAD.keys())
def test_the_check_fails_any_other_absolute_link_or_target(analyzed_site, tmp_path, place, markup):
    check_links(analyzed_site)  # the site as built passes
    with pytest.raises(AssertionError):
        check_links(plant(analyzed_site, tmp_path, place, markup))


@pytest.mark.parametrize(
    ("place", "markup", "kind"),
    [
        ("infobox", f'<a href="{LICHESS_GAME}e4" {GOOD}>x</a>', "games"),
        ("answer", f'<a href="{POSITION}" {GOOD}>x</a>', "positions"),
    ],
    ids=["game", "position"],
)
def test_a_planted_lichess_link_of_the_right_form_in_its_place_passes(analyzed_site, tmp_path, place, markup, kind):
    before = check_links(analyzed_site)
    after = check_links(plant(analyzed_site, tmp_path, place, markup))
    assert getattr(after, kind) == getattr(before, kind) + 1


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
    assert check_links(tmp_path).total > len(expected) * 3


def test_a_stale_page_the_builder_wrote_is_removed_whatever_its_name(tmp_path):
    collection = Collection.read(ODD)
    collection.build_site(tmp_path)
    odd = [path.name for path in (tmp_path / "games").iterdir() if path.name.startswith("2019-123-05-")]
    assert len(odd) == 1  # the three-digit month stays in the name, as file_stem writes it
    kept = [item for item in collection if item.game.headers["Date"] != "2019.123.05"]
    build_site(kept, tmp_path)  # that game has left the collection
    assert sorted(path.name for path in (tmp_path / "games").iterdir()) == sorted(
        f"{file_stem(item.game, item.id)}.html" for item in kept
    )


def test_a_file_the_builder_did_not_write_is_never_removed(tmp_path):
    (tmp_path / "games").mkdir()
    foreign = tmp_path / "games" / "2000-01-01-0123456789.html"  # named like an article, but not ours
    foreign.write_text("<!DOCTYPE html>\n<title>My own notes</title>\n", encoding="utf-8")
    notes = tmp_path / "games" / "notes.html"
    notes.write_text("not an article", encoding="utf-8")
    build([ANALYZED], tmp_path, *PLAYER)
    assert foreign.exists()
    assert notes.exists()


# --- awkward headers ------------------------------------------------------------------

TAGS = {
    "html", "head", "meta", "title", "link", "body", "header", "main", "footer", "article", "nav", "section",
    "h1", "h2", "p", "b", "i", "span", "a", "ol", "li", "pre", "table", "caption", "tr", "th", "td", "div",
    "figure", "figcaption", "details", "summary", "script", "button",  # the reading history's (F-8)
}  # fmt: skip
ATTRIBUTES = {
    "lang", "charset", "name", "content", "rel", "href", "class", "id", "role", "aria-label", "colspan",
    "data-r", "data-f", "hidden", "type", "data-site", "data-game", "data-move", "data-moves",  # F-8
    "target",  # the lichess links' only (F-10), which check_links asserts
}  # fmt: skip


def test_names_with_markup_characters_are_escaped(tmp_path):
    build([ODD], tmp_path, "--title", 'Ada\'s <games> & "notes"')
    headers = next(item for item in Collection.read(ODD) if item.game.headers["Date"] == "2022.02.02").game.headers
    article = tmp_path / "games" / f"2022-02-02-{headers['PostmortemId']}.html"
    for path in [tmp_path / "index.html", *(tmp_path / "games").iterdir()]:
        dom = parse(path)  # well-formed: every element closed, in order
        # nothing in a header became an element or an attribute
        assert {e.tag for e in dom.iter()} - {"#document"} <= TAGS, path.name
        assert {name for e in dom.iter() for name in e.attrs} <= ATTRIBUTES, path.name
        text = path.read_text(encoding="utf-8")
        for raw in ("<GM>", "<Open>", "<Pub>", "<2400>", "<draw>", "<games>", "<i>Italian", "1 & 2", "Smith & "):
            assert raw not in text, f"{path.name}: {raw!r} is not escaped"
    assert check_links(tmp_path).games == 3  # the target attribute is allowed on the lichess links only

    dom = parse(article)
    assert dom.find_all("h1")[0].text() == 'Alberic <GM> O\'Kelly vs. Smith & "Jones" <b>, 2022'
    infobox = {row.find_all("th")[0].text(): row.find_all("td")[0].text() for row in dom.find_all("tr")[1:]}
    assert infobox["Event"] == headers["Event"] == 'Club <Open> & "Rapid"'
    assert infobox["Site"] == "O'Brien's <Pub> & Grill"
    assert infobox["Round"] == "1 & 2"
    assert infobox["White"] == "Alberic <GM> O'Kelly (<2400>)"
    assert infobox["Opening"] == "<i>Italian</i> & 'more'"
    assert infobox["Termination"] == 'agreed <draw> & "shook hands"'
    assert "Alberic &lt;GM&gt; O'Kelly" in article.read_text(encoding="utf-8")
    assert parse(tmp_path / "index.html").find_all("h1")[0].text() == 'Ada\'s <games> & "notes"'


# --- odd dates ---------------------------------------------------------------------


def test_a_malformed_date_still_gets_an_article_filed_as_undated(tmp_path):
    collection = Collection.read(ODD)
    report = collection.build_site(tmp_path)
    assert len(report.articles) == len(collection) == 3
    superscript = next(item for item in collection if item.game.headers["Date"] == "²019.01.01")
    # file_stem's convention for a date with no year: undated-<id>; "²019" is not a year of ASCII digits
    name = f"undated-{superscript.id}.html"
    assert (tmp_path / "games" / name).is_file()
    index = parse(tmp_path / "index.html")
    (undated,) = [s for s in index.find_all("section") if s.attrs.get("id") == "undated"]
    assert [a.attrs["href"] for a in undated.find_all("a")] == [f"games/{name}"]
    assert "its date is not recorded" in parse(tmp_path / "games" / name).find_all("p", "lead")[0].text()
    # a month out of range is left out of the prose, the year kept
    long_month = next(item for item in collection if item.game.headers["Date"] == "2019.123.05")
    page = parse(tmp_path / "games" / f"{file_stem(long_month.game, long_month.id)}.html")
    assert "played on 2019," in page.find_all("p", "lead")[0].text()
    assert check_links(tmp_path).total > 0


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


def test_keep_analysis_still_strips_a_source_that_the_library_did_not_analyze():
    annotated = COLLECTION / "club" / "2019.pgn"  # Fritz-era comments, a source [%eval], a variation, NAGs
    collection = Collection.read(annotated, keep_analysis=True)
    nodes = [node for item in collection for node in (item.game, *item.game.mainline())]
    assert nodes and not any(node.comment or node.nags or len(node.variations) > 1 for node in nodes)
    assert not any(item.game.headers.get("Annotator") for item in collection)


def test_without_keep_analysis_the_analysis_is_stripped():
    collection = Collection.read(ANALYZED)
    assert all("PostmortemAnalysis" not in item.game.headers for item in collection)
    assert all(not critical_moments(item.game) for item in collection)
