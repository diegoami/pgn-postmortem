#!/usr/bin/env python3
"""Generate GitHub-viewable markdown pages for a folder of PGN games,
highlighting every blunder a chosen player made (found via independent
engine analysis - see analyze_games.py) with board diagrams, the engine's
refutation, and how the game actually continued, plus an opening-theory
breakdown. Works with any standard PGN collection, not tied to a particular
source site or player.

Reads games from <data-dir>/<source>/*.pgn (source defaults to daily_games/,
pass --source analyzed_games to use analyze_games.py's output instead) and
writes, inside <data-dir>:
  docs/games/<id>.md            - game info page (result, opening, full PGN)
  docs/games/<id>/<id>.pgn      - copy of the source PGN, downloadable
  docs/games/<id>/blunder_*.svg - board position before each blunder
                                   (NAG $2 Mistake, $4 Blunder, or $9 Miss)
                                   played by --player

Whenever the source PGN attaches a side variation directly at a blunder's
decision point, its full line (not just the first move) is rendered under
"Better was:" alongside the diagram.

It also (re)writes docs/index.md, a table linking to every game page.

The script is idempotent: docs/games/ is wiped and fully regenerated each
run, so it always reflects exactly what's currently in the source directory.

<data-dir> can be this same repo, or a separate repo/directory holding just
the games/analysis/docs, kept apart from these scripts. Resolved as:
--data-dir, else CHESS_DATA_DIR (from .env or the real environment), else
this repo's own checkout directory. --player is resolved the same way via
CHESS_PLAYER, but has no directory fallback - it's always required one way
or another. See .env.example.

Usage:
    .venv/bin/python scripts/publish_games.py --player "Magnus Carlsen"
    .venv/bin/python scripts/publish_games.py --player myusername --source analyzed_games
    .venv/bin/python scripts/publish_games.py --player myusername --data-dir /path/to/games
    .venv/bin/python scripts/publish_games.py   # reads CHESS_PLAYER/CHESS_DATA_DIR from .env
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

import chess
import chess.pgn
import chess.svg

from openings import OpeningBook, load_book
from pgn_io import load_dotenv, read_single_game

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = REPO_ROOT

# Populated at startup by main() from --player/--data-dir/--source.
PLAYER_NAME: str
GAMES_SRC_DIR: Path
DOCS_DIR: Path
GAMES_OUT_DIR: Path

# Some PGN sources (e.g. chess.com exports) mark their worst move categories
# with these NAGs: $2 = Mistake, $4 = Blunder, $9 = Miss (a non-standard
# reuse of that code). All three count as a "blunder" here, when present.
BLUNDER_NAGS = {chess.pgn.NAG_MISTAKE, chess.pgn.NAG_BLUNDER, 9}

NAG_LABELS = {
    chess.pgn.NAG_GOOD_MOVE: "Good",
    chess.pgn.NAG_MISTAKE: "Mistake",
    chess.pgn.NAG_BRILLIANT_MOVE: "Brilliant",
    chess.pgn.NAG_BLUNDER: "Blunder",
    chess.pgn.NAG_SPECULATIVE_MOVE: "Speculative",
    chess.pgn.NAG_DUBIOUS_MOVE: "Inaccuracy",
    9: "Miss",
}

# Standard PGN position-evaluation NAGs, always from White's POV.
POSITION_NAG_SYMBOLS = {
    10: "=",
    13: "∞",  # unclear
    14: "+=",
    15: "=+",
    16: "±",  # white moderate advantage
    17: "∓",  # black moderate advantage
    18: "+-",
    19: "-+",
}


def sort_key(path: Path):
    stem = path.stem
    return (0, int(stem)) if stem.isdigit() else (1, stem)


def load_games() -> list[tuple[Path, chess.pgn.Game]]:
    games = []
    for pgn_path in sorted(GAMES_SRC_DIR.glob("*.pgn"), key=sort_key):
        game = read_single_game(pgn_path)
        if game is None:
            continue
        games.append((pgn_path, game))
    return games


def player_color(game: chess.pgn.Game) -> chess.Color | None:
    white = game.headers.get("White", "")
    black = game.headers.get("Black", "")
    if white.lower() == PLAYER_NAME.lower():
        return chess.WHITE
    if black.lower() == PLAYER_NAME.lower():
        return chess.BLACK
    return None


def move_label(step: dict) -> str:
    letter = "." if step["mover_color"] == chess.WHITE else "..."
    return f"{step['move_number']}{letter} {step['san']}"


def format_named_line(board_before: chess.Board, moves_san: tuple[str, ...]) -> str | None:
    """Render a sequence of SAN moves (as found in the openings dataset,
    starting at board_before) as PGN-style movetext. Returns None if the
    moves turn out not to be legal from this position (defensive - the
    dataset is external, third-party data)."""
    board = board_before.copy()
    parts = []
    first = True
    try:
        for san in moves_san:
            if board.turn == chess.WHITE:
                parts.append(f"{board.fullmove_number}. {san}")
            elif first:
                parts.append(f"{board.fullmove_number}... {san}")
            else:
                parts.append(san)
            board.push_san(san)
            first = False
    except ValueError:
        return None
    return " ".join(parts)


def analyze_opening(book: OpeningBook, steps: list[dict], color: chess.Color | None, headers: chess.pgn.Headers) -> dict:
    """Describe how far the game matches a cataloged named opening line
    (see scripts/openings.py). Returns a dict with:
      message           - summary sentence
      opening_moves     - movetext played up to (not including) the point
                           the game left cataloged theory, i.e. what the
                           deviation diagram shows the position after
      deviation_step     - the step where the game first left the cataloged
                            lines (for a diagram), or None if it never did
                            (or never matched one at all)
      continuation_lines - a few example cataloged lines from that same
                            position, as "movetext (*name*, ECO)" strings
    """
    sans = [s["san"] for s in steps]
    result = book.find_deviation(sans)
    in_book_plies = result["in_book_plies"]
    opening = result["opening"]

    empty = {"message": "", "opening_moves": "", "deviation_step": None, "continuation_lines": []}

    if opening is None:
        return {**empty, "message": "No cataloged named opening line matches this game's moves."}

    name, eco = opening[1], opening[0]
    if not result["left_book"]:
        message = f"The whole game stayed within a cataloged named opening line (*{name}*, ECO {eco})."
        return {**empty, "message": message}

    last_book_step = steps[in_book_plies - 1]
    dev_step = steps[in_book_plies]
    if color is not None and dev_step["mover_color"] == color:
        who = PLAYER_NAME
    else:
        who = headers.get("White") if dev_step["mover_color"] == chess.WHITE else headers.get("Black")
        who = who or ("White" if dev_step["mover_color"] == chess.WHITE else "Black")

    message = (
        f"Matches a cataloged line (*{name}*, ECO {eco}) through {move_label(last_book_step)}. "
        f"{who} played {move_label(dev_step)}, the first move not found in any named line in this dataset."
    )

    continuation_lines = []
    for cont_eco, cont_name, cont_moves in book.continuations(sans[:in_book_plies]):
        line = format_named_line(dev_step["board_before"], cont_moves)
        if line:
            continuation_lines.append(f"{line} (*{cont_name}*, {cont_eco})")

    return {
        "message": message,
        "opening_moves": format_movetext(steps[:in_book_plies]),
        "deviation_step": dev_step,
        "continuation_lines": continuation_lines,
    }


def format_movetext(steps: list[dict]) -> str:
    """Render a slice of mainline steps as PGN-style movetext, e.g.
    '7. Bxc4 c6 8. e4 Nh5'."""
    parts = []
    for i, step in enumerate(steps):
        board_before = step["board_before"]
        san = board_before.san(step["move"])
        if board_before.turn == chess.WHITE:
            parts.append(f"{board_before.fullmove_number}. {san}")
        elif i == 0:
            parts.append(f"{board_before.fullmove_number}... {san}")
        else:
            parts.append(san)
    return " ".join(parts)


def variation_movetext(board_before: chess.Board, first_node: chess.pgn.GameNode) -> str:
    """Render a variation's own mainline (following .variations[0] down the
    chain) as PGN-style movetext, e.g. '8. dxc6 Qxd1+ 9. Kxd1 Nxc6 ±'. If the
    last move carries a position-evaluation NAG (see analyze_games.py), the
    usual annotation symbol (=, +=, ±, +-, ...) is appended."""
    board = board_before.copy()
    parts = []
    node = first_node
    last_node = None
    first = True
    while node is not None:
        san = board.san(node.move)
        if board.turn == chess.WHITE:
            parts.append(f"{board.fullmove_number}. {san}")
        elif first:
            parts.append(f"{board.fullmove_number}... {san}")
        else:
            parts.append(san)
        board.push(node.move)
        first = False
        last_node = node
        node = node.variations[0] if node.variations else None
    text = " ".join(parts)
    if last_node is not None:
        symbol = next((POSITION_NAG_SYMBOLS[n] for n in last_node.nags if n in POSITION_NAG_SYMBOLS), None)
        if symbol:
            text += f" {symbol}"
    return text


def suggested_better_line(step: dict) -> str | None:
    """If the PGN attaches a side variation directly at this decision point
    (the engine's suggested refutation), return its full movetext. Returns
    "same" if that variation's first move is identical to the move actually
    played (i.e. the played move was already the top choice), or None if no
    variation is attached here at all."""
    parent_node = step["parent_node"]
    child_node = step["child_node"]
    alt = next((v for v in parent_node.variations if v is not child_node), None)
    if alt is None:
        return None
    alt_first_san = step["board_before"].san(alt.move)
    if alt_first_san == step["san"]:
        return "same"
    return variation_movetext(step["board_before"], alt)


def suggested_punishment_line(step: dict) -> str | None:
    """If the PGN attaches a side variation directly off of the blunder move
    itself (the engine's best continuation from the position that actually
    resulted, i.e. how the blunder should have been punished), return its
    full movetext - regardless of whether it happens to match what the
    opponent actually played next. Returns None if no such variation is
    attached at all — e.g. the blunder was the last move of the game, or the
    source PGN doesn't offer one."""
    child_node = step["child_node"]
    if len(child_node.variations) < 2:
        return None
    punishment_node = child_node.variations[1]
    board_after = step["board_before"].copy()
    board_after.push(step["move"])
    return variation_movetext(board_after, punishment_node)


def mainline_steps(game: chess.pgn.Game) -> list[dict]:
    """Flatten the mainline (the game as actually played) into a list of
    per-move steps, each retaining enough tree context to find the sibling
    variation the source PGN attached at that point."""
    steps = []
    node = game
    while node.variations:
        next_node = node.variations[0]
        board_before = node.board()
        mover = board_before.turn
        move = next_node.move
        steps.append(
            {
                "board_before": board_before,
                "move": move,
                "san": board_before.san(move),
                "move_number": board_before.fullmove_number,
                "mover_color": mover,
                "nags": sorted(next_node.nags),
                "parent_node": node,
                "child_node": next_node,
            }
        )
        node = next_node
    return steps


def find_blunders(steps: list[dict], color: chess.Color) -> list[dict]:
    """From the flattened mainline, collect every move by `color` whose NAG
    marks it a Mistake or Blunder, together with the movetext played since
    the previous blunder (or the start of the game) and, where the source
    PGN offers one, the engine's suggested better move."""
    blunders = []
    lead_in_start = 0
    for i, step in enumerate(steps):
        if step["mover_color"] == color and BLUNDER_NAGS & set(step["nags"]):
            blunder = dict(step)
            blunder["nags"] = sorted(BLUNDER_NAGS & set(step["nags"]))
            blunder["lead_in"] = format_movetext(steps[lead_in_start:i])
            blunder["better_line"] = suggested_better_line(step)
            blunder["punishment_line"] = suggested_punishment_line(step)
            blunders.append(blunder)
            lead_in_start = i
    return blunders


def render_svg(board_before: chess.Board, move: chess.Move, mover_color: chess.Color) -> str:
    arrow = chess.svg.Arrow(move.from_square, move.to_square, color="#cc0000cc")
    return chess.svg.board(
        board=board_before,
        arrows=[arrow],
        orientation=mover_color,
        size=400,
    )


def color_letter(color: chess.Color) -> str:
    return "w" if color == chess.WHITE else "b"


def format_headers_table(headers: chess.pgn.Headers) -> str:
    white = headers.get("White", "?")
    black = headers.get("Black", "?")
    white_elo = headers.get("WhiteElo", "?")
    black_elo = headers.get("BlackElo", "?")
    eco = headers.get("ECO", "")
    eco_url = headers.get("ECOUrl", "")
    opening = f"[{eco}]({eco_url})" if eco_url else (eco or "?")
    link = headers.get("Link", "")
    site = headers.get("Site", "").strip()
    source = f"[{site or 'link'}]({link})" if link else "?"

    rows = [
        ("Date", headers.get("Date", "?")),
        ("Result", headers.get("Result", "?")),
        ("White", f"{white} ({white_elo})"),
        ("Black", f"{black} ({black_elo})"),
        ("Opening", opening),
        ("Time control", headers.get("TimeControl", "?")),
        ("Termination", headers.get("Termination", "?")),
        ("Source", source),
    ]
    lines = ["| | |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in rows]
    return "\n".join(lines)


def write_game_markdown(
    index: str,
    pgn_path: Path,
    game: chess.pgn.Game,
    color: chess.Color | None,
    blunders_with_svg: list[tuple[str, dict]],
    opening: dict,
    opening_svg_name: str | None,
) -> None:
    headers = game.headers
    white = headers.get("White", "?")
    black = headers.get("Black", "?")

    parts = [f"# Game {index}: {white} vs {black}", ""]
    parts.append(format_headers_table(headers))
    parts.append("")
    parts.append(f"[Download PGN]({index}/{index}.pgn)")
    parts.append("")

    parts.append("## Opening theory")
    parts.append("")
    if opening_svg_name:
        dev_step = opening["deviation_step"]
        move_no = dev_step["move_number"]
        letter = "." if dev_step["mover_color"] == chess.WHITE else "..."
        if opening["opening_moves"]:
            parts.append(f"**Opening moves**: {opening['opening_moves']}")
            parts.append("")
        parts.append(f"![Position before {move_no}{letter} {dev_step['san']}]({index}/{opening_svg_name})")
        parts.append("")
        parts.append(opening["message"])
        parts.append("")
        if opening["continuation_lines"]:
            parts.append("**Known continuations from here:**")
            parts.append("")
            for line in opening["continuation_lines"]:
                parts.append(f"- {line}")
            parts.append("")
    else:
        parts.append(opening["message"])
        parts.append("")

    parts.append(f"## Blunders by {PLAYER_NAME}")
    parts.append("")
    if color is None:
        parts.append(f"_{PLAYER_NAME} is not a player in this game._")
    elif not blunders_with_svg:
        parts.append(f"No blunders (Mistake or worse) by {PLAYER_NAME} found in this game.")
    else:
        for n, (svg_name, b) in enumerate(blunders_with_svg, start=1):
            labels = "/".join(NAG_LABELS.get(nag, f"${nag}") for nag in b["nags"])
            move_no = b["move_number"]
            letter = "." if b["mover_color"] == chess.WHITE else "..."
            parts.append(f"### Move {move_no}{letter} {b['san']} ({labels})")
            parts.append("")
            if b["lead_in"]:
                lead_label = "Moves from the start of the game" if n == 1 else "Moves since the previous diagram"
                parts.append(f"**{lead_label}**: {b['lead_in']}")
                parts.append("")
            better = b["better_line"]
            if better == "same":
                parts.append("No stronger alternative was available here — this was already the engine's top choice.")
                parts.append("")
            elif better:
                parts.append(f"**Better was:** {better}")
                parts.append("")
            punishment = b["punishment_line"]
            if punishment:
                parts.append(f"**Best continuation:** {punishment}")
                parts.append("")
            parts.append(f"![Position before {move_no}{letter} {b['san']}]({index}/{svg_name})")
            parts.append("")

    parts.append("## Full PGN")
    parts.append("")
    parts.append("<details>")
    parts.append("<summary>Show movetext</summary>")
    parts.append("")
    parts.append("```pgn")
    parts.append(pgn_path.read_text(encoding="utf-8").strip())
    parts.append("```")
    parts.append("</details>")
    parts.append("")

    (GAMES_OUT_DIR / f"{index}.md").write_text("\n".join(parts), encoding="utf-8")


def process_game(pgn_path: Path, game: chess.pgn.Game, book: OpeningBook) -> dict:
    index = pgn_path.stem
    game_dir = GAMES_OUT_DIR / index
    game_dir.mkdir(parents=True, exist_ok=True)

    dest_pgn = game_dir / f"{index}.pgn"
    shutil.copyfile(pgn_path, dest_pgn)

    color = player_color(game)
    steps = mainline_steps(game)
    blunders = find_blunders(steps, color) if color is not None else []
    opening = analyze_opening(book, steps, color, game.headers)

    blunders_with_svg = []
    for i, b in enumerate(blunders, start=1):
        svg_name = f"blunder_{i}_move{b['move_number']}{color_letter(b['mover_color'])}.svg"
        (game_dir / svg_name).write_text(
            render_svg(b["board_before"], b["move"], b["mover_color"]), encoding="utf-8"
        )
        blunders_with_svg.append((svg_name, b))

    opening_svg_name = None
    dev_step = opening["deviation_step"]
    if dev_step is not None:
        opening_svg_name = "opening_deviation.svg"
        (game_dir / opening_svg_name).write_text(
            render_svg(dev_step["board_before"], dev_step["move"], dev_step["mover_color"]), encoding="utf-8"
        )

    write_game_markdown(index, pgn_path, game, color, blunders_with_svg, opening, opening_svg_name)

    return {
        "index": index,
        "headers": game.headers,
        "num_blunders": len(blunders_with_svg),
    }


def write_index(entries: list[dict]) -> None:
    lines = [f"# {PLAYER_NAME}'s Games", "", "| # | Date | White | Black | Result | Opening | Blunders |", "|---|---|---|---|---|---|---|"]
    for e in entries:
        h = e["headers"]
        eco = h.get("ECO", "")
        eco_url = h.get("ECOUrl", "")
        opening = f"[{eco}]({eco_url})" if eco_url else (eco or "?")
        lines.append(
            f"| [{e['index']}](games/{e['index']}.md) "
            f"| {h.get('Date', '?')} "
            f"| {h.get('White', '?')} "
            f"| {h.get('Black', '?')} "
            f"| {h.get('Result', '?')} "
            f"| {opening} "
            f"| {e['num_blunders']} |"
        )
    (DOCS_DIR / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    load_dotenv(REPO_ROOT / ".env")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--player",
        default=os.environ.get("CHESS_PLAYER"),
        help="whose blunders to report, matched against the PGN White/Black headers "
        "(required; can also be set via CHESS_PLAYER in .env or the real environment)",
    )
    parser.add_argument(
        "--source",
        default="daily_games",
        help="directory of source PGNs, relative to --data-dir (default: daily_games)",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help=f"directory holding {{daily_games,analyzed_games,docs}}/ - your own repo, or a "
        f"separate data repo (default: CHESS_DATA_DIR in .env or the real environment, else "
        f"this repo's own checkout, currently {DEFAULT_DATA_DIR})",
    )
    args = parser.parse_args()

    if not args.player:
        print("error: --player is required (whose blunders to report), or set CHESS_PLAYER in .env", file=sys.stderr)
        sys.exit(1)

    data_dir = Path(args.data_dir or os.environ.get("CHESS_DATA_DIR") or DEFAULT_DATA_DIR).resolve()
    if not data_dir.is_dir():
        print(
            f"error: data dir not found: {data_dir}\nPass --data-dir, or set CHESS_DATA_DIR in .env.",
            file=sys.stderr,
        )
        sys.exit(1)

    global PLAYER_NAME, GAMES_SRC_DIR, DOCS_DIR, GAMES_OUT_DIR
    PLAYER_NAME = args.player
    GAMES_SRC_DIR = data_dir / args.source
    DOCS_DIR = data_dir / "docs"
    GAMES_OUT_DIR = DOCS_DIR / "games"

    games = load_games()
    if not games:
        print(f"No PGN files found in {GAMES_SRC_DIR}", file=sys.stderr)
        sys.exit(1)

    if GAMES_OUT_DIR.exists():
        shutil.rmtree(GAMES_OUT_DIR)
    GAMES_OUT_DIR.mkdir(parents=True)

    book = load_book()
    entries = [process_game(pgn_path, game, book) for pgn_path, game in games]
    write_index(entries)

    total_blunders = sum(e["num_blunders"] for e in entries)
    print(f"Wrote docs/index.md and {len(entries)} game page(s) ({total_blunders} blunder diagram(s) total).")


if __name__ == "__main__":
    main()
