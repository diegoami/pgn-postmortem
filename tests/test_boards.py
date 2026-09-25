"""The board diagrams (pgn_postmortem.site.board_html and the stylesheet), on
the committed fixtures (no Stockfish, no browser).

A board is a grid of 64 empty cells. Each cell draws its own square's colour
(class ``l`` or ``d``), its piece (a piece class, a background image) and, on
the last move's squares, the highlight (``hl``), so the three always share the
same box. The board itself draws no square pattern: a board-level pattern and
the grid's cells round differently when a square is not a whole number of
pixels, which skewed the squares against the pieces and the highlight (the
defect "The final position looks skewed", 2026-09-25; the board design of
F-1.2).
"""

import re

import chess
import pytest

from pgn_postmortem.site import PIECE_CLASSES, board_html
from tests.test_lichess_links import LICHESS, POSITION_TEXT, SETS, article_game, articles, sites  # noqa: F401
from tests.test_site import Element, TreeBuilder, inside, parse

FILES = "abcdefgh"


def cells_of(board: Element) -> list[list[Element]]:
    """The board's cells, as eight rows of eight, top to bottom."""
    cells = [c for c in board.children if isinstance(c, Element)]
    assert len(cells) == 64 and all(c.tag == "i" for c in cells), "a board is 64 <i> cells"
    return [cells[i : i + 8] for i in range(0, 64, 8)]


def squares_by_labels(board: Element) -> list[list[int]]:
    """The square of each cell, read from the board's own coordinates: the rank
    on the first cell of each row (``data-r``), the file on each cell of the
    bottom row (``data-f``). They must be one of the two orientations."""
    rows = cells_of(board)
    ranks = [int(row[0].attrs["data-r"]) for row in rows]
    files = [cell.attrs["data-f"] for cell in rows[7]]
    white_below = (ranks, files) == ([8, 7, 6, 5, 4, 3, 2, 1], list(FILES))
    black_below = (ranks, files) == ([1, 2, 3, 4, 5, 6, 7, 8], list(reversed(FILES)))
    assert white_below or black_below, f"the labels are neither orientation: ranks {ranks}, files {files}"
    # no other cell carries a coordinate
    for r, row in enumerate(rows):
        for f, cell in enumerate(row):
            assert ("data-r" in cell.attrs) == (f == 0) and ("data-f" in cell.attrs) == (r == 7)
    return [[chess.square(FILES.index(file), rank - 1) for file in files] for rank in ranks]


def check_board(board: Element, position: chess.Board, highlight: set[int]) -> bool:
    """Every cell carries its square's colour, its square's piece and, only on
    ``highlight``, the highlight; returns whether Black is at the bottom."""
    squares = squares_by_labels(board)
    for row, row_squares in zip(cells_of(board), squares, strict=True):
        for cell, square in zip(row, row_squares, strict=True):
            name = chess.square_name(square)
            classes = (cell.attrs.get("class") or "").split()
            light = bool(chess.BB_LIGHT_SQUARES & chess.BB_SQUARES[square])
            assert ("l" in classes, "d" in classes) == (light, not light), f"{name}: {classes}"
            piece = position.piece_at(square)
            pieces = [c for c in classes if c in PIECE_CLASSES.values()]
            assert pieces == ([PIECE_CLASSES[piece.symbol()]] if piece else []), f"{name}: {classes}"
            assert ("hl" in classes) == (square in highlight), f"{name}: {classes}"
            assert set(classes) <= {"l", "d", "hl", *PIECE_CLASSES.values()}, f"{name}: {classes}"
    return squares[0][0] == chess.H1


def one_board(markup: str) -> Element:
    builder = TreeBuilder()
    builder.feed(markup)
    builder.close()
    (board,) = builder.root.find_all("div", "board")
    return board


# --- one board, both ways up ---------------------------------------------------------


@pytest.mark.parametrize("flipped", [False, True], ids=["white-below", "black-below"])
def test_each_cell_draws_its_own_square_colour_piece_and_highlight(flipped):
    position = chess.Board()
    for san in ("e4", "e5", "Nf3"):
        position.push_san(san)
    board = one_board(board_html(position, flipped=flipped, highlight=(chess.G1, chess.F3)))
    assert check_board(board, position, {chess.G1, chess.F3}) == flipped
    rows = cells_of(board)
    # the corners, worked out by hand: a1 and h8 are dark, h1 and a8 light, whichever way up
    corners = {"a8": "l", "h8": "d", "a1": "d", "h1": "l"}
    top_left, top_right, bottom_left, bottom_right = ("h1", "a1", "h8", "a8") if flipped else ("a8", "h8", "a1", "h1")
    for cell, name in ((rows[0][0], top_left), (rows[0][7], top_right), (rows[7][0], bottom_left),
                       (rows[7][7], bottom_right)):
        assert corners[name] in cell.attrs["class"].split(), name
    # the highlight on its two squares, over each one's own colour: g1 dark and empty, f3 light with the knight
    g1, f3 = (rows[0][1], rows[2][2]) if flipped else (rows[7][6], rows[5][5])
    assert g1.attrs["class"].split() == ["d", "hl"]
    assert f3.attrs["class"].split() == ["l", "wN", "hl"]


# --- every board of every fixture site ------------------------------------------------


def test_every_board_of_every_fixture_site_carries_the_colours_pieces_and_highlight_of_its_game(sites):  # noqa: F811
    """Each board against its article's own PGN section: the infobox's is the
    final position with the last move highlighted; a critical moment's is the
    position of its lichess link (the position before the move), with the move
    that led to it highlighted, none from the starting position."""
    boards, highlighted, orientations = 0, 0, set()
    for name in SETS:
        for path in articles(sites[name]):
            dom = parse(path)
            game = article_game(dom)
            end = game.end()
            (infobox,) = dom.find_all("table", "infobox")
            (final,) = infobox.find_all("div", "board")
            last = {end.move.from_square, end.move.to_square} if end.move else set()
            orientations.add(check_board(final, end.board(), last))
            highlighted += len(last)
            boards += 1
            nodes = {node.board().fen(): node for node in [game, *game.mainline()]}
            moments = dom.find_all("div", "moment")
            for moment in moments:
                (board,) = moment.find_all("div", "board")
                (link,) = [a for a in moment.find_all("a") if a.text() == POSITION_TEXT]
                node = nodes[link.attrs["href"][len(LICHESS) :].replace("_", " ")]
                before = {node.move.from_square, node.move.to_square} if node.move else set()
                orientations.add(check_board(board, node.board(), before))
                highlighted += len(before)
                boards += 1
            # no other board on the page
            every = dom.find_all("div", "board")
            assert len(every) == 1 + len(moments), path.name
            assert all(inside(b, "table", "infobox") or inside(b, "div", "moment") for b in every), path.name
    assert orientations == {False, True}, "both orientations are covered"
    assert boards >= 50 and highlighted >= 100, (boards, highlighted)  # 55 and 110 when written


# --- the stylesheet --------------------------------------------------------------------


def rules(css: str) -> list[tuple[list[str], dict[str, str]]]:
    """The stylesheet's rules as (selectors, declarations), the ones inside
    ``@media`` included."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    found = []
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        selector = selector.split("{")[-1].strip()
        declarations = dict(
            (part.split(":", 1)[0].strip(), part.split(":", 1)[1].strip()) for part in body.split(";") if ":" in part
        )
        found.append(([s.strip() for s in selector.split(",")], declarations))
    return found


def test_the_board_draws_no_square_pattern_and_each_cell_its_own_colour(sites):  # noqa: F811
    css = (sites["analyzed"] / "assets" / "style.css").read_text(encoding="utf-8")
    parsed = rules(css)
    assert "gradient(" not in css, "a gradient draws squares that the cells do not share"
    for selectors, declarations in parsed:
        for selector in selectors:
            if re.search(r"\.board$", selector):  # the board element itself, in any context
                assert not [p for p in declarations if p.startswith("background")], f"{selector}: {declarations}"
            if re.match(r"\.board i\b", selector):  # a cell: never a background image, which would hide the piece
                assert "background-image" not in declarations and "background" not in declarations, selector
    colour = {sel: d.get("background-color") for sels, d in parsed for sel in sels}
    assert colour[".board i.l"] == "var(--light)" and colour[".board i.d"] == "var(--dark)"
    assert colour[".board i.l.hl"] == "var(--hl-light)" and colour[".board i.d.hl"] == "var(--hl-dark)"
    # each set of colours (light, and dark mode) defines the highlight, solid and different from the square's
    roots = [d for sels, d in parsed if sels == [":root"]]
    assert len(roots) == 2
    for root in roots:
        for square in ("light", "dark"):
            assert re.fullmatch(r"#[0-9a-f]{6}", root[f"--hl-{square}"]), root
            assert root[f"--hl-{square}"] != root[f"--{square}"]
    # the piece classes set the image only; the cells' rules never override it
    for symbol, cls in PIECE_CLASSES.items():
        assert f".{cls}{{background-image:url(" in css, symbol

