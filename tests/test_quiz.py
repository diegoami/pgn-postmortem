"""The quiz list of the player's own mistakes, worst first (ROADMAP.md, F-9),
on the hand-written fixtures in tests/fixtures/site/quiz/ (their README says
what each game is and why) and on the analyzed fixture of test_site.py. No
test here runs Stockfish.

The quiz page, ``quiz.html``, lists every critical moment (F-6's rules) that
the player played, across the player's games, from the move that lost the
most winning chances down; ties go by the game's position in the index, then
the article's file name, then move order. Each line links to its question.
With no player there is no quiz page. The reading-history marks are the
script's, tested by the "script" gate (tests/js/quiz.test.mjs).
"""

import dataclasses
from pathlib import Path

import chess
import pytest

from pgn_postmortem import Collection, build_site, critical_moments
from pgn_postmortem.analysis import win_percent
from pgn_postmortem.collection import CollectedGame, file_stem, player_names
from pgn_postmortem.site import index_order, make_articles, move_key, move_label, quiz_entries, quiz_order
from tests.test_site import ANALYZED, PLAYER, Element, build, check_links, parse

QUIZ = Path(__file__).resolve().parent / "fixtures" / "site" / "quiz"
NAMES = {"player": "Ada Example", "aliases": ["adaex", "Example, Ada"]}
NBSP = " "

# The quiz of every game in tests/fixtures/site/quiz/, for Ada Example, worked out by hand (its README).
EXPECTED = [
    ("blunder-2015.pgn", "7... a6"),  # 45.7 points, the worst
    ("tie-999.pgn", "7. Re1"),  # 26.95, three games tied: the index lists the year 999 first
    ("tie-2012.pgn", "7. Re1"),
    ("ties-2014.pgn", "7. Re1"),  # and two moves tied in one game: move order
    ("ties-2014.pgn", "8. h3"),
    ("both-sides.pgn", "7. Re1"),  # 18.7, an outcome swing; both sides are the player
    ("both-sides.pgn", "8... Nh5"),  # 13.1, an outcome swing
]


def plain(text: str) -> str:
    return text.replace(NBSP, " ")


def read(name: str) -> CollectedGame:
    (item,) = Collection.read(QUIZ / name, keep_analysis=True)
    return item


def stem_of(name: str) -> str:
    item = read(name)
    return file_stem(item.game, item.id)


def facts(name: str, label: str) -> tuple[float, int, str]:
    """Read straight from the fixture, not through the library: what the move
    ``label`` cost its side in winning chances (exactly), its number among the
    game's critical moments (its ``moment-N``), and its move key (``7w``)."""
    game = read(name).game
    labels = [plain(move_label(r.board_before, r.node.move)) for r in critical_moments(game)]
    for node in game.mainline():
        if plain(move_label(node.parent.board(), node.move)) == label:
            before = win_percent(node.parent.eval().white().score())
            after = win_percent(node.eval().white().score())
            cost = before - after if node.turn() == chess.BLACK else after - before
            return cost, labels.index(label) + 1, move_key(node.parent.board())
    raise AssertionError(f"{label} is not in {name}")


def quiz_list(site: Path) -> Element | None:
    found = [e for e in parse(site / "quiz.html").find_all("ol") if e.attrs.get("id") == "quiz"]
    assert len(found) <= 1
    return found[0] if found else None


def lines(site: Path) -> list[dict[str, str]]:
    """Each line of the quiz page: its parts as text, its link and its data- attributes."""
    found = []
    for li in quiz_list(site).find_all("li"):
        (link,) = li.find_all("a")
        spans = {span.attrs["class"]: plain(span.text()) for span in li.find_all("span")}
        assert sorted(spans) == ["lost", "meta", "rank"], spans  # no mark in the static page
        found.append(
            {
                "rank": spans["rank"],
                "move": plain(link.text()),
                "href": link.attrs["href"],
                "points": spans["lost"],
                "meta": spans["meta"],
                "game": li.attrs.get("data-game"),
                "key": li.attrs.get("data-move"),
                "text": plain(li.text()),
            }
        )
    return found


def listed(site: Path) -> list[tuple[str, str]]:
    """The quiz as (the article's file stem, the move), in its order."""
    return [(line["href"].split("/")[1].split(".html")[0], line["move"]) for line in lines(site)]


def expected(pairs=EXPECTED) -> list[tuple[str, str]]:
    return [(stem_of(name), label) for name, label in pairs]


def links_quiz(site: Path) -> bool:
    return any(a.attrs.get("href") == "quiz.html" for a in parse(site / "index.html").find_all("a"))


@pytest.fixture(scope="module")
def site(tmp_path_factory) -> Path:
    """Every quiz fixture, read without a player (so others.pgn is in the site too), built for Ada Example."""
    out = tmp_path_factory.mktemp("quiz")
    build_site(Collection.read(QUIZ, keep_analysis=True), out, **NAMES)
    return out


# --- which questions, and in which order ---------------------------------------------------------


def test_the_quiz_lists_exactly_the_players_own_critical_moments(site):
    names = player_names(NAMES["player"], NAMES["aliases"])
    own, others = set(), set()
    for item in Collection.read(QUIZ, keep_analysis=True):
        for review in critical_moments(item.game):
            mover = item.game.headers["White" if review.mover == chess.WHITE else "Black"]
            moment = (file_stem(item.game, item.id), plain(move_label(review.board_before, review.node.move)))
            (own if mover.strip().casefold() in names else others).add(moment)
    assert own == set(expected())
    # the opponents' moments, and those of a game that is not the player's, are left out
    assert others == set(expected([("ties-2014.pgn", "7... a6"), ("opponents-only.pgn", "7. Re1"),
                                   ("others.pgn", "7. Re1")]))  # fmt: skip
    assert sorted(listed(site)) == sorted(own)
    assert not set(listed(site)) & others
    # outcome swings (F-6) that cost less than 20 points are among them
    assert [facts("both-sides.pgn", label)[0] < 20 for label in ("7. Re1", "8... Nh5")] == [True, True]


def test_the_quiz_is_in_worst_first_order_with_the_tie_rule(site):
    assert listed(site) == expected()
    costs = [facts(name, label)[0] for name, label in EXPECTED]
    assert costs == sorted(costs, reverse=True)
    # the three games tie exactly (the unrounded value), and so do the two moves of ties-2014
    assert costs[1] == costs[2] == costs[3] == costs[4]
    # the games' tie goes by their position in the index, which lists the year 999 first; by the file
    # name alone, tie-999's 999-09-09-… would come after 2012-… and 2014-…
    index = [a.attrs["href"] for a in parse(site / "index.html").find_all("a") if a.attrs["href"].startswith("games/")]
    tied = [f"games/{stem_of(name)}.html" for name in ("tie-999.pgn", "tie-2012.pgn", "ties-2014.pgn")]
    assert sorted(tied, key=index.index) == tied
    assert sorted(tied) != tied
    # the ranks are the order, 1 to 7
    assert [line["rank"] for line in lines(site)] == [f"{i}." for i in range(1, 8)]


def test_the_tie_rule_goes_on_to_the_file_name_then_move_order():
    # Two games never share a position in the index, so the file name decides nothing on a real site;
    # the rule is total all the same, so the entries' positions are made equal here.
    names = player_names(NAMES["player"], NAMES["aliases"])
    entries = quiz_entries(index_order(make_articles(Collection.read(QUIZ, keep_analysis=True))), names)
    by_move = {(entry.filename, plain(move_label(entry.review.board_before, entry.review.node.move))): entry
               for entry in entries}  # fmt: skip
    a = by_move[(f"{stem_of('tie-999.pgn')}.html", "7. Re1")]
    b = by_move[(f"{stem_of('tie-2012.pgn')}.html", "7. Re1")]
    assert a.loss == b.loss and a.position < b.position
    assert quiz_order([b, a]) == [a, b]  # the index first
    same = [dataclasses.replace(a, position=0), dataclasses.replace(b, position=0)]
    assert [e.filename for e in same] != sorted(e.filename for e in same)  # 999-… is given first
    assert [e.filename for e in quiz_order(same)] == sorted(e.filename for e in same)  # then the file name
    c = by_move[(f"{stem_of('ties-2014.pgn')}.html", "7. Re1")]
    d = by_move[(f"{stem_of('ties-2014.pgn')}.html", "8. h3")]
    assert c.loss == d.loss and c.position == d.position and c.filename == d.filename
    assert quiz_order([d, c]) == [c, d]  # then move order
    worse = dataclasses.replace(d, loss=d.loss + 1e-9)
    assert quiz_order([c, worse]) == [worse, c]  # the points first, exactly


def test_names_match_regardless_of_case_and_spaces_and_both_sides_count(tmp_path, site):
    build_site(Collection.read(QUIZ, keep_analysis=True), tmp_path, player="  ada EXAMPLE ",
               aliases=[" ADAEX", "example, ada  "])  # fmt: skip
    assert listed(tmp_path) == listed(site) == expected()
    # ties-2014's White is "  ADA EXAMPLE "; both-sides has the player on both sides, and both count
    assert read("ties-2014.pgn").game.headers["White"] == "  ADA EXAMPLE "
    assert [label for stem, label in listed(site) if stem == stem_of("both-sides.pgn")] == ["7. Re1", "8... Nh5"]
    # an alias alone is a player
    build_site(Collection.read(QUIZ, keep_analysis=True), tmp_path / "alias", aliases=["ADAEX"])
    assert listed(tmp_path / "alias") == expected([("tie-999.pgn", "7. Re1"), ("both-sides.pgn", "7. Re1")])


# --- each line --------------------------------------------------------------------------------------


def test_each_line_links_to_its_question_and_carries_its_game_and_move(site):
    assert check_links(site) > 0  # every link of every page, the quiz's included, resolves (files and anchors)
    for line, (name, label) in zip(lines(site), EXPECTED, strict=True):
        item = read(name)
        cost, number, key = facts(name, label)
        assert line["href"] == f"games/{file_stem(item.game, item.id)}.html#moment-{number}"
        assert line["move"] == label
        assert line["points"] == f"{cost:.0f} points"
        assert (line["game"], line["key"]) == (item.id, key)
        # the anchor is that move's question, and its answer carries the same game and move
        article = parse(site / line["href"].split("#")[0])
        (moment,) = [e for e in article.iter() if e.attrs.get("id") == f"moment-{number}"]
        assert moment.tag == "div" and "moment" in moment.attrs["class"]
        (answer,) = moment.find_all("details", "answer")
        assert answer.attrs["data-move"] == line["key"]
        assert f"played {label}" in plain(answer.text())
        (body,) = article.find_all("article")
        assert body.attrs["data-game"] == line["game"]


def test_each_line_names_the_game_by_date_and_opponent(site):
    metas = [line["meta"] for line in lines(site)]
    assert metas == [
        "5 May 2015 · vs. Enzo Opponent",
        "9 September 999 · vs. Gino Newcomer",
        "2 February 2012 · vs. Dora Sample",
        "4 April 2014 · vs. Carl <Foe> & Co",  # escaped in the page, as every header is
        "4 April 2014 · vs. Carl <Foe> & Co",
        "3 March 2013 · vs. Ada Example",  # both sides the player: the other side, as its name is shown
        "3 March 2013 · vs. adaex",
    ]
    text = (site / "quiz.html").read_text(encoding="utf-8")
    assert "<Foe>" not in text and "Carl &lt;Foe&gt; &amp; Co" in text
    # no diagram and no answer on the quiz page
    dom = parse(site / "quiz.html")
    assert not dom.find_all("div", "board") and not dom.find_all("details")


# --- no player, no own moments ---------------------------------------------------------------------


def test_without_a_player_there_is_no_quiz_page_and_no_link(tmp_path):
    report = build_site(Collection.read(QUIZ, keep_analysis=True), tmp_path / "library")
    assert not (tmp_path / "library" / "quiz.html").exists()
    assert not links_quiz(tmp_path / "library")
    assert report.quiz is None
    build_site(Collection.read(QUIZ, keep_analysis=True), tmp_path / "blank", player="  ", aliases=["", " "])
    assert not (tmp_path / "blank" / "quiz.html").exists() and not links_quiz(tmp_path / "blank")  # blank names: none
    build([QUIZ], tmp_path / "command")  # the site command without --player or --alias
    assert not (tmp_path / "command" / "quiz.html").exists()
    assert not links_quiz(tmp_path / "command")
    index = (tmp_path / "command" / "index.html").read_text(encoding="utf-8")
    assert "quiz.html" not in index and "Quiz:" not in index and "quiz-link" not in index


@pytest.mark.parametrize("keep_analysis", [True, False], ids=["no-own-moment", "not-analyzed"])
def test_a_player_with_no_own_moments_gets_a_page_that_says_so(tmp_path, keep_analysis):
    games = Collection.read([QUIZ / "opponents-only.pgn", QUIZ / "others.pgn"], keep_analysis=keep_analysis)
    report = build_site(games, tmp_path, **NAMES)
    assert report.quiz == tmp_path / "quiz.html" and report.quiz_questions == 0
    dom = parse(tmp_path / "quiz.html")
    assert quiz_list(tmp_path) is None and not dom.find_all("li")
    assert "no questions" in dom.find_all("p", "lead")[0].text()
    assert links_quiz(tmp_path)
    assert check_links(tmp_path) > 0


# --- stale pages ------------------------------------------------------------------------------------


def test_a_rebuild_without_a_player_removes_the_quiz_page_the_builder_wrote(tmp_path):
    games = Collection.read(QUIZ, keep_analysis=True)
    build_site(games, tmp_path, **NAMES)
    assert (tmp_path / "quiz.html").is_file() and links_quiz(tmp_path)
    report = build_site(games, tmp_path)
    assert not (tmp_path / "quiz.html").exists()
    assert report.removed == [tmp_path / "quiz.html"]
    assert not links_quiz(tmp_path)


def test_a_quiz_page_the_builder_did_not_write_is_never_removed(tmp_path):
    foreign = tmp_path / "quiz.html"
    foreign.write_text("<!DOCTYPE html>\n<title>My own quiz</title>\n", encoding="utf-8")
    report = build_site(Collection.read(QUIZ, keep_analysis=True), tmp_path)
    assert foreign.read_text(encoding="utf-8") == "<!DOCTYPE html>\n<title>My own quiz</title>\n"
    assert report.removed == []


# --- how the names reach the builder ------------------------------------------------------------------


def test_a_collection_read_for_a_player_builds_the_quiz(tmp_path):
    collection = Collection.read(QUIZ, keep_analysis=True, **NAMES)
    assert (collection.player, collection.aliases) == ("Ada Example", ("adaex", "Example, Ada"))
    collection.build_site(tmp_path / "method")
    assert listed(tmp_path / "method") == expected()
    build_site(collection, tmp_path / "function")  # the module's function, given the collection
    assert listed(tmp_path / "function") == expected()
    # names given to the builder take the place of the collection's
    collection.build_site(tmp_path / "alias", aliases=["adaex"])
    assert listed(tmp_path / "alias") == expected([("tie-999.pgn", "7. Re1"), ("both-sides.pgn", "7. Re1")])
    # the aliases are kept even when they came as a one-pass iterable
    once = Collection.read(QUIZ, player=None, aliases=iter(["adaex", "Example, Ada"]), keep_analysis=True)
    assert once.aliases == ("adaex", "Example, Ada")


def test_a_collection_without_names_builds_no_quiz(tmp_path):
    games = list(Collection.read(QUIZ, keep_analysis=True, **NAMES))
    Collection(games).build_site(tmp_path / "direct")
    assert not (tmp_path / "direct" / "quiz.html").exists()
    build_site(games, tmp_path / "list")  # a plain list of games has no names either
    assert not (tmp_path / "list" / "quiz.html").exists()


def test_the_site_command_passes_its_player_and_aliases(tmp_path):
    build([QUIZ], tmp_path, "--player", "Ada Example", "--alias", "adaex", "--alias", "Example, Ada")
    assert listed(tmp_path) == expected()  # others.pgn is not even read: it is not the player's
    assert links_quiz(tmp_path)


def test_the_report_counts_the_questions(tmp_path):
    report = build_site(Collection.read(QUIZ, keep_analysis=True), tmp_path, **NAMES)
    assert report.quiz == tmp_path / "quiz.html"
    assert report.quiz_questions == len(EXPECTED)
    assert report.summary(tmp_path).endswith(f" The quiz lists {len(EXPECTED)} of them, the player's own.")
    assert "quiz" not in build_site([], tmp_path / "none").summary(tmp_path / "none")


# --- the index ----------------------------------------------------------------------------------------


def test_the_index_links_to_the_quiz_at_its_top(site):
    dom = parse(site / "index.html")
    main = dom.find_all("main")[0]
    blocks = [child for child in main.children if isinstance(child, Element)]
    # the title, the summary, then the link: before the reading history and the list of games
    assert [block.tag for block in blocks[:3]] == ["h1", "p", "p"]
    (link,) = blocks[2].find_all("a")
    assert link.attrs["href"] == "quiz.html"
    assert blocks[2].text().endswith(": seven questions.")


def test_the_fixture_site_has_a_quiz_of_ada_examples_one_own_moment(tmp_path):
    # tests/fixtures/site/analyzed: of its four critical moments, only 3... Nf6 is Ada Example's (as AdaEx)
    build([ANALYZED], tmp_path, *PLAYER)
    assert [(line["move"], line["game"], line["key"]) for line in lines(tmp_path)] == [
        ("3... Nf6", "9705c13f05", "3b")
    ]
    assert lines(tmp_path)[0]["href"] == "games/2020-06-01-9705c13f05.html#moment-1"


def test_the_lead_says_how_many_questions_from_how_many_games(tmp_path, site):
    def lead(root: Path) -> str:
        return plain(parse(root / "quiz.html").find_all("p", "lead")[0].text())

    # others.pgn is in the site but not one of Ada Example's games
    assert lead(site).startswith("Seven questions from six games of Ada Example's: each is a critical moment where "
                                 "Ada Example was the one to move, a move that cost at least 20 points")  # fmt: skip
    build([ANALYZED], tmp_path, *PLAYER)
    assert lead(tmp_path).startswith("One question from six games of Ada Example's: it is a critical moment")
