"""The static site: one Wikipedia-style article per game, and an index of the
games by year.

The site is HTML and one stylesheet, with a small script inlined in every
page for the optional reading history (below), written to an output
directory::

    index.html              the games by year, each linking to its article
    games/<date>-<id>.html  one article per game, named like the game's PGN file
    quiz.html               the player's own critical moments, worst first
                            (below), when the site has a player
    assets/style.css        the layout, the colours (light or dark, as the OS
                            says) and the one piece set every diagram uses

Every link within the site is relative and names a file (``../index.html``,
not ``../``), so the site works from a web server, from a folder copied to a
phone, and from ``file://``. The only absolute links are the two lichess
links of an article (below), which open in a new tab, and lichess is reached
only when the reader taps one. Nothing is loaded from the network. The only
JavaScript is the optional reading history (below), inlined in every page;
without it the pages read the same.

An article has an infobox (the players, the event, the result, the final
position), a lead paragraph, the moves with notes, a diagram and a question at
each critical moment, a conclusion and the game's PGN. All prose comes from
templates (the LLM is F-2 in ``ROADMAP.md``).

**The lichess links** (ROADMAP.md, F-10). Under the final position, the
infobox links "Open this game on lichess" to lichess's analysis board with
the game's moves, ``https://lichess.org/analysis/pgn/<moves>``: the mainline
in SAN without move numbers and without the check and mate signs (a ``+`` in
the path reads as a space), separated by spaces, URL-encoded
(``lichess_game_url``). A game that does not start from the standard position
(a ``FEN`` header that sets up another one) or has no moves has no game link.
Inside each critical moment's hidden answer, "Analyze this position on
lichess" links to ``https://lichess.org/analysis/<FEN>``, the question's
position (before the move), with the FEN's spaces written as ``_``
(``lichess_position_url``); it sits in the answer because an engine on the
question's position gives the answer away. Both links carry
``target="_blank"`` and ``rel="noopener noreferrer"``, with or without the
reading history.

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
lost at least ``thresholds.mistake`` points (20 by default), a mistake or a
blunder, or an outcome swing** (below). Other graded moves get a note but no
diagram. The first move of a game has no evaluation before it (the analysis
step does not write the start position's), so it is never graded; from the
standard start no single move loses that much.

**Outcome swings** (ROADMAP.md, F-6). Each analyzed position gets an
*expected outcome* from White's winning chances after the move: White winning
at ``outcome_bands[1]`` (60 by default) or more, Black winning at
``outcome_bands[0]`` (40) or less, level in between. A move is an outcome
swing when all three hold:

1. it makes the expected outcome worse for the side that played it (winning
   to level, level to losing, or winning to losing);
2. it cost that side at least ``thresholds.inaccuracy`` points (10 by
   default), so every swing is a graded move;
3. a better move exists: the engine's first choice in the position before
   the move differs from the move played. The first choice is the first move
   of any engine line stored at that position: the move's own better line,
   or the previous move's refutation, which is the engine's line from the
   same position. With no line stored there the move is not a swing either.
   With the thresholds the analysis used, no line there means the engine's
   first choice was the move played (the analysis stores a graded move's
   better line whenever the engine's first choice differs); with a lower
   inaccuracy threshold than the analysis used, a move graded between the
   two thresholds may have no line of its own, and then nothing is known
   about a better move. Either way there is no better move to show.

A swing is a critical moment even when it cost less than
``thresholds.mistake``; a move that is both is one moment. The note on a
swing, in the moves and in the answer, says how the expected result changed
("an inaccuracy that turned a level game into a losing one"). A move that
changed the band without meeting all three conditions gets no such words.

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

**The quiz** (ROADMAP.md, F-9). ``build_site`` takes the player's name and
aliases (``player``, ``aliases``), matched as ``Collection.read`` matches them:
letter case and surrounding spaces are ignored. A site without a player (no
name given, or only blank ones) has no quiz page and no link to it, since no
move is the player's own; a rebuild without a player removes the
``quiz.html`` an earlier build wrote (it carries the generator marker,
``GENERATOR``), and never a ``quiz.html`` without it. With a player, the
index links at its top to ``quiz.html``, which lists every critical moment
(the rules above) played by the player, in every game where White or Black
is one of the player's names (both sides when both are), and none of the
opponents'. They are ordered by the winning chances the move lost (the
exact value, not the rounded one shown), the most first; ties go by the
game's position in the index, then the article's file name, then move
order. Each line shows its rank, the move played (``30... Rd2``), the points
it lost and the game (its date and the opponent), and links to the
question in its article (``games/<file>.html#moment-N``); the page shows no
diagram and no answer. A player without a critical moment of their own gets
a quiz page that says so.

**The reading history** (ROADMAP.md, F-8). Every page carries, inline and
byte for byte, the script ``pgn_postmortem/static/history.js`` (package
data). In the reader's browser only (``localStorage``, never sent anywhere)
it records a game as viewed when its article is opened, and an answer as
revealed when its ``<details class="answer">`` is opened, keyed by its move
(``31b``: Black's 31st), not by the moment's number, which changes when the
rules for critical moments do. The index shows a "Recently viewed" list (the
latest 10 of its own games, newest first), a mark on each viewed game with
how many of its current questions' answers were revealed ("2/4"), and a
"Clear history" button that removes this site's history after a
confirmation. The quiz page marks "answered" each question whose answer was
revealed, keeping the order; it has no button of its own, and the index's
clears its marks too. For it the pages carry these ``data-`` attributes and
no others: ``data-site`` on ``<html>`` (the site key), ``data-game`` on the
article (the ``PostmortemId``), ``data-move`` on each answer,
``data-game`` and ``data-moves`` (the moves of its current questions) on
each game in the index, and ``data-game`` and ``data-move`` on each line of
the quiz. Every stored key starts with ``pgn-postmortem:`` and
the site key, which the pages carry so that sites sharing an origin (all
GitHub Pages sites of one user, or ``file://`` pages in some browsers) keep
separate histories; by default it is derived from the title
(``default_site_key``), so two sites with the same title share one. The
index's history section is in the HTML with the ``hidden`` attribute, and
only the script shows it; its styling is in the script too, added when it
shows something, so ``assets/style.css`` is the same with or without the
history. With scripts off, or with no storage, the pages read as they would
without the history. ``build_site(..., history=False)`` leaves out the
script, the section and the ``data-`` attributes.
"""

from __future__ import annotations

import hashlib
import html
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from urllib.parse import quote

import chess
import chess.engine
import chess.pgn
import chess.svg

from pgn_postmortem.analysis import LICHESS_THRESHOLDS, MATE_SCORE, Thresholds, classify, win_percent
from pgn_postmortem.collection import (
    ANALYSIS_HEADER,
    CollectedGame,
    Collection,
    date_fields,
    file_stem,
    format_game,
    is_number,
    player_names,
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
# White's winning chances (%) at or below which Black is winning, and at or above which White is. The owner
# changed the shaping's 35/65 to 40/60 on 2026-09-25, so that the example game's 15. Nxc5 (47% -> 37%) is a question.
OUTCOME_BANDS = (40.0, 60.0)
OUTCOMES = ("losing", "level", "winning")  # the expected outcome for one side, from worst to best
CHANGES = {
    ("winning", "level"): "a winning game into a level one",
    ("level", "losing"): "a level game into a losing one",
    ("winning", "losing"): "a winning game into a losing one",
}
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]  # fmt: skip
NUMBER_WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
NBSP = "\u00a0"  # between a move number and its move, so a line never breaks between them
GENERATOR = '<meta name="generator" content="pgn-postmortem">'  # in every page; marks what a rebuild may delete
QUIZ_PAGE = "quiz.html"  # the quiz list of the player's own mistakes (ROADMAP.md, F-9)
SITE_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")  # the reading history's site key (ROADMAP.md, F-8)
LICHESS_ANALYSIS = "https://lichess.org/analysis/"  # lichess's analysis board (ROADMAP.md, F-10)
NEW_TAB = 'target="_blank" rel="noopener noreferrer"'  # the lichess links open in a new tab, so the book stays open


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
    # the mover's expected outcome before and after the move ("losing", "level", "winning"), when analyzed
    outcomes: tuple[str, str] | None = None
    swing: bool = False  # an outcome swing (the rule is in the module docstring)

    @property
    def mover(self) -> chess.Color:
        return not self.node.turn()

    @property
    def board_before(self) -> chess.Board:
        return self.node.parent.board()

    @property
    def symbol(self) -> str:
        return GRADES[self.grade][2] if self.grade else ""

    @property
    def change(self) -> str:
        """``turned a level game into a losing one`` for a swing, else nothing."""
        return f"turned {CHANGES[self.outcomes]}" if self.swing else ""

    @property
    def loss(self) -> float:
        """The winning chances the move cost the mover, exactly as graded
        (0 when it gained, or without analysis)."""
        if self.before is None or self.after is None:
            return 0.0
        return max(self.before - self.after, 0.0)


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


def check_outcome_bands(bands: object) -> tuple[float, float]:
    """``bands`` as ``(lower, upper)``; raise ``ValueError`` unless both are
    finite numbers with 0 < lower < 50 < upper < 100."""
    try:
        lower, upper = bands
    except (TypeError, ValueError):
        lower = upper = None
    numbers = all(isinstance(value, int | float) and not isinstance(value, bool) for value in (lower, upper))
    if not (numbers and 0 < lower < 50 < upper < 100):  # also rejects NaN and infinities
        raise ValueError(
            "outcome_bands must be two finite numbers (lower, upper), White's winning chances in percent, "
            f"with 0 < lower < 50 < upper < 100; not {bands!r}"
        )
    return float(lower), float(upper)


def expected_outcome(white: float, bands: tuple[float, float], color: chess.Color) -> str:
    """``winning``, ``level`` or ``losing`` for ``color``, from White's winning
    chances ``white``: White is winning at ``bands[1]`` or more, Black at
    ``bands[0]`` or less."""
    lower, upper = bands
    leader = chess.WHITE if white >= upper else chess.BLACK if white <= lower else None
    return "level" if leader is None else "winning" if leader == color else "losing"


def has_better_move(node: chess.pgn.ChildNode) -> bool:
    """Whether the engine's first choice before ``node``'s move differs from
    it: some engine line is stored at the position before the move, and none
    starts with the move played (the rule is in the module docstring)."""
    first_choices = {line.move for line in node.parent.variations[1:]}
    return bool(first_choices) and node.move not in first_choices


def review_moves(
    game: chess.pgn.Game,
    thresholds: Thresholds = LICHESS_THRESHOLDS,
    outcome_bands: tuple[float, float] = OUTCOME_BANDS,
) -> list[MoveReview]:
    """Every mainline move with its grade, its expected outcomes, and whether
    it is an outcome swing and a critical moment (the rules are in the module
    docstring). An invalid ``outcome_bands`` raises ``ValueError``."""
    bands = check_outcome_bands(outcome_bands)
    analyzed = is_analyzed(game)
    reviews = []
    cp_before: int | None = None
    score_before: chess.engine.PovScore | None = None
    for node in game.mainline():
        cp_after, score_after = white_cp(node) if analyzed else (None, None)
        before = after = outcomes = None
        grade, critical, swing = None, False, False
        if cp_before is not None and cp_after is not None:
            mover = not node.turn()
            white_before, white_after = win_percent(cp_before), win_percent(cp_after)
            before, after = white_before, white_after
            if mover == chess.BLACK:
                before, after = 100 - before, 100 - after
            loss = max(before - after, 0.0)
            grade = classify(loss, thresholds)
            # the bands are read from White's chances as computed, so an edge set to a position's exact value holds
            outcomes = (expected_outcome(white_before, bands, mover), expected_outcome(white_after, bands, mover))
            # With the clamped ``loss`` at the floor the mover's chances fell, so its band can only stay or
            # worsen: the first condition overlaps the second. Both are kept, as the rule states them.
            swing = (
                OUTCOMES.index(outcomes[1]) < OUTCOMES.index(outcomes[0])
                and loss >= thresholds.inaccuracy
                and has_better_move(node)
            )
            critical = loss >= thresholds.mistake or swing
        reviews.append(MoveReview(node, before, after, score_before, score_after, grade, critical, outcomes, swing))
        cp_before, score_before = cp_after, score_after
    return reviews


def critical_moments(
    game: chess.pgn.Game,
    thresholds: Thresholds = LICHESS_THRESHOLDS,
    outcome_bands: tuple[float, float] = OUTCOME_BANDS,
) -> list[MoveReview]:
    """The game's critical moments, in move order: the moves that lost the
    mover at least ``thresholds.mistake`` points of winning chances, and the
    outcome swings."""
    return [review for review in review_moves(game, thresholds, outcome_bands) if review.critical]


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
    """``one move``, ``two moves``; a consonant and ``y`` become ``ies``
    (``two inaccuracies``)."""
    if words is None:
        words = word[:-1] + "ies" if word.endswith("y") and word[-2:-1] not in ("", *"aeiou") else word + "s"
    return f"{number_word(n)} {word if n == 1 else words}"


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


def grade_words(review: MoveReview) -> str:
    """``A mistake``, or for an outcome swing ``A mistake that turned a level
    game into a losing one``."""
    _, kind, _ = GRADES[review.grade]
    return f"{kind} that {review.change}" if review.swing else kind


def note_text(review: MoveReview) -> str:
    """The note after a graded move in the moves section."""
    kind = grade_words(review)
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
    """The position as an 8x8 grid of empty elements, one line per rank. Each
    cell draws its own square: its colour (``l`` or ``d``), its piece (a class
    of the shared stylesheet) and the highlight (``hl``), so they share one box
    at any size; the board draws no square pattern of its own, which would
    round differently from the cells when a square is not a whole number of
    pixels. The coordinates are ``data-`` attributes on the edge squares."""
    highlight = set(highlight)
    ranks = range(8) if flipped else range(7, -1, -1)
    files = list(range(7, -1, -1) if flipped else range(8))
    rows = []
    for row, rank in enumerate(ranks):
        cells = []
        for col, file in enumerate(files):
            square = chess.square(file, rank)
            classes = ["l" if chess.BB_LIGHT_SQUARES & chess.BB_SQUARES[square] else "d"]
            piece = board.piece_at(square)
            if piece:
                classes.append(PIECE_CLASSES[piece.symbol()])
            if square in highlight:
                classes.append("hl")
            attrs = f' class="{" ".join(classes)}"'
            if col == 0:
                attrs += f' data-r="{rank + 1}"'
            if row == 7:
                attrs += f' data-f="{chess.FILE_NAMES[file]}"'
            cells.append(f"<i{attrs}></i>")
        rows.append("".join(cells))
    description = f"{label} {describe_position(board)}".strip()
    return f'<div class="board" role="img" aria-label="{attr(description)}">\n' + "\n".join(rows) + "\n</div>"


# --- the lichess links (ROADMAP.md, F-10) --------------------------------------


def lichess_game_url(game: chess.pgn.Game) -> str | None:
    """The game on lichess's analysis board: ``LICHESS_ANALYSIS`` ``pgn/``
    and the mainline moves in SAN, without move numbers and without the check
    and mate signs (``+`` in a path reads as a space), separated by spaces and
    URL-encoded (``e4%20e5%20Qh5``). None for a game that does not start from
    the standard position, or has no moves."""
    board = game.board()
    if board.fen() != chess.STARTING_FEN or game.next() is None:
        return None
    sans = []
    for move in game.mainline_moves():
        sans.append(board.san(move).rstrip("+#"))
        board.push(move)
    return f"{LICHESS_ANALYSIS}pgn/{quote(' '.join(sans), safe='')}"


def lichess_position_url(board: chess.Board) -> str:
    """The position on lichess's analysis board: ``LICHESS_ANALYSIS`` and
    its FEN, with the spaces written as ``_``."""
    return LICHESS_ANALYSIS + quote(board.fen().replace(" ", "_"), safe="/")


def lichess_link(url: str, text: str) -> str:
    return f'<a href="{attr(url)}" {NEW_TAB}>{esc(text)}</a>'


# --- the reading history ------------------------------------------------------


@dataclass(frozen=True)
class History:
    """What the pages carry for the reading history: the site key, and the
    script that every page inlines (the rule is in the module docstring)."""

    site_key: str
    script: str


HISTORY_SECTION = (
    '<section id="history" class="history" hidden>\n'
    "<h2>Recently viewed</h2>\n"
    '<ol id="history-recent" class="games"></ol>\n'
    '<p><button type="button" id="history-clear">Clear history</button> '
    '<span class="note">Kept in this browser only.</span></p>\n'
    "</section>\n"
)


def history_script() -> str:
    """The reading-history script, ``pgn_postmortem/static/history.js``, as
    its bytes read (package data)."""
    return (resources.files("pgn_postmortem") / "static" / "history.js").read_bytes().decode("utf-8")


def default_site_key(title: str) -> str:
    """The site key for a site titled ``title``: its words in ASCII, lower
    case, joined by ``-`` (at most 40 characters), then the first 8 hex
    digits of the title's SHA-256, so that only the same title gives the same
    key: ``Games of Ada Example`` is ``games-of-ada-example-`` and 8 digits."""
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii").lower()
    words = "-".join(re.findall(r"[a-z0-9]+", ascii_title))[:40].strip("-")
    digest = hashlib.sha256(title.encode("utf-8")).hexdigest()[:8]
    return f"{words}-{digest}" if words else digest


def check_site_key(key: object) -> str:
    """``key``, or ``ValueError`` unless it is 1 to 64 ASCII letters, digits,
    ``.``, ``_`` and ``-``, starting with a letter or a digit."""
    if not (isinstance(key, str) and SITE_KEY.fullmatch(key)):
        raise ValueError(
            "site_key must be 1 to 64 ASCII letters, digits, '.', '_' or '-', starting with a letter or a digit; "
            f"not {key!r}"
        )
    return key


def data(history: History | None, **values: str) -> str:
    """`` data-game="…"`` and the like for the reading history, or nothing
    when the pages are built without it."""
    if history is None:
        return ""
    return "".join(f' data-{name}="{attr(value)}"' for name, value in values.items())


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


def page(title: str, body: str, *, root: str, site_title: str, history: History | None = None,
         home: bool | None = None) -> str:  # fmt: skip
    """A whole page. ``home`` puts the link to the index at the top: by
    default on every page but the index (``root`` is empty only there and on
    the quiz page, which asks for it)."""
    home = root != "" if home is None else home
    home = f'<header class="top"><a href="{root}index.html">{esc(site_title)}</a></header>\n' if home else ""
    return (
        "<!DOCTYPE html>\n"
        f'<html lang="en"{data(history, site=history.site_key) if history else ""}>\n'
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
        + (f"<script>{history.script}</script>\n" if history else "")
        + "</body>\n"
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
            f"of winning chances or changed the expected result; {'it is' if k == 1 else 'each is'} a “what would "
            "you play?” question below."
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
    # under the final position; none for a set-up position or a game without moves
    game_url = lichess_game_url(article.game)
    lichess = f'\n<div class="lichess">{lichess_link(game_url, "Open this game on lichess")}</div>' if game_url else ""

    highlight = (end.move.from_square, end.move.to_square) if end.move else ()
    board = board_html(end.board(), highlight=highlight, label=f"The final position{' ' + last if last else ''}.")
    body = "\n".join(f"<tr><th>{label}</th><td>{value}</td></tr>" for label, value in rows)
    return (
        '<table class="infobox">\n'
        f"<caption>{esc(article.title)}</caption>\n"
        f'<tr><td colspan="2" class="figure">\n{board}\n'
        f'<div class="caption">The final position{" " + esc(last) if last else ""}</div>{lichess}</td></tr>\n'
        f"{body}\n"
        "</table>\n"
    )


def move_key(board: chess.Board) -> str:
    """The move about to be played on ``board`` as the reading history keys
    it: ``31b`` for Black's 31st move, ``4w`` for White's 4th."""
    return f"{board.fullmove_number}{'w' if board.turn == chess.WHITE else 'b'}"


def moment_html(review: MoveReview, number: int, history: History | None = None) -> str:
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
    kind = grade_words(review)
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
    # inside the hidden answer, since an engine on the question's position gives the answer away
    position = lichess_link(lichess_position_url(board), "Analyze this position on lichess")
    answer += f'<p class="lichess">{position}</p>\n'
    return (
        f'<div class="moment" id="moment-{number}">\n'
        "<figure>\n"
        f"{diagram}\n"
        f"<figcaption>Critical moment {number}. {esc(caption)} <b>What would you play?</b></figcaption>\n"
        "</figure>\n"
        f'<details class="answer"{data(history, move=move_key(board))}>\n'
        "<summary>Show the answer</summary>\n"
        f"{answer}"
        "</details>\n"
        "</div>\n"
    )


def moves_html(article: Article, history: History | None = None) -> str:
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
            blocks.append(moment_html(review, number, history))
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
                 thresholds: Thresholds, history: History | None = None) -> str:  # fmt: skip
    nav = []
    if previous:
        nav.append(f'<a rel="prev" href="{previous.filename}">← {esc(previous.title)}</a>')
    if following:
        nav.append(f'<a rel="next" href="{following.filename}">{esc(following.title)} →</a>')
    body = (
        f"<article{data(history, game=article.item.id)}>\n"
        f"<h1>{esc(article.title)}</h1>\n"
        f"{infobox_html(article)}"
        f"{lead_html(article, thresholds)}"
        '<h2 id="game">The game</h2>\n'
        f"{moves_html(article, history)}"
        '<h2 id="conclusion">Conclusion</h2>\n'
        f"{conclusion_html(article)}"
        '<h2 id="pgn">PGN</h2>\n'
        f'<pre class="pgn">{esc(pgn_text(article.item))}</pre>\n'
        "</article>\n"
        + (f'<nav class="pager">\n{chr(10).join(nav)}\n</nav>\n' if nav else "")
    )
    return page(article.title, body, root="../", site_title=site_title, history=history)


def index_years(articles: list[Article]) -> list[tuple[int | None, list[Article]]]:
    """The index's sections: the years in order (as numbers), then the
    undated games; in each, the articles in the order given (by file name,
    as ``build_site`` sorts them)."""
    years: dict[int | None, list[Article]] = {}
    for article in articles:
        years.setdefault(article.year, []).append(article)
    dated = sorted(year for year in years if year is not None)
    return [(year, years[year]) for year in [*dated, *([None] if None in years else [])]]


def index_order(articles: list[Article]) -> list[Article]:
    """The articles in the order the index lists them."""
    return [article for _, section in index_years(articles) for article in section]


@dataclass(frozen=True)
class Quiz:
    """What the index needs to link to the quiz page: its title and its
    number of questions."""

    title: str
    questions: int


def index_html(articles: list[Article], site_title: str, history: History | None = None,
               quiz: Quiz | None = None) -> str:  # fmt: skip
    sections = index_years(articles)
    dated = [year for year, _ in sections if year is not None]

    def anchor(year: int | None) -> str:
        return f"y{year}" if year is not None else "undated"

    def heading(year: int | None) -> str:
        return str(year) if year is not None else "Undated"

    years = dict(sections)
    order = [year for year, _ in sections]
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
    if quiz:
        count = plural(quiz.questions, "question") if quiz.questions else "no questions"
        parts.append(f'<p class="quiz-link"><a href="{QUIZ_PAGE}">{esc(quiz.title)}</a>: {count}.</p>\n')
    if history:
        parts.append(HISTORY_SECTION)
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
            questions = " ".join(move_key(review.board_before) for review in article.moments)
            parts.append(
                f'<li{data(history, game=article.item.id, moves=questions)}><a href="games/{article.filename}">'
                f"{esc(article.white)} vs. {esc(article.black)}</a> "
                f'<span class="result">{esc(result_text(article.result, "result not recorded"))}</span>'
                f'<span class="meta">{esc(" · ".join(meta))}</span></li>\n'
            )
        parts.append("</ol>\n</section>\n")
    return page(site_title, "".join(parts), root="", site_title=site_title, history=history)


# --- the quiz (ROADMAP.md, F-9) -----------------------------------------------------


@dataclass(frozen=True)
class QuizEntry:
    """One line of the quiz: a critical moment that the player played."""

    article: Article
    review: MoveReview
    number: int  # the moment's number in its article, as in its anchor ``moment-N``
    loss: float  # the winning chances the move cost, exactly
    position: int  # the game's position in the index, from 0
    filename: str  # the article's file name
    ply: int  # the move's place in its game

    def order(self) -> tuple[float, int, str, int]:
        """The quiz's order: the most points lost first, then the index's
        order, then the file name, then move order."""
        return (-self.loss, self.position, self.filename, self.ply)


def own_colors(game: chess.pgn.Game, names: set[str]) -> set[chess.Color]:
    """The sides of ``game`` whose name is one of ``names`` (as
    ``player_names`` gives them): White's, Black's, both or neither, compared
    as ``Collection.read`` compares them."""
    colors = set()
    for color, key in ((chess.WHITE, "White"), (chess.BLACK, "Black")):
        if (game.headers.get(key) or "").strip().casefold() in names:
            colors.add(color)
    return colors


def quiz_order(entries: Iterable[QuizEntry]) -> list[QuizEntry]:
    return sorted(entries, key=QuizEntry.order)


def quiz_entries(articles: list[Article], names: set[str]) -> list[QuizEntry]:
    """The quiz for the player called ``names``, in its order: every critical
    moment of ``articles`` (given in the index's order) played by one of the
    player's sides."""
    entries = []
    for position, article in enumerate(articles):
        own = own_colors(article.game, names)
        for number, review in enumerate(article.moments, 1):
            if review.mover in own:
                entries.append(
                    QuizEntry(article, review, number, review.loss, position, article.filename, review.node.ply())
                )
    return quiz_order(entries)


def player_label(player: str | None, aliases: Iterable[str]) -> str:
    """The player's name as the quiz shows it: ``player``'s, else the first
    alias's, as prose wants it (``Example, Ada`` is ``Ada Example``)."""
    name = next((name for name in [player or "", *aliases] if name.strip()), "")
    return display_name(name)


def quiz_title(label: str) -> str:
    return f"Quiz: {label}'s own mistakes, worst first"


def quiz_html(entries: list[QuizEntry], games: int, unanalyzed: int, label: str, site_title: str,
              thresholds: Thresholds, history: History | None = None) -> str:  # fmt: skip
    """The quiz page: one line per question, linking to it. ``games`` is the
    number of the player's games, ``unanalyzed`` how many of them have no
    analysis yet; the page without questions says both. With questions, the
    lead counts the games they come from."""
    title = quiz_title(label)
    name = esc(label)
    what = (
        f"a move that cost at least {thresholds.mistake:g} points of winning chances or changed the expected result"
    )
    of_games = f"{plural(games, 'game')} of {name}'s"
    parts = [f"<h1>{esc(title)}</h1>\n"]
    if not entries:
        if games:
            lead = f"The quiz has no questions: in {of_games}, no move {name} played is a critical moment ({what})."
        else:
            lead = f"The quiz has no questions: no game here is {name}'s."
        if unanalyzed:
            lead += (
                f" {number_word(unanalyzed).capitalize()} of them {'is' if unanalyzed == 1 else 'are'} not analyzed "
                "yet, and only analyzed games have critical moments."
            )
        parts.append(f'<p class="lead">{lead}</p>\n')
        return page(title, "".join(parts), root="", site_title=site_title, history=history, home=True)

    # the games the questions come from, not all of the player's games
    sources = len({entry.article.item.id for entry in entries})
    parts.append(
        f'<p class="lead">{plural(len(entries), "question").capitalize()} from '
        f"{plural(sources, 'game')} of {name}'s: "
        f"{'it is' if len(entries) == 1 else 'each is'} a critical "
        f"moment where {name} was the one to move, {what}. The move that cost the most comes first, with the "
        "points of winning chances each one cost. Each line leads to its “what would you play?” question, where "
        "the answer stays hidden until you tap it.</p>\n"
    )
    parts.append('<ol id="quiz" class="games quiz">\n')
    for rank, entry in enumerate(entries, 1):
        article, review = entry.article, entry.review
        board = review.board_before
        points = f"{entry.loss:.0f}"
        opponent = article.black if review.mover == chess.WHITE else article.white
        meta = f"{format_date(article.game.headers.get('Date')) or 'Undated'} · vs. {opponent}"
        parts.append(
            f"<li{data(history, game=article.item.id, move=move_key(board))}>"
            f'<span class="rank">{rank}.</span> '
            f'<a href="games/{entry.filename}#moment-{entry.number}">{esc(move_label(board, review.node.move))}</a> '
            f'<span class="lost">{points} point{"" if points == "1" else "s"}</span>'
            f'<span class="meta">{esc(meta)}</span></li>\n'
        )
    parts.append("</ol>\n")
    return page(title, "".join(parts), root="", site_title=site_title, history=history, home=True)


STYLE = """\
/* pgn-postmortem site. Mobile first; light or dark as the OS says. */
:root {
  --bg: #ffffff; --fg: #202122; --muted: #54595d; --link: #3366cc; --rule: #a2a9b1;
  --box: #f8f9fa; --note: #54595d; --answer: #eaf3ff;
  --light: #f0d9b5; --dark: #b58863; --hl-light: #f7d764; --hl-dark: #d6ab36;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #101418; --fg: #e8eaed; --muted: #a8adb3; --link: #8ab4f8; --rule: #3c4043;
    --box: #1b2026; --note: #b0b6bd; --answer: #17263a;
    --light: #d8c3a0; --dark: #9c7453; --hl-light: #e8ca60; --hl-dark: #c49b32;
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
.infobox .lichess { text-align: center; font-size: .85rem; margin-top: .3rem; }
@media (min-width: 44rem) {
  .infobox { float: right; clear: right; width: 20rem; margin: 0 0 1rem 1.2rem; }
}
h2 { overflow: hidden; }
article::after { content: ""; display: block; clear: both; }
.sym { white-space: nowrap; }
.board {
  display: grid; grid-template-columns: repeat(8, 1fr); aspect-ratio: 1; width: 100%; max-width: 24rem;
  border: 1px solid var(--rule); font: 600 .65rem/1 system-ui, sans-serif; margin: 0 auto;
}
.board i { position: relative; background-size: 100% 100%; background-repeat: no-repeat; }
/* Each cell draws its own square's colour, under its piece: no pattern on the board, whose squares
   would round differently from the cells. The highlight is solid: rgba(255, 213, 0, .45) over the
   square's colour (.4 in dark mode), worked out, so the piece stays drawn over it. */
.board i.l { background-color: var(--light); }
.board i.d { background-color: var(--dark); }
.board i.l.hl { background-color: var(--hl-light); }
.board i.d.hl { background-color: var(--hl-dark); }
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
.quiz .rank { display: inline-block; min-width: 2rem; color: var(--muted); }
.quiz .lost { margin-left: .5rem; font-weight: 600; }
/* The piece set (Colin M.L. Burnett's, as python-chess ships it), shared by every diagram. */
"""


@dataclass
class SiteReport:
    articles: list[Path] = field(default_factory=list)
    analyzed: int = 0
    critical_moments: int = 0
    removed: list[Path] = field(default_factory=list)
    quiz: Path | None = None  # the quiz page, when the site has a player
    quiz_questions: int = 0

    def summary(self, out_dir: str | Path) -> str:
        text = (
            f"Wrote {len(self.articles)} article(s) to {out_dir}: {self.analyzed} analyzed, "
            f"{len(self.articles) - self.analyzed} not analyzed yet, {self.critical_moments} critical moment(s)."
        )
        if self.quiz:
            text += f" The quiz lists {self.quiz_questions} of them, the player's own."
        return text


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
    outcome_bands: tuple[float, float] = OUTCOME_BANDS,
    history: bool = True,
    site_key: str | None = None,
    player: str | None = None,
    aliases: Iterable[str] = (),
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

    ``outcome_bands`` is the pair ``(lower, upper)`` of White's winning
    chances, in percent, that decides a position's expected outcome for the
    outcome swings (the rule is in the module docstring): Black is winning at
    ``lower`` or less, White at ``upper`` or more, 40 and 60 by default. Both
    must be finite, with 0 < lower < 50 < upper < 100; any other pair raises
    ``ValueError`` before anything is written.

    ``history`` puts the reading history in the pages (the rule is in the
    module docstring); with ``history=False`` the pages carry no script, no
    history section and no ``data-`` attribute for it. ``site_key`` is the
    key the history is stored under, by default ``default_site_key(title)``:
    1 to 64 ASCII letters, digits, ``.``, ``_`` and ``-``, starting with a
    letter or a digit; any other value raises ``ValueError`` before anything
    is written, with or without the history.

    ``player`` and ``aliases`` name the player, as ``Collection.read`` takes
    them and compares them (letter case and surrounding spaces ignored), for
    the quiz page ``quiz.html`` (the rule is in the module docstring). When
    neither is given and ``games`` is a ``Collection``, the names it was read
    with are used; names given here take their place.
    """
    check_presume_threshold(presume_threshold)
    check_outcome_bands(outcome_bands)
    key = check_site_key(site_key) if site_key is not None else default_site_key(title)
    reading = History(key, history_script()) if history else None
    aliases = tuple(aliases)
    if player is None and not aliases and isinstance(games, Collection):
        player, aliases = games.player, games.aliases
    names = player_names(player, aliases)
    out_dir = Path(out_dir)
    articles = make_articles(games, thresholds, presume_threshold, outcome_bands)

    report = SiteReport()
    write_text(out_dir / "assets" / "style.css", STYLE + piece_css())
    for i, article in enumerate(articles):
        previous = articles[i - 1] if i > 0 else None
        following = articles[i + 1] if i + 1 < len(articles) else None
        path = out_dir / "games" / article.filename
        html_text = article_html(article, previous, following, site_title=title, thresholds=thresholds, history=reading)
        write_text(path, html_text)
        report.articles.append(path)
        report.analyzed += article.analyzed
        report.critical_moments += len(article.moments)
    quiz = None
    if names:
        in_order = index_order(articles)
        entries = quiz_entries(in_order, names)
        players = [article for article in in_order if own_colors(article.game, names)]
        label = player_label(player, aliases)
        unanalyzed = sum(not article.analyzed for article in players)
        quiz_text = quiz_html(entries, len(players), unanalyzed, label, title, thresholds, reading)
        write_text(out_dir / QUIZ_PAGE, quiz_text)
        quiz = Quiz(quiz_title(label), len(entries))
        report.quiz, report.quiz_questions = out_dir / QUIZ_PAGE, len(entries)
    write_text(out_dir / "index.html", index_html(articles, title, reading, quiz))

    written = {path.name for path in report.articles}
    for path in sorted((out_dir / "games").glob("*.html")):
        if path.name not in written and is_generated(path):
            path.unlink()
            report.removed.append(path)
    stale = out_dir / QUIZ_PAGE
    if not names and stale.is_file() and is_generated(stale):  # a site without a player has no quiz page
        stale.unlink()
        report.removed.append(stale)
    return report


def make_articles(
    games: Iterable[CollectedGame],
    thresholds: Thresholds = LICHESS_THRESHOLDS,
    presume_threshold: float = PRESUME_THRESHOLD,
    outcome_bands: tuple[float, float] = OUTCOME_BANDS,
) -> list[Article]:
    """An ``Article`` for each game, with its reviewed moves and the result
    it shows, sorted by file name."""
    articles = []
    for item in games:
        analyzed = is_analyzed(item.game)
        result = shown_result(item.game, presume_threshold)
        articles.append(Article(item, review_moves(item.game, thresholds, outcome_bands), analyzed, result))
    articles.sort(key=lambda article: article.stem)
    return articles
