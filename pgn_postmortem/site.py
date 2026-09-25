"""The static site: one Wikipedia-style article per game, and an index of the
games by year.

The site is plain HTML and one stylesheet, written to an output directory::

    index.html              the games by year, each linking to its article
    games/<date>-<id>.html  one article per game, named like the game's PGN file
    assets/style.css        the layout, the colours (light or dark, as the OS
                            says) and the one piece set every diagram uses

Every link is relative and names a file (``../index.html``, not ``../``), so
the site works from a web server, from a folder copied to a phone, and from
``file://``. There is no JavaScript and nothing is loaded from the network.

An article has an infobox (the players, the event, the result, the final
position), a lead paragraph, the moves with notes, a diagram and a question at
each critical moment, a conclusion and the game's PGN. All prose comes from
templates (the LLM is F-2 in ``ROADMAP.md``).

**Critical moments.** They come from the ``[%eval]`` comments the analysis
step writes (``pgn_postmortem.analysis``), and only from those: a game read
without the ``PostmortemAnalysis`` header has none, whatever comments its
source carried. For every move, the mover's winning chances before and after
it are the lichess win percentages (``analysis.win_percent``) of the
evaluation of the position before the move (the ``[%eval]`` of the previous
move) and after it (its own ``[%eval]``; a move that gives checkmate has none
and counts as 100 for the side that gave it). The difference is what the
move lost; it is graded with the analysis step's thresholds
(``analysis.classify``: 10/20/30 points by default, lichess's), so the grades
here are the NAGs the analysis step wrote. **A critical moment is a move that
lost at least ``thresholds.mistake`` points (20 by default): a mistake or a
blunder.** Inaccuracies get a note but no diagram. The first move of a game
has no evaluation before it (the analysis step does not write the start
position's), so it is never graded; from the standard start no single move
loses that much.

At each critical moment the article shows the position before the move, from
the side of the player to move, and asks "What would you play?"; the answer
(the engine's better move and line, then what the move played allowed) is in a
``<details>`` element, hidden until tapped. The engine lines are the
variations the analysis step attached: the best line from the position before
the move, and the refutation after it.

**Results that were not recorded** (ROADMAP.md, F-5). For a game whose
``Result`` is ``*`` or missing, the site shows the result ``shown_result``
gives, in this order: the board's, if the final position is checkmate (the
mating side wins), stalemate or insufficient material (a draw); else, for an
analyzed game whose final move carries an ``[%eval]``, a win for the side
with at least ``presume_threshold`` (70 by default, 55 to 95) winning chances
by ``analysis.win_percent`` (a forced mate counts as 100), and a draw
otherwise; else the site says the result was not recorded. The result is
shown like a recorded one, with no marker, everywhere outside the PGN section
(the infobox, the lead, the end of the moves, the conclusion, the index).
The game itself is untouched: its ``Result`` header, so its id and its file
name, and the article's PGN section stay as the source had them. A recorded
result is always shown as recorded.
"""

from __future__ import annotations

import html
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import chess
import chess.engine
import chess.pgn
import chess.svg

from pgn_postmortem.analysis import LICHESS_THRESHOLDS, MATE_SCORE, Thresholds, classify, win_percent
from pgn_postmortem.collection import (
    ANALYSIS_HEADER,
    CollectedGame,
    date_fields,
    file_stem,
    format_game,
    is_number,
    strip_game,
)

GRADES = {
    chess.pgn.NAG_DUBIOUS_MOVE: ("inaccuracy", "An inaccuracy", "?!"),
    chess.pgn.NAG_MISTAKE: ("mistake", "A mistake", "?"),
    chess.pgn.NAG_BLUNDER: ("blunder", "A blunder", "??"),
}
POSITION_SYMBOLS = {10: "=", 13: "∞", 14: "⩲", 15: "⩱", 16: "±", 17: "∓", 18: "+−", 19: "−+"}
RESULTS = {"1-0": "1–0", "0-1": "0–1", "1/2-1/2": "½–½"}
NOT_RECORDED = "*"  # the PGN result of a game in progress or with an unknown result
PRESUME_THRESHOLD = 70.0  # the winning chances (%) that make an unrecorded result a win (owner, 2026-09-24)
PRESUME_THRESHOLD_RANGE = (55.0, 95.0)
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]  # fmt: skip
NUMBER_WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
NBSP = "\u00a0"  # between a move number and its move, so a line never breaks between them
GENERATOR = '<meta name="generator" content="pgn-postmortem">'  # in every page; marks what a rebuild may delete


# --- reading the analysis ---------------------------------------------------


@dataclass(frozen=True)
class MoveReview:
    """One mainline move and what the analysis says about it. Without
    analysis (or for the first move) ``before``/``after`` are None and the
    move is not graded."""

    node: chess.pgn.ChildNode
    before: float | None  # the mover's winning chances (0-100) before the move
    after: float | None  # and after it
    score_before: chess.engine.PovScore | None
    score_after: chess.engine.PovScore | None
    grade: int | None  # NAG_DUBIOUS_MOVE, NAG_MISTAKE, NAG_BLUNDER or None
    critical: bool

    @property
    def mover(self) -> chess.Color:
        return not self.node.turn()

    @property
    def board_before(self) -> chess.Board:
        return self.node.parent.board()

    @property
    def symbol(self) -> str:
        return GRADES[self.grade][2] if self.grade else ""


def is_analyzed(game: chess.pgn.Game) -> bool:
    """Whether the game carries the analysis step's marker header."""
    return ANALYSIS_HEADER in game.headers


def white_cp(node: chess.pgn.ChildNode) -> tuple[int | None, chess.engine.PovScore | None]:
    """The White-POV evaluation after ``node`` in centipawns (a mate as
    ``MATE_SCORE`` minus its length, as the analysis step counts it), and the
    score it came from; a checkmate counts as a full mate for the side that
    gave it."""
    score = node.eval()
    if score is not None:
        return score.white().score(mate_score=MATE_SCORE), score
    if node.board().is_checkmate():
        return (MATE_SCORE if node.turn() == chess.BLACK else -MATE_SCORE), None
    return None, None


def review_moves(game: chess.pgn.Game, thresholds: Thresholds = LICHESS_THRESHOLDS) -> list[MoveReview]:
    """Every mainline move with its grade and whether it is a critical
    moment (the rule is in the module docstring)."""
    analyzed = is_analyzed(game)
    reviews = []
    cp_before: int | None = None
    score_before: chess.engine.PovScore | None = None
    for node in game.mainline():
        cp_after, score_after = white_cp(node) if analyzed else (None, None)
        before = after = None
        grade, critical = None, False
        if cp_before is not None and cp_after is not None:
            mover_is_white = node.turn() == chess.BLACK
            before, after = win_percent(cp_before), win_percent(cp_after)
            if not mover_is_white:
                before, after = 100 - before, 100 - after
            loss = max(before - after, 0.0)
            grade = classify(loss, thresholds)
            critical = loss >= thresholds.mistake
        reviews.append(MoveReview(node, before, after, score_before, score_after, grade, critical))
        cp_before, score_before = cp_after, score_after
    return reviews


def critical_moments(game: chess.pgn.Game, thresholds: Thresholds = LICHESS_THRESHOLDS) -> list[MoveReview]:
    """The game's critical moments, in move order: the moves that lost the
    mover at least ``thresholds.mistake`` points of winning chances."""
    return [review for review in review_moves(game, thresholds) if review.critical]


# --- the result -----------------------------------------------------------------


def check_presume_threshold(threshold: float) -> None:
    """Raise ``ValueError`` unless ``threshold`` is from 55 to 95."""
    low, high = PRESUME_THRESHOLD_RANGE
    if not low <= threshold <= high:  # also rejects NaN
        raise ValueError(
            f"presume_threshold must be from {low:g} to {high:g} (a side's winning chances in percent), "
            f"not {threshold!r}"
        )


def final_white_chances(game: chess.pgn.Game) -> float | None:
    """White's winning chances (0-100) in the final position of an analyzed
    game, from the ``[%eval]`` of its last move (a forced mate counts as 100
    for the side with the mate), or None: not analyzed, or no eval there."""
    if not is_analyzed(game):
        return None
    score = game.end().eval()
    if score is None:
        return None
    white = score.white()
    if white.is_mate():
        return 100.0 if white > chess.engine.Cp(0) else 0.0
    return win_percent(white.score())


def shown_result(game: chess.pgn.Game, presume_threshold: float = PRESUME_THRESHOLD) -> str:
    """The result the site shows for ``game``, in PGN notation: its
    ``Result`` header when one is recorded; otherwise the board's result,
    else the result presumed from the analysis, else ``*`` (not recorded).
    The rule is in the module docstring. ``game`` is not changed."""
    check_presume_threshold(presume_threshold)
    recorded = (game.headers.get("Result") or NOT_RECORDED).strip()
    if recorded not in ("", NOT_RECORDED):
        return recorded
    board = game.end().board()
    if board.is_checkmate():
        return "0-1" if board.turn == chess.WHITE else "1-0"
    if board.is_stalemate() or board.is_insufficient_material():
        return "1/2-1/2"
    white = final_white_chances(game)
    if white is None:
        return NOT_RECORDED
    if white >= presume_threshold:
        return "1-0"
    if 100 - white >= presume_threshold:
        return "0-1"
    return "1/2-1/2"


def engine_line(node: chess.pgn.GameNode) -> tuple[list[chess.Move], str] | None:
    """The first engine line the analysis step attached off ``node`` (a
    variation, not the mainline), and the symbol of the position it ends in."""
    if len(node.variations) < 2:
        return None
    start = node.variations[1]
    moves = [start.move, *start.mainline_moves()]
    last = start.end()
    symbol = next((POSITION_SYMBOLS[nag] for nag in sorted(last.nags) if nag in POSITION_SYMBOLS), "")
    return moves, symbol


# --- text helpers -----------------------------------------------------------


def esc(text: object) -> str:
    """Text for an element's content."""
    return html.escape(str(text), quote=False)


def attr(text: object) -> str:
    """Text for a quoted attribute value."""
    return html.escape(str(text), quote=True)


def known(value: str | None) -> str | None:
    value = (value or "").strip()
    return None if value in ("", "?", "-", "??", "????.??.??") else value


def display_name(name: str | None) -> str:
    """A player's name as prose wants it: PGN's ``Last, First`` becomes
    ``First Last``."""
    name = known(name)
    if name is None:
        return "Unknown"
    if name.count(",") == 1:
        last, first = (part.strip() for part in name.split(","))
        if last and first:
            return f"{first} {last}"
    return name


def number_word(n: int) -> str:
    return NUMBER_WORDS[n] if 0 <= n < len(NUMBER_WORDS) else str(n)


def plural(n: int, word: str, words: str | None = None) -> str:
    return f"{number_word(n)} {word if n == 1 else (words or word + 's')}"


def date_parts(date: str | None) -> tuple[int | None, int | None, int | None]:
    """The year, month and day as numbers, each None unless it is ASCII digits
    (as ``file_stem`` reads them) and, for the month and day, in range."""
    y, m, d = date_fields(date or "")
    year = int(y) if is_number(y) else None
    month = int(m) if is_number(m) and 1 <= int(m) <= 12 else None
    day = int(d) if is_number(d) and 1 <= int(d) <= 31 and month else None
    return year, month, day


def format_date(date: str | None) -> str | None:
    """``2019.03.14`` as ``14 March 2019``; a partial date as far as it goes."""
    year, month, day = date_parts(date)
    if year is None:
        return None
    if month is None:
        return str(year)
    return f"{day} {MONTHS[month - 1]} {year}" if day else f"{MONTHS[month - 1]} {year}"


def format_time_control(value: str | None) -> str | None:
    """``600`` as ``10 min``, ``180+2`` as ``3 min + 2 s``; anything else as written."""
    value = known(value)
    if value is None:
        return None
    match = re.fullmatch(r"(\d+)(?:\+(\d+))?", value)
    if not match:
        return value
    base, inc = int(match[1]), match[2]
    text = f"{base // 60} min" if base % 60 == 0 else f"{base} s"
    return f"{text} + {int(inc)} s" if inc and int(inc) else text


def move_label(board: chess.Board, move: chess.Move, symbol: str = "") -> str:
    """``4. Qxf7#`` or ``3... Nf6``: the move with its number, from ``board``."""
    dots = "." if board.turn == chess.WHITE else "..."
    return f"{board.fullmove_number}{dots}{NBSP}{board.san(move)}{symbol}"


def line_text(board: chess.Board, moves: list[chess.Move]) -> str:
    """A line of moves in SAN with move numbers, from ``board``."""
    board = board.copy()
    parts = []
    for i, move in enumerate(moves):
        if board.turn == chess.WHITE:
            parts.append(f"{board.fullmove_number}.{NBSP}{board.san(move)}")
        elif i == 0:
            parts.append(f"{board.fullmove_number}...{NBSP}{board.san(move)}")
        else:
            parts.append(board.san(move))
        board.push(move)
    return " ".join(parts)


def format_eval(score: chess.engine.PovScore) -> str:
    white = score.white()
    if white.is_mate():
        mate = white.mate()
        return f"#{mate}" if mate > 0 else f"#−{-mate}"
    return f"{white.score() / 100:+.2f}".replace("-", "−")


def symbol_html(symbol: str) -> str:
    """A position symbol (``+−``) after a line, kept on the line's last line."""
    return f'{NBSP}<span class="sym">{symbol}</span>' if symbol else ""


def result_text(result: str, not_recorded: str) -> str:
    """``1-0`` as ``1–0``; ``*`` as the words ``not_recorded``, never a bare
    ``*``; any other value as written."""
    return RESULTS.get(result, not_recorded if result == NOT_RECORDED else result)


def percent(value: float) -> str:
    return f"{value:.0f}%"


def side(color: chess.Color) -> str:
    return "White" if color == chess.WHITE else "Black"


def moves_played(game: chess.pgn.Game) -> int:
    board = game.end().board()
    return board.fullmove_number - (1 if board.turn == chess.WHITE else 0)


def mate_clause(review: MoveReview) -> str:
    """``it allows mate in 2``, ``it lets a mate in 3 slip``, or nothing."""
    mover = review.mover
    before = review.score_before.pov(mover).mate() if review.score_before else None
    after = review.score_after.pov(mover).mate() if review.score_after else None
    if after is not None and after < 0 and not (before is not None and before < 0):
        return f"it allows mate in {-after}"
    if before is not None and before > 0 and not (after is not None and after > 0):
        return f"it lets a mate in {before} slip"
    return ""


def note_text(review: MoveReview) -> str:
    """The note after a graded move in the moves section."""
    _, kind, _ = GRADES[review.grade]
    clause = mate_clause(review)
    chances = f"{side(review.mover)}'s winning chances fall from {percent(review.before)} to {percent(review.after)}"
    return f"{kind}: {clause}; {chances}." if clause else f"{kind}: {chances}."


# --- the diagrams -------------------------------------------------------------


PIECE_CLASSES = {symbol: ("w" if symbol.isupper() else "b") + symbol.upper() for symbol in chess.svg.PIECES}


def piece_css() -> str:
    """One CSS rule per piece, each an SVG data URI: the one piece set every
    diagram shares (Colin M.L. Burnett's, as python-chess ships it)."""
    rules = []
    for symbol in "KQRBNPkqrbnp":
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45">{chess.svg.PIECES[symbol]}</svg>'
        data = svg.replace('"', "'").replace("#", "%23").replace("<", "%3C").replace(">", "%3E")
        rules.append(f'.{PIECE_CLASSES[symbol]}{{background-image:url("data:image/svg+xml,{data}")}}')
    return "\n".join(rules) + "\n"


def describe_position(board: chess.Board) -> str:
    """The pieces in words, for screen readers: ``White: Ke1, Qh5, pawns a2, b2``."""
    parts = []
    for color in (chess.WHITE, chess.BLACK):
        pieces = []
        for piece_type in (chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT):
            letter = chess.piece_symbol(piece_type).upper()
            pieces += [letter + chess.square_name(sq) for sq in board.pieces(piece_type, color)]
        pawns = [chess.square_name(sq) for sq in board.pieces(chess.PAWN, color)]
        if pawns:
            pieces.append(("pawn " if len(pawns) == 1 else "pawns ") + ", ".join(pawns))
        parts.append(f"{side(color)}: {', '.join(pieces) or 'nothing'}")
    return ". ".join(parts) + "."


def board_html(board: chess.Board, *, flipped: bool = False, highlight: Iterable[int] = (), label: str = "") -> str:
    """The position as an 8x8 grid of empty elements, one line per rank: the
    squares' colours are the board's background, each piece a class of the
    shared stylesheet, the coordinates ``data-`` attributes on the edge squares."""
    highlight = set(highlight)
    ranks = range(8) if flipped else range(7, -1, -1)
    files = list(range(7, -1, -1) if flipped else range(8))
    rows = []
    for row, rank in enumerate(ranks):
        cells = []
        for col, file in enumerate(files):
            square = chess.square(file, rank)
            classes = []
            piece = board.piece_at(square)
            if piece:
                classes.append(PIECE_CLASSES[piece.symbol()])
            if square in highlight:
                classes.append("hl")
            attrs = f' class="{" ".join(classes)}"' if classes else ""
            if col == 0:
                attrs += f' data-r="{rank + 1}"'
            if row == 7:
                attrs += f' data-f="{chess.FILE_NAMES[file]}"'
            cells.append(f"<i{attrs}></i>")
        rows.append("".join(cells))
    description = f"{label} {describe_position(board)}".strip()
    return f'<div class="board" role="img" aria-label="{attr(description)}">\n' + "\n".join(rows) + "\n</div>"


# --- the pages ----------------------------------------------------------------


@dataclass
class Article:
    """One game's page, with what the index and the navigation need."""

    item: CollectedGame
    reviews: list[MoveReview]
    analyzed: bool
    result: str  # the result shown (``shown_result``): recorded, from the board, presumed, or "*"

    @property
    def game(self) -> chess.pgn.Game:
        return self.item.game

    @property
    def stem(self) -> str:
        return file_stem(self.game, self.item.id)

    @property
    def filename(self) -> str:
        return f"{self.stem}.html"

    @property
    def white(self) -> str:
        return display_name(self.game.headers.get("White"))

    @property
    def black(self) -> str:
        return display_name(self.game.headers.get("Black"))

    @property
    def year(self) -> int | None:
        return date_parts(self.game.headers.get("Date"))[0]

    @property
    def title(self) -> str:
        return f"{self.white} vs. {self.black}" + (f", {self.year}" if self.year else "")

    @property
    def presumed(self) -> bool:
        """Whether the result shown was not recorded but read from the board
        or presumed from the analysis."""
        return self.result != self.game.headers.get("Result", NOT_RECORDED)

    @property
    def moments(self) -> list[MoveReview]:
        return [review for review in self.reviews if review.critical]


def page(title: str, body: str, *, root: str, site_title: str) -> str:
    home = "" if root == "" else f'<header class="top"><a href="{root}index.html">{esc(site_title)}</a></header>\n'
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="color-scheme" content="light dark">\n'
        f"{GENERATOR}\n"
        f"<title>{esc(title)}</title>\n"
        f'<link rel="stylesheet" href="{root}assets/style.css">\n'
        "</head>\n"
        "<body>\n"
        f"{home}"
        "<main>\n"
        f"{body}"
        "</main>\n"
        '<footer class="bottom">Made with pgn-postmortem. Analysis by Stockfish; '
        "pieces by Colin M.L. Burnett.</footer>\n"
        "</body>\n"
        "</html>\n"
    )


def lead_html(article: Article, thresholds: Thresholds) -> str:
    headers = article.game.headers
    date = format_date(headers.get("Date"))
    site, event, round_ = known(headers.get("Site")), known(headers.get("Event")), known(headers.get("Round"))
    where = ""
    if date:
        where += f" on {esc(date)}"
    if site:
        where += f" at {esc(site)}"
    first = f"<b>{esc(article.white)} vs. {esc(article.black)}</b> is a chess game"
    if where:
        first += f" played{where}"
    if event:
        first += f", in round {esc(round_)} of “{esc(event)}”" if round_ else f", part of “{esc(event)}”"
    if not date:
        first += "; its date is not recorded"
    sentences = [first + "."]

    n = moves_played(article.game)
    moves = plural(n, "move")
    board = article.game.end().board()
    result = article.result
    if result in ("1-0", "0-1"):
        winner = chess.WHITE if result == "1-0" else chess.BLACK
        name = article.white if winner == chess.WHITE else article.black
        how = "by checkmate " if board.is_checkmate() else ""
        sentences.append(f"{esc(name)}, with the {side(winner).lower()} pieces, won {how}in {moves}.")
    elif result == "1/2-1/2":
        how = " by stalemate" if board.is_stalemate() else ""
        sentences.append(f"It was drawn{how} after {moves}.")
    else:
        sentences.append(f"Its result is not recorded; the score stops after {moves}.")

    opening, eco = known(headers.get("Opening")), known(headers.get("ECO"))
    if opening:
        sentences.append(f"The opening was the {esc(opening)}" + (f" (ECO {esc(eco)})." if eco else "."))
    elif eco:
        sentences.append(f"The opening is classified as ECO {esc(eco)}.")

    threshold = f"{thresholds.mistake:g}"
    k = len(article.moments)
    if not article.analyzed:
        sentences.append("It has not been analyzed yet, so this article has no notes, critical moments or questions.")
    elif k:
        sentences.append(
            f"The engine found {plural(k, 'critical moment')}, where a single move cost at least {threshold} points "
            f"of winning chances; {'it is' if k == 1 else 'each is'} a “what would you play?” question below."
        )
    else:
        sentences.append(
            "The engine found no critical moment: no single move cost either side "
            f"{threshold} points of winning chances."
        )
    return f'<p class="lead">{" ".join(sentences)}</p>\n'


def infobox_html(article: Article) -> str:
    headers = article.game.headers
    end = article.game.end()
    last = f"after {move_label(end.parent.board(), end.move)}" if end.move else ""

    def player(color: str) -> str:
        name = esc(article.white if color == "White" else article.black)
        elo = known(headers.get(f"{color}Elo"))
        return f"{name} ({esc(elo)})" if elo else name

    rows = [
        ("White", player("White")),
        ("Black", player("Black")),
        ("Result", esc(result_text(article.result, "Not recorded"))),
        ("Date", esc(format_date(headers.get("Date")) or "Unknown")),
    ]
    for label, key in (("Event", "Event"), ("Round", "Round"), ("Site", "Site")):
        if value := known(headers.get(key)):
            rows.append((label, esc(value)))
    if value := format_time_control(headers.get("TimeControl")):
        rows.append(("Time control", esc(value)))
    opening, eco = known(headers.get("Opening")), known(headers.get("ECO"))
    if opening or eco:
        rows.append(("Opening", esc(" ".join(filter(None, [eco, opening])))))
    rows.append(("Moves", str(moves_played(article.game))))
    if value := known(headers.get("Termination")):
        rows.append(("Termination", esc(value)))
    rows.append(("Analysis", esc(headers[ANALYSIS_HEADER]) if article.analyzed else "Not analyzed yet"))
    if article.analyzed:
        links = ", ".join(f'<a href="#moment-{i}">{i}</a>' for i in range(1, len(article.moments) + 1))
        rows.append(("Critical moments", links or "None"))

    highlight = (end.move.from_square, end.move.to_square) if end.move else ()
    board = board_html(end.board(), highlight=highlight, label=f"The final position{' ' + last if last else ''}.")
    body = "\n".join(f"<tr><th>{label}</th><td>{value}</td></tr>" for label, value in rows)
    return (
        '<table class="infobox">\n'
        f"<caption>{esc(article.title)}</caption>\n"
        f'<tr><td colspan="2" class="figure">\n{board}\n'
        f'<div class="caption">The final position{" " + esc(last) if last else ""}</div></td></tr>\n'
        f"{body}\n"
        "</table>\n"
    )


def moment_html(review: MoveReview, number: int) -> str:
    board = review.board_before
    mover = side(review.mover)
    previous = review.node.parent
    if previous.move is not None:
        where = f"After {move_label(previous.parent.board(), previous.move)}"
        highlight = (previous.move.from_square, previous.move.to_square)
    else:
        where = "The starting position"
        highlight = ()
    caption = f"{where}, {mover} to move."
    diagram = board_html(board, flipped=review.mover == chess.BLACK, highlight=highlight, label=caption)

    played = move_label(board, review.node.move, review.symbol)
    best = engine_line(review.node.parent)
    if best and best[0][0] != review.node.move:
        moves, symbol = best
        answer = (
            f"<p><b>Best was {esc(move_label(board, moves[0]))}</b>, the engine's line being "
            f"{esc(line_text(board, moves))}{symbol_html(symbol)}. "
            f"With it, {mover}'s winning chances stay at {percent(review.before)}.</p>\n"
        )
    else:
        answer = f"<p>The analysis records no better move than {esc(played)}.</p>\n"
    _, kind, _ = GRADES[review.grade]
    clause = mate_clause(review)
    answer += (
        f"<p>In the game {mover} played <b>{esc(played)}</b>, {kind.lower()}"
        + (f": {clause}. " if clause else ". ")
        + f"{mover}'s winning chances fell from {percent(review.before)} to {percent(review.after)}."
    )
    refutation = engine_line(review.node)
    if refutation:
        moves, symbol = refutation
        answer += f" The refutation: {esc(line_text(review.node.board(), moves))}{symbol_html(symbol)}."
    answer += "</p>\n"
    return (
        f'<div class="moment" id="moment-{number}">\n'
        "<figure>\n"
        f"{diagram}\n"
        f"<figcaption>Critical moment {number}. {esc(caption)} <b>What would you play?</b></figcaption>\n"
        "</figure>\n"
        '<details class="answer">\n'
        "<summary>Show the answer</summary>\n"
        f"{answer}"
        "</details>\n"
        "</div>\n"
    )


def moves_html(article: Article) -> str:
    """The moves as paragraphs, with a note after each graded move, broken
    by a diagram and a question before each critical moment."""
    blocks: list[str] = []
    tokens: list[str] = []
    need_number = True
    number = 0

    def flush() -> None:
        if tokens:
            blocks.append(f'<p class="moves">{" ".join(tokens)}</p>\n')
            tokens.clear()

    for review in article.reviews:
        if review.critical:
            flush()
            number += 1
            blocks.append(moment_html(review, number))
            need_number = True
        board = review.board_before
        san = esc(board.san(review.node.move) + review.symbol)
        if board.turn == chess.WHITE:
            token = f"{board.fullmove_number}.{NBSP}{san}"
        elif need_number:
            token = f"{board.fullmove_number}...{NBSP}{san}"
        else:
            token = san
        need_number = False
        if review.grade:
            token = f"<b>{token}</b> <span class=\"note\">({esc(note_text(review))})</span>"
            need_number = True
        tokens.append(token)
    tokens.append(esc(result_text(article.result, "(result not recorded)")))
    flush()
    return "".join(blocks)


def conclusion_html(article: Article) -> str:
    game = article.game
    end = game.end()
    board = end.board()
    last = esc(move_label(end.parent.board(), end.move)) if end.move else "the start"
    result = article.result
    sentences = []
    winner = {"1-0": chess.WHITE, "0-1": chess.BLACK}.get(result)
    if board.is_checkmate():
        name = article.white if not board.turn == chess.WHITE else article.black
        sentences.append(f"{esc(name)} delivered checkmate with {last}.")
    elif board.is_stalemate():
        sentences.append(f"The game ended in stalemate after {last}.")
    elif board.is_insufficient_material():
        sentences.append(f"The game ended after {last}, with too little material left on the board for a mate.")
    else:
        if result == NOT_RECORDED:
            sentences.append(f"The score stops after {last}; the result was not recorded.")
        else:
            sentences.append(f"The game ended {esc(RESULTS.get(result, result))} after {last}.")
        final = article.reviews[-1] if article.reviews else None
        cp = white_cp(final.node)[0] if (final and article.analyzed) else None
        if cp is not None:
            white_chances = win_percent(cp)
            if winner is None:
                sentences.append(
                    f"The engine gives White {percent(white_chances)} winning chances in the final position."
                )
            else:
                name = esc(article.white if winner == chess.WHITE else article.black)
                chances = white_chances if winner == chess.WHITE else 100 - white_chances
                if chances >= 60:
                    sentences.append(f"{name} was clearly ahead: the engine gives {percent(chances)} winning chances.")
                elif article.presumed:  # a win presumed from these chances, so from the position itself
                    sentences.append(
                        f"{name} was ahead: the engine gives {percent(chances)} winning chances in the final position."
                    )
                else:
                    sentences.append(
                        f"The engine gives {name} only {percent(chances)} winning chances in the final position, "
                        "so the result came from outside the position on the board: a resignation, the clock or "
                        "an adjudication."
                    )
    if termination := known(game.headers.get("Termination")):
        sentences.append(f"The source records the termination as “{esc(termination)}”.")
    if article.analyzed:
        tallies = []
        for color in (chess.WHITE, chess.BLACK):
            counts = [
                plural(sum(1 for r in article.reviews if r.mover == color and r.grade == nag), name)
                for nag, (name, _, _) in GRADES.items()
            ]
            made = [count for count in counts if not count.startswith("no ")]
            tallies.append(f"{side(color)} made " + (" and ".join(made) if made else "none"))
        sentences.append(f"In the engine's grading, {tallies[0]}, and {tallies[1]}.")
    return f"<p>{' '.join(sentences)}</p>\n"


def pgn_text(item: CollectedGame) -> str:
    """The game as plain PGN: its headers and moves, without the analysis."""
    return format_game(strip_game(item.game, item.id))


def article_html(article: Article, previous: Article | None, following: Article | None, *, site_title: str,
                 thresholds: Thresholds) -> str:  # fmt: skip
    nav = []
    if previous:
        nav.append(f'<a rel="prev" href="{previous.filename}">← {esc(previous.title)}</a>')
    if following:
        nav.append(f'<a rel="next" href="{following.filename}">{esc(following.title)} →</a>')
    body = (
        "<article>\n"
        f"<h1>{esc(article.title)}</h1>\n"
        f"{infobox_html(article)}"
        f"{lead_html(article, thresholds)}"
        '<h2 id="game">The game</h2>\n'
        f"{moves_html(article)}"
        '<h2 id="conclusion">Conclusion</h2>\n'
        f"{conclusion_html(article)}"
        '<h2 id="pgn">PGN</h2>\n'
        f'<pre class="pgn">{esc(pgn_text(article.item))}</pre>\n'
        "</article>\n"
        + (f'<nav class="pager">\n{chr(10).join(nav)}\n</nav>\n' if nav else "")
    )
    return page(article.title, body, root="../", site_title=site_title)


def index_html(articles: list[Article], site_title: str) -> str:
    years: dict[int | None, list[Article]] = {}
    for article in articles:
        years.setdefault(article.year, []).append(article)
    dated = sorted(year for year in years if year is not None)

    def anchor(year: int | None) -> str:
        return f"y{year}" if year is not None else "undated"

    def heading(year: int | None) -> str:
        return str(year) if year is not None else "Undated"

    order = [*dated, *([None] if None in years else [])]
    span = f"from {dated[0]} to {dated[-1]}" if len(dated) > 1 else (f"from {dated[0]}" if dated else "")
    undated = len(years.get(None, []))
    summary = f"{plural(len(articles), 'game').capitalize()}"
    if span:
        summary += f" {span}"
    if undated and dated:
        summary += f" ({number_word(undated)} undated)"
    summary += (
        ". Every game has its own article. In the analyzed ones, each critical moment is a question, "
        "“what would you play?”, with the answer hidden until you tap it."
    )
    parts = [f"<h1>{esc(site_title)}</h1>\n", f'<p class="lead">{summary}</p>\n']
    if len(order) > 1:
        links = " ".join(f'<a href="#{anchor(year)}">{heading(year)}</a>' for year in order)
        parts.append(f'<nav class="years">{links}</nav>\n')
    for year in order:
        parts.append(f'<section id="{anchor(year)}">\n<h2>{heading(year)}</h2>\n<ol class="games">\n')
        for article in years[year]:
            headers = article.game.headers
            meta = [format_date(headers.get("Date")) or "Undated"]
            if event := known(headers.get("Event")):
                meta.append(event)
            if article.analyzed:
                k = len(article.moments)
                meta.append(f"{number_word(k)} question{'' if k == 1 else 's'}" if k else "no questions")
            else:
                meta.append("not analyzed")
            parts.append(
                f'<li><a href="games/{article.filename}">{esc(article.white)} vs. {esc(article.black)}</a> '
                f'<span class="result">{esc(result_text(article.result, "result not recorded"))}</span>'
                f'<span class="meta">{esc(" · ".join(meta))}</span></li>\n'
            )
        parts.append("</ol>\n</section>\n")
    return page(site_title, "".join(parts), root="", site_title=site_title)


STYLE = """\
/* pgn-postmortem site. Mobile first; light or dark as the OS says. */
:root {
  --bg: #ffffff; --fg: #202122; --muted: #54595d; --link: #3366cc; --rule: #a2a9b1;
  --box: #f8f9fa; --note: #54595d; --answer: #eaf3ff;
  --light: #f0d9b5; --dark: #b58863; --hl: rgba(255, 213, 0, .45);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #101418; --fg: #e8eaed; --muted: #a8adb3; --link: #8ab4f8; --rule: #3c4043;
    --box: #1b2026; --note: #b0b6bd; --answer: #17263a;
    --light: #d8c3a0; --dark: #9c7453; --hl: rgba(255, 213, 0, .4);
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0; background: var(--bg); color: var(--fg);
  font: 1rem/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
a { color: var(--link); text-decoration: none; }
a:hover, a:focus { text-decoration: underline; }
main { max-width: 52rem; margin: 0 auto; padding: 0 1rem 2rem; }
.top { border-bottom: 1px solid var(--rule); padding: .6rem 1rem; font-weight: 600; }
.bottom { max-width: 52rem; margin: 0 auto; padding: 1rem; color: var(--muted); font-size: .85rem;
  border-top: 1px solid var(--rule); }
h1, h2 { font-family: Georgia, "Linux Libertine", "Times New Roman", serif; font-weight: normal; line-height: 1.25; }
h1 { font-size: 1.8rem; margin: 1rem 0 .5rem; border-bottom: 1px solid var(--rule); padding-bottom: .2rem; }
h2 { font-size: 1.4rem; margin: 1.6rem 0 .5rem; border-bottom: 1px solid var(--rule); padding-bottom: .1rem; }
.lead { margin-top: 0; }
.moves { font-weight: 600; overflow-wrap: anywhere; }
.moves b { font-weight: 700; }
.note { font-weight: normal; font-style: italic; color: var(--note); }
.infobox { width: 100%; margin: 0 0 1rem; border: 1px solid var(--rule); background: var(--box);
  border-collapse: collapse; font-size: .9rem; line-height: 1.4; }
.infobox caption { font-weight: bold; font-size: 1.05rem; padding: .4rem; }
.infobox th, .infobox td { text-align: left; vertical-align: top; padding: .25rem .5rem; }
.infobox th { white-space: nowrap; }
.infobox .figure { padding: .5rem; }
.infobox .board { max-width: 100%; }
.caption { font-size: .85rem; color: var(--muted); text-align: center; margin-top: .3rem; }
@media (min-width: 44rem) {
  .infobox { float: right; clear: right; width: 20rem; margin: 0 0 1rem 1.2rem; }
}
h2 { overflow: hidden; }
article::after { content: ""; display: block; clear: both; }
.sym { white-space: nowrap; }
.board {
  display: grid; grid-template-columns: repeat(8, 1fr); aspect-ratio: 1; width: 100%; max-width: 24rem;
  background: repeating-conic-gradient(var(--dark) 0 25%, var(--light) 0 50%) 0 0 / 25% 25%;
  border: 1px solid var(--rule); font: 600 .65rem/1 system-ui, sans-serif; margin: 0 auto;
}
.board i { position: relative; background-size: 100% 100%; background-repeat: no-repeat; }
.board i.hl { background-color: var(--hl); }
.board i[data-r]::before, .board i[data-f]::after { position: absolute; color: #5b4632; opacity: .8; }
.board i[data-r]::before { content: attr(data-r); top: 3%; left: 4%; }
.board i[data-f]::after { content: attr(data-f); bottom: 3%; right: 6%; }
figure { margin: 1rem 0 .5rem; }
figcaption { text-align: center; font-size: .9rem; color: var(--muted); margin-top: .4rem; }
figcaption b { color: var(--fg); }
.moment { margin: 1.2rem 0; }
.answer { display: flow-root; background: var(--answer); border-radius: .4rem; padding: .2rem .8rem; max-width: 36rem;
  margin: 0 auto; }
.answer summary { cursor: pointer; font-weight: 600; padding: .5rem 0; min-height: 2.75rem; display: flex;
  align-items: center; }
.answer summary::before { content: "▸"; margin-right: .4rem; }
.answer[open] summary::before { content: "▾"; }
.answer summary::-webkit-details-marker { display: none; }
.answer summary { list-style: none; }
.pgn { white-space: pre-wrap; overflow-wrap: anywhere; background: var(--box); border: 1px solid var(--rule);
  padding: .6rem; font-size: .85rem; }
.pager { display: flex; flex-wrap: wrap; justify-content: space-between; gap: .5rem 1rem;
  border-top: 1px solid var(--rule); padding-top: .8rem; margin-top: 1.5rem; }
.years { display: flex; flex-wrap: wrap; gap: .3rem 1rem; margin: 0 0 1rem; }
.years a { padding: .3rem 0; }
.games { list-style: none; padding: 0; margin: 0; }
.games li { padding: .5rem 0; border-bottom: 1px solid var(--rule); }
.games .result { margin-left: .5rem; font-weight: 600; }
.games .meta { display: block; color: var(--muted); font-size: .85rem; }
/* The piece set (Colin M.L. Burnett's, as python-chess ships it), shared by every diagram. */
"""


@dataclass
class SiteReport:
    articles: list[Path] = field(default_factory=list)
    analyzed: int = 0
    critical_moments: int = 0
    removed: list[Path] = field(default_factory=list)

    def summary(self, out_dir: str | Path) -> str:
        return (
            f"Wrote {len(self.articles)} article(s) to {out_dir}: {self.analyzed} analyzed, "
            f"{len(self.articles) - self.analyzed} not analyzed yet, {self.critical_moments} critical moment(s)."
        )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))  # "\n" line ends on every OS, for byte-for-byte golden files


def is_generated(path: Path) -> bool:
    """Whether ``path`` is a page this builder wrote: it carries the
    ``GENERATOR`` line in its head, where ``page`` puts it."""
    with path.open("rb") as handle:
        head = handle.read(1024)
    return f"\n{GENERATOR}\n".encode() in head


def build_site(
    games: Iterable[CollectedGame],
    out_dir: str | Path,
    *,
    title: str = "Games",
    thresholds: Thresholds = LICHESS_THRESHOLDS,
    presume_threshold: float = PRESUME_THRESHOLD,
) -> SiteReport:
    """Write the site for ``games`` (a ``Collection``, or any iterable of
    ``CollectedGame``) to ``out_dir``: ``index.html``, ``assets/style.css``
    and one ``games/<date>-<id>.html`` per game, in date order.

    Games read with ``Collection.read(..., keep_analysis=True)`` from the
    analysis step's output get notes, critical moments and questions; any
    other game gets an article without them. A page that an earlier build
    wrote in ``out_dir/games/`` for a game no longer in ``games`` is removed,
    whatever its name, so the site has one article per game; a file there
    that the builder did not write (no ``GENERATOR`` line) is never touched.
    The output depends only on the games and the options: building twice
    gives the same bytes.

    A game whose result was not recorded is shown with the result
    ``shown_result`` gives (the rule is in the module docstring):
    ``presume_threshold`` is the winning chances, in percent, at which the
    analysis makes it a win, 70 by default. A value below 55 or above 95
    raises ``ValueError`` before anything is written. The games are not
    changed.
    """
    check_presume_threshold(presume_threshold)
    out_dir = Path(out_dir)
    articles = []
    for item in games:
        analyzed = is_analyzed(item.game)
        result = shown_result(item.game, presume_threshold)
        articles.append(Article(item, review_moves(item.game, thresholds), analyzed, result))
    articles.sort(key=lambda article: article.stem)

    report = SiteReport()
    write_text(out_dir / "assets" / "style.css", STYLE + piece_css())
    for i, article in enumerate(articles):
        previous = articles[i - 1] if i > 0 else None
        following = articles[i + 1] if i + 1 < len(articles) else None
        path = out_dir / "games" / article.filename
        write_text(path, article_html(article, previous, following, site_title=title, thresholds=thresholds))
        report.articles.append(path)
        report.analyzed += article.analyzed
        report.critical_moments += len(article.moments)
    write_text(out_dir / "index.html", index_html(articles, title))

    written = {path.name for path in report.articles}
    for path in sorted((out_dir / "games").glob("*.html")):
        if path.name not in written and is_generated(path):
            path.unlink()
            report.removed.append(path)
    return report
