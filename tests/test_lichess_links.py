"""The lichess links (ROADMAP.md, F-10), on the committed fixtures (no
Stockfish, no network):

  "Open this game on lichess", in each article's infobox, links to
  https://lichess.org/analysis/pgn/<moves>: the game's mainline moves in SAN,
  without move numbers and without the check and mate signs, separated by
  spaces, URL-encoded (a space is %20, never "+"). There is no game link for a
  game that starts from a set-up position or has no moves.

  "Analyze this position on lichess", inside each critical moment's hidden
  answer, links to https://lichess.org/analysis/<FEN>: the position before the
  move, with the FEN's spaces written as "_".

The narrowed link check itself is ``check_links`` in test_site.py.
tests/fixtures/site/lichess/ holds the hand-written fixtures (its README says
what each game is for).
"""

import html
import io
from pathlib import Path
from urllib.parse import unquote, urlsplit

import chess
import chess.pgn
import pytest

from pgn_postmortem import Collection
from pgn_postmortem.collection import CollectedGame, game_id
from pgn_postmortem.site import build_site
from tests.test_site import (
    ANALYZED,
    FIXTURES,
    LICHESS,
    LICHESS_GAME,
    NEW_TAB,
    ODD,
    PLAYER,
    Element,
    build,
    check_links,
    inside,
    parse,
)

LICHESS_FIXTURES = FIXTURES / "site" / "lichess"
SETS = {
    "analyzed": ANALYZED,
    "lichess": LICHESS_FIXTURES,
    "synthetic": FIXTURES / "site" / "synthetic",
    "swings": FIXTURES / "site" / "swings",
    "quiz": FIXTURES / "site" / "quiz",
    "odd": ODD,
}
GAME_TEXT = "Open this game on lichess"
POSITION_TEXT = "Analyze this position on lichess"
NBSP = " "
# The position before 31. Ra7?? in setup-blunder.pgn, after 30... h6, worked out by hand.
SETUP_QUESTION = "3r2k1/5pp1/7p/8/8/8/R4PPP/6K1 w - - 0 31"


@pytest.fixture(scope="module")
def sites(tmp_path_factory) -> dict[str, Path]:
    """Each fixture set built as a site, as the command line builds it."""
    built = {}
    for name, source in SETS.items():
        built[name] = tmp_path_factory.mktemp(name)
        build([source], built[name], *PLAYER)
    return built


def articles(site: Path) -> list[Path]:
    return sorted((site / "games").glob("*.html"))


def article_game(dom: Element) -> chess.pgn.Game:
    """The game in the article's own PGN section."""
    (pgn,) = dom.find_all("pre", "pgn")
    return chess.pgn.read_game(io.StringIO(pgn.text()))


def game_links(dom: Element) -> list[Element]:
    return [a for a in dom.find_all("a") if (a.attrs.get("href") or "").startswith(LICHESS_GAME)]


def position_links(dom: Element) -> list[Element]:
    return [
        a
        for a in dom.find_all("a")
        if (a.attrs.get("href") or "").startswith(LICHESS) and not a.attrs["href"].startswith(LICHESS_GAME)
    ]


def link_fen(link: Element) -> str:
    return link.attrs["href"][len(LICHESS) :].replace("_", " ")


def positions_before(game: chess.pgn.Game) -> dict[str, str]:
    """The FEN of the position before each mainline move, keyed by the move
    as the article writes it (``3...`` and a no-break space, then the SAN)."""
    board, positions = game.board(), {}
    for move in game.mainline_moves():
        dots = "." if board.turn == chess.WHITE else "..."
        positions[f"{board.fullmove_number}{dots}{NBSP}{board.san(move)}"] = board.fen()
        board.push(move)
    return positions


def played(details: Element) -> str:
    """The move the answer says was played, without its grade symbol."""
    (paragraph,) = [p for p in details.find_all("p") if p.text().startswith("In the game")]
    return paragraph.find_all("b")[0].text().rstrip("?!")


# --- the game link --------------------------------------------------------------------------------


def test_every_game_from_the_standard_start_has_one_game_link_with_its_moves(sites):
    signs, checked, without = set(), 0, 0
    for name, site in sites.items():
        for path in articles(site):
            dom = parse(path)
            game = article_game(dom)
            links = game_links(dom)
            if game.board().fen() != chess.STARTING_FEN or game.next() is None:
                assert not links, f"{name}/{path.name}: a game link for a set-up game"
                without += 1
                continue
            (link,) = links  # exactly one in the page
            where = f"{name}/{path.name}"
            assert inside(link, "table", "infobox") and link.text() == GAME_TEXT, where
            href = link.attrs["href"]
            parts = urlsplit(href)
            assert (parts.scheme, parts.netloc, parts.query, parts.fragment) == ("https", "lichess.org", "", ""), where
            assert "?" not in href and "#" not in href, where
            assert parts.path.startswith("/analysis/pgn/"), where
            moves = parts.path[len("/analysis/pgn/") :]
            assert "+" not in moves and " " not in moves, where  # lichess reads a "+" in the path as a space
            board, sans = game.board(), []
            for move in game.mainline_moves():
                sans.append(board.san(move))
                board.push(move)
            signs |= {sign for san in sans for sign in "+#=" if sign in san}
            assert unquote(moves) == " ".join(san.rstrip("+#") for san in sans), where
            checked += 1
    assert signs == {"+", "#", "="}, "the fixtures cover checks, mates and a promotion"
    assert checked >= 20 and without >= 4  # the set-up games of synthetic/ and lichess/


def test_a_standard_start_spelled_out_in_a_fen_header_still_gets_its_game_link(sites):
    (item,) = Collection.read(LICHESS_FIXTURES / "standard-fen.pgn", keep_analysis=True)
    assert item.game.headers["FEN"] == chess.STARTING_FEN  # kept, as the analysis step wrote it
    dom = parse(sites["lichess"] / "games" / f"2013-04-07-{item.id}.html")
    (link,) = game_links(dom)
    assert link.attrs["href"] == LICHESS_GAME + "d4%20d5%20c4"


def test_the_promotion_and_the_signs_are_encoded_as_expected(sites):
    (item,) = Collection.read(LICHESS_FIXTURES / "promotion.pgn")
    dom = parse(sites["lichess"] / "games" / f"2013-04-06-{item.id}.html")
    (link,) = game_links(dom)
    # 4... Qxf2+ and 6. bxc8=Q# lose their signs; the "=" is encoded
    assert link.attrs["href"] == LICHESS_GAME + "e4%20d5%20exd5%20c6%20dxc6%20Qb6%20cxb7%20Qxf2%20Kxf2%20Nf6%20bxc8%3DQ"


# --- set-up games and games without moves -------------------------------------------------------------


def test_a_set_up_game_has_no_game_link_but_its_critical_position_has_its_link(tmp_path):
    build([LICHESS_FIXTURES / "setup-blunder.pgn"], tmp_path, *PLAYER)
    (path,) = articles(tmp_path)
    dom = parse(path)
    assert "FEN" in article_game(dom).headers
    assert not game_links(dom)
    (moment,) = dom.find_all("div", "moment")
    (link,) = position_links(dom)
    assert inside(link, "details", "answer") and link in moment.find_all("a")
    assert link_fen(link) == SETUP_QUESTION  # after 30... h6: not the FEN header's position, nor the one after 31. Ra7
    checked = check_links(tmp_path)
    assert checked.positions >= 1 and checked.games == 0


@pytest.mark.parametrize("fen", [None, "3r2k1/5ppp/8/8/8/8/R4PPP/6K1 b - - 0 30"], ids=["standard", "set-up"])
def test_a_game_without_moves_has_no_game_link(tmp_path, fen):
    game = chess.pgn.Game()
    game.headers.update({"White": "Ada Example", "Black": "Bert Sample", "Date": "2013.04.08", "Result": "*"})
    if fen:
        game.setup(fen)
    source = tmp_path / "no-moves.pgn"
    source.write_text(str(game) + "\n", encoding="utf-8")
    assert len(Collection.read(source)) == 0  # the reader skips it, so it is built directly
    site = tmp_path / "site"
    build_site([CollectedGame(game_id(game), game, "no-moves.pgn#1")], site)
    (path,) = articles(site)
    dom = parse(path)
    assert dom.find_all("table", "infobox")
    assert not game_links(dom) and not position_links(dom)
    assert check_links(site).games == 0


# --- the position links --------------------------------------------------------------------------------


def test_every_critical_moment_has_one_position_link_to_the_position_before_its_move(sites):
    counts = dict.fromkeys(sites, 0)
    for name, site in sites.items():
        for path in articles(site):
            dom = parse(path)
            where = f"{name}/{path.name}"
            moments = dom.find_all("div", "moment")
            links = position_links(dom)
            assert len(links) == len(moments), where  # one per moment, and none anywhere else
            assert all(inside(link, "details", "answer") for link in links), where
            positions = positions_before(article_game(dom))
            for moment in moments:
                (details,) = moment.find_all("details", "answer")
                assert "open" not in details.attrs, where
                (link,) = position_links(details)
                assert link.text() == POSITION_TEXT, where
                assert urlsplit(link.attrs["href"]).path.count("/") >= 8, where  # the FEN's ranks, not encoded
                assert link_fen(link) == positions[played(details)], f"{where}: {played(details)}"
                counts[name] += 1
    assert counts["analyzed"] == 4 and counts["lichess"] == 1, counts
    assert sum(counts.values()) >= 10, counts


# --- the narrowed link check ---------------------------------------------------------------------------


def test_every_lichess_link_opens_in_a_new_tab_is_escaped_and_the_pages_load_nothing(sites):
    totals = {"games": 0, "positions": 0}
    for name, site in sites.items():
        checked = check_links(site)
        totals["games"] += checked.games
        totals["positions"] += checked.positions
        for path in site.rglob("*.html"):
            dom, text = parse(path), path.read_text(encoding="utf-8")
            assert not any("src" in e.attrs for e in dom.iter()), f"{name}/{path.name}: a src"
            for a in dom.find_all("a"):
                href = a.attrs["href"]
                if urlsplit(href).scheme:
                    assert href.startswith(LICHESS), f"{name}/{path.name}: {href}"
                    assert {key: a.attrs.get(key) for key in NEW_TAB} == NEW_TAB, f"{name}/{path.name}: {href}"
                    markup = f'<a href="{html.escape(href, quote=True)}" target="_blank" rel="noopener noreferrer">'
                    assert markup in text, f"{name}/{path.name}: {href}"
    assert totals["games"] >= 20 and totals["positions"] >= 10, totals
