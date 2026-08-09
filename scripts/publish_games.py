#!/usr/bin/env python3
"""Generate GitHub-viewable markdown pages for the games in daily_games/ (or
another source directory of same-shaped PGNs, e.g. analyzed_games/).

For every <source>/<id>.pgn this writes:
  docs/games/<id>.md            - game info page (result, opening, full PGN)
  docs/games/<id>/<id>.pgn      - copy of the source PGN, downloadable
  docs/games/<id>/blunder_*.svg - board position before each blunder
                                   (NAG $2 Mistake, $4 Blunder, or $9 Miss)
                                   played by PLAYER_NAME

Whenever the source PGN attaches a side variation directly at a blunder's
decision point, its full line (not just the first move) is rendered under
"Better was:" alongside the diagram.

It also (re)writes docs/index.md, a table linking to every game page.

The script is idempotent: docs/games/ is wiped and fully regenerated each
run, so it always reflects exactly what's currently in the source directory.

Usage:
    .venv/bin/python scripts/publish_games.py
    .venv/bin/python scripts/publish_games.py --source analyzed_games
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import chess
import chess.pgn
import chess.svg

PLAYER_NAME = "diegoami"

REPO_ROOT = Path(__file__).resolve().parent.parent
GAMES_SRC_DIR = REPO_ROOT / "daily_games"
DOCS_DIR = REPO_ROOT / "docs"
GAMES_OUT_DIR = DOCS_DIR / "games"

# chess.com marks its worst move categories with these PGN NAGs:
# $2 = Mistake, $4 = Blunder, $9 = Miss. All three count as a "blunder" here.
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


def sort_key(path: Path):
    stem = path.stem
    return (0, int(stem)) if stem.isdigit() else (1, stem)


def load_games() -> list[tuple[Path, chess.pgn.Game]]:
    games = []
    for pgn_path in sorted(GAMES_SRC_DIR.glob("*.pgn"), key=sort_key):
        with pgn_path.open(encoding="utf-8") as fh:
            game = chess.pgn.read_game(fh)
        if game is None:
            print(f"warning: could not parse {pgn_path}", file=sys.stderr)
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
    chain) as PGN-style movetext, e.g. '8. dxc6 Qxd1+ 9. Kxd1 Nxc6'."""
    board = board_before.copy()
    parts = []
    node = first_node
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
        node = node.variations[0] if node.variations else None
    return " ".join(parts)


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


def mainline_steps(game: chess.pgn.Game) -> list[dict]:
    """Flatten the mainline (the game as actually played) into a list of
    per-move steps, each retaining enough tree context to find the sibling
    variation chess.com attached at that point."""
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
    source = f"[chess.com]({link})" if link else "?"

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
) -> None:
    headers = game.headers
    white = headers.get("White", "?")
    black = headers.get("Black", "?")

    parts = [f"# Game {index}: {white} vs {black}", ""]
    parts.append(format_headers_table(headers))
    parts.append("")
    parts.append(f"[Download PGN]({index}/{index}.pgn)")
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
                parts.append(f"_{lead_label}: {b['lead_in']}_")
                parts.append("")
            parts.append(f"![Position before {move_no}{letter} {b['san']}]({index}/{svg_name})")
            parts.append("")
            better = b["better_line"]
            if better == "same":
                parts.append("No stronger alternative was available here — this was already the engine's top choice.")
                parts.append("")
            elif better:
                parts.append(f"**Better was:** {better}")
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


def process_game(pgn_path: Path, game: chess.pgn.Game) -> dict:
    index = pgn_path.stem
    game_dir = GAMES_OUT_DIR / index
    game_dir.mkdir(parents=True, exist_ok=True)

    dest_pgn = game_dir / f"{index}.pgn"
    shutil.copyfile(pgn_path, dest_pgn)

    color = player_color(game)
    blunders = find_blunders(mainline_steps(game), color) if color is not None else []

    blunders_with_svg = []
    for i, b in enumerate(blunders, start=1):
        svg_name = f"blunder_{i}_move{b['move_number']}{color_letter(b['mover_color'])}.svg"
        (game_dir / svg_name).write_text(
            render_svg(b["board_before"], b["move"], b["mover_color"]), encoding="utf-8"
        )
        blunders_with_svg.append((svg_name, b))

    write_game_markdown(index, pgn_path, game, color, blunders_with_svg)

    return {
        "index": index,
        "headers": game.headers,
        "num_blunders": len(blunders_with_svg),
    }


def write_index(entries: list[dict]) -> None:
    lines = [f"# {PLAYER_NAME}'s Daily Games", "", "| # | Date | White | Black | Result | Opening | Blunders |", "|---|---|---|---|---|---|---|"]
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
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--source",
        default="daily_games",
        help="directory of source PGNs, relative to repo root (default: daily_games)",
    )
    args = parser.parse_args()

    global GAMES_SRC_DIR
    GAMES_SRC_DIR = REPO_ROOT / args.source

    games = load_games()
    if not games:
        print(f"No PGN files found in {GAMES_SRC_DIR}", file=sys.stderr)
        sys.exit(1)

    if GAMES_OUT_DIR.exists():
        shutil.rmtree(GAMES_OUT_DIR)
    GAMES_OUT_DIR.mkdir(parents=True)

    entries = [process_game(pgn_path, game) for pgn_path, game in games]
    write_index(entries)

    total_blunders = sum(e["num_blunders"] for e in entries)
    print(f"Wrote docs/index.md and {len(entries)} game page(s) ({total_blunders} blunder diagram(s) total).")


if __name__ == "__main__":
    main()
