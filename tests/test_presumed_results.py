"""A result for games whose result was not recorded (ROADMAP.md, F-5), on the
hand-written fixtures in tests/fixtures/site/synthetic/ (their README says
what each game is and why). No test here runs Stockfish.

For a game whose Result is "*" (or missing), the site shows: the board's
result if the game ended in checkmate, stalemate or insufficient material;
else, for an analyzed game, a win for the side with at least the threshold's
winning chances (70% by default) in the final position, and a draw otherwise;
else wording that says the result was not recorded. The result is shown like
a recorded one everywhere outside the PGN section, and the PGN is untouched.
"""

import io
import re
from pathlib import Path

import chess.pgn
import pytest

from pgn_postmortem import Collection
from pgn_postmortem.collection import file_stem, game_id
from pgn_postmortem.site import build_site, shown_result
from tests.test_site import Element, parse

SYNTHETIC = Path(__file__).resolve().parent / "fixtures" / "site" / "synthetic"
SYMBOLS = {"1-0": "1–0", "0-1": "0–1", "1/2-1/2": "½–½"}

# file -> the result the site shows with the default threshold (None: not recorded),
# and how the conclusion's first sentence starts ({} is the result shown)
EXPECTED = {
    "white-73.pgn": ("1-0", "The game ended {} after 3... a6."),
    "white-27.pgn": ("0-1", "The game ended {} after 3... a6."),
    "white-34.pgn": ("1/2-1/2", "The game ended {} after 3... a6."),
    "white-66.pgn": ("1/2-1/2", "The game ended {} after 3... a6."),
    "white-59.pgn": ("1/2-1/2", "The game ended {} after 3... a6."),
    "checkmate.pgn": ("0-1", "Ada Example delivered checkmate with 2... Qh4#."),
    "stalemate.pgn": ("1/2-1/2", "The game ended in stalemate after 50. Qf7."),
    "insufficient-material.pgn": ("1/2-1/2", "The game ended after 60. Kxd2, with too little material left"),
    "stalemate-analyzed.pgn": ("1/2-1/2", "The game ended in stalemate after 50. Qf7."),
    "mate-white.pgn": ("1-0", "The game ended {} after 60... Kd6."),
    "mate-black.pgn": ("0-1", "The game ended {} after 61. Kd5."),
    "not-recorded.pgn": (None, "The score stops after 3... Nf6; the result was not recorded."),
    "no-result-header.pgn": (None, "The score stops after 2... Nf6; the result was not recorded."),
}


def read(name: str):
    (item,) = Collection.read(SYNTHETIC / name, keep_analysis=True)
    return item


def build(tmp_path: Path, **options) -> Path:
    build_site(Collection.read(SYNTHETIC, keep_analysis=True), tmp_path, **options)
    return tmp_path


@pytest.fixture(scope="module")
def site(tmp_path_factory) -> Path:
    """The site of every synthetic game, with the default threshold."""
    return build(tmp_path_factory.mktemp("site"))


def following(parent: Element, element: Element) -> Element:
    siblings = [c for c in parent.children if isinstance(c, Element)]
    return siblings[siblings.index(element) + 1]


def results_shown(site: Path, name: str) -> dict[str, str]:
    """Every place the site shows the result of the game in ``name``, as text."""
    item = read(name)
    stem = file_stem(item.game, item.id)
    dom = parse(site / "games" / f"{stem}.html")
    (article,) = dom.find_all("article")
    rows = {row.find_all("th")[0].text(): row.find_all("td")[0].text() for row in dom.find_all("tr")[1:]}
    (conclusion_heading,) = [h for h in article.find_all("h2") if h.attrs.get("id") == "conclusion"]
    index = parse(site / "index.html")
    (entry,) = [li for li in index.find_all("li") if li.find_all("a")[0].attrs["href"] == f"games/{stem}.html"]
    return {
        "infobox": rows["Result"],
        "lead": article.find_all("p", "lead")[0].text(),
        "moves": article.find_all("p", "moves")[-1].text(),
        "conclusion": following(article, conclusion_heading).text(),
        "index": entry.find_all("span", "result")[0].text(),
    }


def assert_shows(site: Path, name: str, result: str | None) -> None:
    """The game in ``name`` shows ``result`` (None: "not recorded") in the
    infobox, the lead, at the end of the moves, in the conclusion and in the index."""
    item = read(name)
    white, black = item.game.headers["White"], item.game.headers["Black"]
    shown = results_shown(site, name)
    if result is None:
        assert shown["infobox"] == "Not recorded", shown
        assert "Its result is not recorded" in shown["lead"], shown
        assert shown["moves"].endswith("(result not recorded)"), shown
        assert "the result was not recorded" in shown["conclusion"], shown
        assert shown["index"] == "result not recorded", shown
        return
    symbol = SYMBOLS[result]
    assert shown["infobox"] == symbol, shown
    if result == "1/2-1/2":
        assert "It was drawn" in shown["lead"], shown
    else:
        winner, colour = (white, "white") if result == "1-0" else (black, "black")
        assert f"{winner}, with the {colour} pieces, won" in shown["lead"], shown
    assert shown["moves"].endswith(f" {symbol}"), shown
    assert shown["index"] == symbol, shown
    # the conclusion names the result, or the board's reason for it
    assert shown["conclusion"].startswith(EXPECTED[name][1].format(symbol)), shown
    for other in set(SYMBOLS.values()) - {symbol}:
        assert other not in shown["conclusion"], shown


# --- 1, 2: presumed from the analysis ---------------------------------------------


@pytest.mark.parametrize(
    ("name", "result"),
    [("white-73.pgn", "1-0"), ("white-27.pgn", "0-1"), ("white-34.pgn", "1/2-1/2")],
)
def test_an_unrecorded_result_is_presumed_from_the_final_evaluation(site, name, result):
    assert_shows(site, name, result)


# --- 3, 4: the threshold ------------------------------------------------------------


def test_the_default_threshold_is_70_not_60(site, tmp_path):
    assert_shows(site, "white-66.pgn", "1/2-1/2")  # 66.5% for White: a draw at 70
    assert_shows(build(tmp_path, presume_threshold=60), "white-66.pgn", "1-0")  # and a win at 60


def test_the_threshold_parameter_is_used(tmp_path):
    assert_shows(build(tmp_path, presume_threshold=80), "white-73.pgn", "1/2-1/2")  # 73.4% for White


@pytest.mark.parametrize("threshold", [54.9, 95.1, 0, 50, 100, float("nan")])
def test_a_threshold_outside_55_to_95_is_rejected(tmp_path, threshold):
    with pytest.raises(ValueError, match="55"):
        build(tmp_path, presume_threshold=threshold)
    assert not (tmp_path / "index.html").exists()  # rejected before anything is written
    with pytest.raises(ValueError, match="55"):
        shown_result(read("white-73.pgn").game, threshold)


@pytest.mark.parametrize("threshold", [55, 95])
def test_the_bounds_of_the_threshold_are_accepted(tmp_path, threshold):
    build(tmp_path, presume_threshold=threshold)
    assert (tmp_path / "index.html").is_file()


def test_a_presumed_win_is_not_said_to_come_from_outside_the_position(tmp_path):
    # 59.1% for White: a win at 55, below the 60% where the conclusion calls a winner "clearly ahead"
    site = build(tmp_path, presume_threshold=55)
    assert_shows(site, "white-59.pgn", "1-0")
    conclusion = results_shown(site, "white-59.pgn")["conclusion"]
    assert "outside the position" not in conclusion
    assert "59% winning chances" in conclusion


# --- 6, 7: the board decides first; a mate score ----------------------------------------


@pytest.mark.parametrize(
    ("name", "result"),
    [
        ("checkmate.pgn", "0-1"),
        ("stalemate.pgn", "1/2-1/2"),
        ("insufficient-material.pgn", "1/2-1/2"),
        ("stalemate-analyzed.pgn", "1/2-1/2"),  # its (impossible) +5.00 does not outvote the board
    ],
)
def test_the_board_decides_an_unrecorded_result_first(site, name, result):
    assert_shows(site, name, result)


@pytest.mark.parametrize(("name", "result"), [("mate-white.pgn", "1-0"), ("mate-black.pgn", "0-1")])
def test_a_mate_score_gives_the_win_to_the_side_with_the_mate(site, name, result):
    assert not read(name).game.end().board().is_game_over()
    assert_shows(site, name, result)


# --- 8: not recorded -------------------------------------------------------------------


@pytest.mark.parametrize("name", ["not-recorded.pgn", "no-result-header.pgn"])
def test_a_result_that_cannot_be_presumed_reads_as_not_recorded(site, name):
    assert_shows(site, name, None)


def test_no_bare_star_appears_outside_the_pgn_section(site):
    assert "*" not in (site / "index.html").read_text(encoding="utf-8")
    pages = sorted((site / "games").iterdir())
    assert len(pages) == len(EXPECTED)
    for path in pages:
        text = path.read_text(encoding="utf-8")
        pgn = re.search(r'<pre class="pgn">.*?</pre>', text, re.DOTALL)[0]
        assert "*" in pgn, path.name  # the source's "*" is still there
        assert "*" not in text.replace(pgn, ""), path.name


# --- every case at once ------------------------------------------------------------


def test_the_expected_table_covers_every_fixture_and_matches_the_library():
    assert sorted(EXPECTED) == sorted(path.name for path in SYNTHETIC.glob("*.pgn"))
    for name, (result, _) in EXPECTED.items():
        assert shown_result(read(name).game) == (result or "*"), name


# --- 9: the PGN and the game's identity are untouched ------------------------------------


def test_the_result_header_the_id_and_the_file_names_are_unchanged(tmp_path):
    collection = Collection.read(SYNTHETIC, keep_analysis=True)
    build_site(collection, tmp_path)
    for item in collection:
        name = Path(item.origin.split("#")[0]).name
        source = chess.pgn.read_game(io.StringIO((SYNTHETIC / name).read_text(encoding="utf-8")))
        assert source.headers.get("Result", "*") == "*", name
        assert item.game.headers["Result"] == "*", name  # building the site did not write the presumed result
        assert item.id == game_id(source), name  # the id is the source's, with "*" as its result
        if EXPECTED[name][0]:  # an id with the presumed result would differ
            source.headers["Result"] = EXPECTED[name][0]
            assert game_id(source) != item.id, name
        page = tmp_path / "games" / f"{file_stem(item.game, item.id)}.html"
        assert page.is_file(), name
        pgn = parse(page).find_all("pre", "pgn")[0].text()
        assert '[Result "*"]' in pgn, name
        assert f'[PostmortemId "{item.id}"]' in pgn, name
        assert pgn.rstrip().endswith(" *"), name
    assert sorted(path.name for path in (tmp_path / "games").iterdir()) == sorted(
        f"{file_stem(item.game, item.id)}.html" for item in collection
    )

