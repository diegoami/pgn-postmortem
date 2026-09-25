"""Moves that changed the expected result (ROADMAP.md, F-6), on the
hand-written fixtures in tests/fixtures/site/swings/ (their README says what
each move is and why). No test here runs Stockfish.

Each analyzed position gets an expected outcome from White's winning chances
after the move: White winning at 65% or more, Black winning at 35% or less,
level in between. A move is an outcome swing when it makes the expected
outcome worse for its side, costs that side at least the inaccuracy threshold
(10 points by default), and the engine's first choice before it (the first
move of any engine line stored there) differs from the move played. A swing
becomes a critical moment, and its note says how the expected result changed.
"""

import io
import math
from pathlib import Path

import chess
import chess.pgn
import pytest

from pgn_postmortem import Collection, Thresholds, build_site, critical_moments
from pgn_postmortem.analysis import win_percent
from pgn_postmortem.collection import file_stem
from pgn_postmortem.site import move_label, review_moves
from tests.test_site import ANALYZED, Element, parse

SWINGS = Path(__file__).resolve().parent / "fixtures" / "site" / "swings"
NBSP = "\u00a0"


def plain(text: str) -> str:
    return text.replace(NBSP, " ")


def read(name: str):
    (item,) = Collection.read(SWINGS / name, keep_analysis=True)
    return item


def moments(name: str, **options) -> list[str]:
    """The critical moments of the game in ``name``, as ``7. Re1``."""
    return [plain(move_label(r.board_before, r.node.move)) for r in critical_moments(read(name).game, **options)]


def band(white: float) -> str:
    """The expected outcome at the default 35/65 bands, from White's chances."""
    return "White winning" if white >= 65 else "Black winning" if white <= 35 else "level"


def facts(name: str, label: str) -> tuple[float, float, float, set[chess.Move], chess.Move]:
    """Read straight from the fixture, not through the library: White's chances
    before and after the move ``label``, what it cost its side, the first moves
    of the engine lines stored before it, and the move played."""
    game = read(name).game
    for node in game.mainline():
        if plain(move_label(node.parent.board(), node.move)) == label:
            before = win_percent(node.parent.eval().white().score())
            after = win_percent(node.eval().white().score())
            cost = before - after if node.turn() == chess.BLACK else after - before
            return before, after, cost, {v.move for v in node.parent.variations[1:]}, node.move
    raise AssertionError(f"{label} is not in {name}")


def build(tmp_path: Path, source: Path = SWINGS, **options) -> Path:
    build_site(Collection.read(source, keep_analysis=True), tmp_path, **options)
    return tmp_path


@pytest.fixture(scope="module")
def site(tmp_path_factory) -> Path:
    """The site of every swing fixture, with the default bands."""
    return build(tmp_path_factory.mktemp("site"))


def lazy_site(request: pytest.FixtureRequest) -> Path:
    """The ``site`` fixture, built only when a test asks for it: a test that
    checks a move is not a moment checks the rule first, so that a broken rule
    fails on that assertion, not on building a page for an ungraded move."""
    return request.getfixturevalue("site")


def page(site: Path, name: str) -> Element:
    item = read(name)
    return parse(site / "games" / f"{file_stem(item.game, item.id)}.html")


def notes(dom: Element) -> dict[str, list[str]]:
    """Each graded move as the moves section shows it (``7. Re1?!``, or ``Bg4?!``
    after a White move in the same run of moves), and its notes."""
    found: dict[str, list[str]] = {}
    for paragraph in dom.find_all("p", "moves"):
        children = [c for c in paragraph.children if isinstance(c, Element)]
        for bold, note in zip(children, children[1:], strict=False):
            if bold.tag == "b" and note.tag == "span" and "note" in note.attrs.get("class", ""):
                found.setdefault(plain(bold.text()), []).append(plain(note.text())[1:-1])  # without ( )
    return found


def answer_of(moment: Element) -> str:
    (details,) = moment.find_all("details")
    assert "open" not in details.attrs, "the answer is not hidden"
    summary = next(c for c in details.children if isinstance(c, Element))
    assert summary.tag == "summary" and summary.text() == "Show the answer"
    return plain(details.text()[len(summary.text()) :])


# --- 1: swings of 10-20 points become critical moments ------------------------------------


def test_a_white_and_a_black_swing_of_10_to_20_points_become_critical_moments(site):
    # the fixture: level -> Black winning by White, Black winning -> level by Black, each 10-20
    # points, each with its own better line (a different first choice) stored before it
    before, after, cost, firsts, played = facts("two-swings.pgn", "7. Re1")
    assert (band(before), band(after)) == ("level", "Black winning") and 10 <= cost < 20
    assert firsts and played not in firsts
    before, after, cost, firsts, played = facts("two-swings.pgn", "8... Nh5")
    assert (band(before), band(after)) == ("Black winning", "level") and 10 <= cost < 20
    assert firsts and played not in firsts

    assert moments("two-swings.pgn") == ["7. Re1", "8... Nh5"]
    dom = page(site, "two-swings.pgn")
    divs = dom.find_all("div", "moment")
    assert [d.attrs["id"] for d in divs] == ["moment-1", "moment-2"]
    expected = [
        ("7. Re1?!", "Best was 7. Bb3", "The refutation: 7... Ng4 8. Re2 Qf6", "a level game into a losing one"),
        ("8... Nh5?!", "Best was 8... Ba7", "The refutation: 9. Nxe5 dxe5 10. Qxh5", "a winning game into a level one"),
    ]
    for div, (move, best, refutation, change) in zip(divs, expected, strict=True):
        (figure,) = div.find_all("figure")
        assert figure.find_all("div", "board"), move
        assert "What would you play?" in figure.find_all("figcaption")[0].text()
        answer = answer_of(div)
        assert best in answer, answer
        assert f"played {move}, an inaccuracy that turned {change}" in answer, answer
        assert refutation in answer, answer

    assert notes(dom) == {
        "7. Re1?!": ["An inaccuracy that turned a level game into a losing one: "
                     "White's winning chances fall from 52% to 33%."],
        "8... Nh5?!": ["An inaccuracy that turned a winning game into a level one: "
                       "Black's winning chances fall from 67% to 54%."],
    }  # fmt: skip


# --- 2, 3, 4: band changes that are not swings -------------------------------------------------


def test_a_band_change_in_favour_of_the_side_that_moved_is_not_a_moment(request):
    before, after, cost, firsts, played = facts("not-swings.pgn", "7. h3")
    assert (band(before), band(after)) == ("level", "White winning")
    assert cost <= -10  # a gain of more than the floor, so only its direction keeps it out
    assert firsts and played not in firsts  # 6... Bg4's refutation starts with 7. b4
    assert "7. h3" not in moments("not-swings.pgn")
    assert not page(lazy_site(request), "not-swings.pgn").find_all("div", "moment")


def test_a_band_change_costing_less_than_10_points_is_not_a_moment(request):
    before, after, cost, firsts, played = facts("not-swings.pgn", "8. Nbd2")
    assert (band(before), band(after)) == ("White winning", "level")
    assert 0 < cost < 10
    assert firsts and played not in firsts  # a line with another first move, so only the cost keeps it out
    assert "8. Nbd2" not in moments("not-swings.pgn")
    assert not page(lazy_site(request), "not-swings.pgn").find_all("div", "moment")


def test_a_10_to_20_point_loss_inside_one_band_is_not_a_moment(request):
    before, after, cost, firsts, played = facts("not-swings.pgn", "6... Bg4")
    assert band(before) == band(after) == "level"
    assert 10 <= cost < 20
    assert firsts and played not in firsts
    assert "6... Bg4" not in moments("not-swings.pgn")
    dom = page(lazy_site(request), "not-swings.pgn")
    assert not dom.find_all("div", "moment")
    assert notes(dom) == {"Bg4?!": ["An inaccuracy: Black's winning chances fall from 48% to 37%."]}


# --- 5: the engine's own first choice ----------------------------------------------------------


def test_a_band_change_that_was_the_engines_first_choice_is_not_a_moment(request):
    # no line stored before it: the engine's first choice was the move played
    before, after, cost, firsts, played = facts("first-choice.pgn", "7. Re1")
    assert (band(before), band(after)) == ("level", "Black winning") and 10 <= cost < 20
    assert firsts == set()
    # only the previous move's refutation stored before it, and it starts with the move played
    before, after, cost, firsts, played = facts("first-choice.pgn", "7... Ng4")
    assert (band(before), band(after)) == ("Black winning", "level") and 10 <= cost < 20
    assert firsts == {played}

    assert moments("first-choice.pgn") == []
    dom = page(lazy_site(request), "first-choice.pgn")
    assert not dom.find_all("div", "moment")
    assert not dom.find_all("details")
    assert notes(dom) == {
        "7. Re1?!": ["An inaccuracy: White's winning chances fall from 52% to 33%."],
        "7... Ng4?!": ["An inaccuracy: Black's winning chances fall from 67% to 54%."],
    }


# --- 6: a 20-point critical moment that is also a swing ---------------------------------------


def test_a_critical_moment_that_is_also_a_swing_is_shown_once(site):
    before, after, cost, firsts, played = facts("critical-swing.pgn", "7. Re1")
    assert (band(before), band(after)) == ("level", "Black winning") and cost >= 20
    assert firsts and played not in firsts

    assert moments("critical-swing.pgn") == ["7. Re1"]
    dom = page(site, "critical-swing.pgn")
    (moment,) = dom.find_all("div", "moment")
    assert len(dom.find_all("details")) == 1
    assert "played 7. Re1?, a mistake that turned a level game into a losing one" in answer_of(moment)
    assert notes(dom) == {
        "7. Re1?": ["A mistake that turned a level game into a losing one: "
                    "White's winning chances fall from 52% to 28%."],
    }  # fmt: skip
    infobox = {row.find_all("th")[0].text(): row.find_all("td")[0].text() for row in dom.find_all("tr")[1:]}
    assert infobox["Critical moments"] == "1"


def test_a_critical_moment_that_is_not_a_swing_says_nothing_about_the_expected_result(tmp_path):
    # tests/fixtures/site/analyzed/: 5... Bxd1 takes Black from 33% to 0%, losing to losing
    build(tmp_path, ANALYZED)
    dom = parse(tmp_path / "games" / "2021-09-10-a9c90416b2.html")
    (note,) = notes(dom)["5... Bxd1??"]
    assert note == "A blunder: it allows mate in 2; Black's winning chances fall from 33% to 0%."
    (moment,) = dom.find_all("div", "moment")
    assert "turned" not in answer_of(moment)


# --- 7: the edges and the parameter -----------------------------------------------------------


def test_chances_exactly_at_the_upper_edge_count_as_white_winning():
    before, after, cost, firsts, played = facts("edges.pgn", "8... Nh5")
    assert after == win_percent(150) and 10 <= cost < 20
    assert band(before) == band(after) == "level"  # at 65, 63.5% is level
    assert moments("edges.pgn") == []
    assert moments("edges.pgn", outcome_bands=(35, win_percent(150))) == ["8... Nh5"]


def test_chances_exactly_at_the_lower_edge_count_as_black_winning():
    before, after, cost, firsts, played = facts("edges.pgn", "7. Re1")
    assert after == win_percent(-150) and 10 <= cost < 20
    assert band(before) == band(after) == "level"  # at 35, 36.5% is level
    assert moments("edges.pgn", outcome_bands=(win_percent(-150), 65)) == ["7. Re1"]


def test_a_changed_band_pair_changes_the_moments(tmp_path):
    assert moments("edges.pgn", outcome_bands=(40, 60)) == ["7. Re1", "8... Nh5"]  # more moments
    assert moments("two-swings.pgn", outcome_bands=(30, 70)) == []  # fewer: 33% and 46% are level at 30/70
    site = build(tmp_path, outcome_bands=(40, 60))
    assert len(page(site, "edges.pgn").find_all("div", "moment")) == 2
    site = build(tmp_path / "wide", outcome_bands=(30, 70))
    dom = page(site, "two-swings.pgn")
    assert not dom.find_all("div", "moment")
    assert "The engine found no critical moment" in dom.find_all("p", "lead")[0].text()


INVALID_BANDS = [
    (50, 50),  # lower >= upper
    (60, 40),
    (0, 65),  # outside its half
    (-5, 65),
    (50, 65),
    (35, 50),
    (35, 100),
    (35, 120),
    (math.nan, 65),  # not a number
    (35, math.nan),
    (-math.inf, 65),
    (35, math.inf),
]


@pytest.mark.parametrize("bands", INVALID_BANDS, ids=repr)
def test_an_invalid_band_pair_is_rejected_up_front_even_for_an_empty_collection(tmp_path, bands):
    out = tmp_path / "site"
    with pytest.raises(ValueError, match="outcome_bands"):
        build_site([], out, outcome_bands=bands)
    assert not out.exists()  # nothing written, not even the stylesheet or the index
    with pytest.raises(ValueError, match="outcome_bands"):
        build(out, outcome_bands=bands)
    assert not out.exists()
    with pytest.raises(ValueError, match="outcome_bands"):
        critical_moments(read("two-swings.pgn").game, outcome_bands=bands)


@pytest.mark.parametrize("bands", [(35, 65), (0.5, 99.5), (49.9, 50.1)])
def test_a_valid_band_pair_is_accepted(tmp_path, bands):
    build_site([], tmp_path, outcome_bands=bands)
    assert (tmp_path / "index.html").is_file()


# --- 8: the counts and the lead -------------------------------------------------------------------


def test_swings_count_in_the_infobox_and_the_lead_and_the_lead_is_true_for_them(site):
    reviews = critical_moments(read("two-swings.pgn").game)
    assert len(reviews) == 2
    assert all(r.before - r.after < 20 for r in reviews)  # "cost at least 20 points" alone would be false

    dom = page(site, "two-swings.pgn")
    infobox = {row.find_all("th")[0]: row.find_all("td")[0] for row in dom.find_all("tr")[1:]}
    (cell,) = [td for th, td in infobox.items() if th.text() == "Critical moments"]
    assert cell.text() == "1, 2"
    assert [a.attrs["href"] for a in cell.find_all("a")] == ["#moment-1", "#moment-2"]
    lead = dom.find_all("p", "lead")[0].text()
    assert (
        "The engine found two critical moments, where a single move cost at least 20 points of winning chances "
        "or changed the expected result; each is a “what would you play?” question below."
    ) in lead

    index = parse(site / "index.html")
    item = read("two-swings.pgn")
    (entry,) = [
        li for li in index.find_all("li")
        if li.find_all("a")[0].attrs["href"] == f"games/{file_stem(item.game, item.id)}.html"
    ]  # fmt: skip
    assert "two questions" in entry.find_all("span", "meta")[0].text()


def test_the_report_counts_the_swings(tmp_path):
    report = build_site(Collection.read(SWINGS, keep_analysis=True), tmp_path)
    assert report.critical_moments == 2 + 0 + 0 + 1 + 0  # two-swings, not-swings, first-choice, critical-swing, edges


# --- 9: unanalyzed games ----------------------------------------------------------------------------


def test_unanalyzed_games_still_have_no_moments(tmp_path):
    # read without keep_analysis, the fixture's evals and lines are stripped
    collection = Collection.read(SWINGS / "two-swings.pgn")
    assert all(not critical_moments(item.game) for item in collection)
    build_site(collection, tmp_path)
    (path,) = (tmp_path / "games").iterdir()
    dom = parse(path)
    assert not dom.find_all("div", "moment")
    assert "It has not been analyzed yet" in dom.find_all("p", "lead")[0].text()
    # and a game that keeps the [%eval]s and lines but lacks the analysis marker is not analyzed
    game = chess.pgn.read_game(io.StringIO((SWINGS / "two-swings.pgn").read_text(encoding="utf-8")))
    del game.headers["PostmortemAnalysis"]
    assert game.end().eval() is not None
    assert not critical_moments(game)
    assert not any(r.critical or r.grade for r in review_moves(game))


# --- the floor follows the inaccuracy threshold ------------------------------------------------------


def test_the_floor_follows_the_inaccuracy_threshold():
    # 8. Nbd2 costs 8.0 points: a swing once the inaccuracy threshold is 5
    assert moments("not-swings.pgn", thresholds=Thresholds(5, 20, 30)) == ["8. Nbd2"]
    # 8... Nh5 costs 13.1 points: no longer a swing once the inaccuracy threshold is 15
    assert moments("two-swings.pgn", thresholds=Thresholds(15, 20, 30)) == ["7. Re1"]
