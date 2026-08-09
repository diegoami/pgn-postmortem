---
name: publish-games
description: Regenerate the docs/ pages (main index + one page per game) from analyzed_games/ (or daily_games/), including SVG diagrams of the board before every blunder diegoami made and the engine's full refutation line. Use when the user adds/updates PGN files and wants the published GitHub pages refreshed, or says things like "publish the games", "regenerate the game pages", "update docs for the new games".
---

# Publish daily games

There are two source-of-truth directories, and `docs/` is generated from one of them — never
hand-edit files under `docs/`, always regenerate with the scripts below.

- `daily_games/*.pgn` — raw PGNs as downloaded from chess.com, with chess.com's own review
  annotations (NAGs + side variations). Turned out unreliable to build blunder detection on:
  chess.com attaches side variations somewhat inconsistently (e.g. to demonstrate a punishment line
  rather than a genuine alternative for the move that was actually flagged).
- `analyzed_games/*.pgn` — same games, re-analyzed independently with a local Stockfish engine by
  `scripts/analyze_games.py`. This is the preferred source for publishing.

## Step 1 (only when daily_games/ changed): re-analyze with Stockfish

```bash
.venv/bin/python scripts/analyze_games.py            # 0.3s of search per position (default)
.venv/bin/python scripts/analyze_games.py --depth 18  # or a fixed depth instead
```

For every `daily_games/<id>.pgn` this writes `analyzed_games/<id>.pgn`: mainline moves only (chess.com's
variations/NAGs stripped), with our own eval comment on every move (pawns, White's POV, e.g. `{+0.23}`)
and our own NAG when centipawn loss crosses a threshold (`$6` Inaccuracy ≥50cp, `$2` Mistake ≥100cp,
`$4` Blunder ≥300cp, for the side that played the move). When a flagged move differs from Stockfish's
own top choice at that point, that choice's full principal line (capped at `--pv-length` half-moves,
default 8) is attached as a sibling variation, e.g.
`( 8. dxc6 Qxd1+ 9. Kxd1 bxc6 10. e4 Nd7 11. a3 Nb6 )`.

`analyzed_games/` is committed to git (unlike `docs/`) so re-running the slower Stockfish pass isn't
required just to rebuild the docs.

## Step 2: regenerate docs/ from analyzed_games/

```bash
.venv/bin/python scripts/publish_games.py --source analyzed_games
```

(Omit `--source` to fall back to raw `daily_games/` instead — same script, same output shape, just
trusts chess.com's own annotations rather than the Stockfish pass.)

For every `<source>/<id>.pgn` it writes:
- `docs/games/<id>.md` — game info table, one section per blunder, full PGN in a collapsible block
- `docs/games/<id>/<id>.pgn` — a copy of the source PGN (downloadable from the page)
- `docs/games/<id>/blunder_*.svg` — one board diagram per blunder by `diegoami`, showing the position
  right before the move with a red arrow for the move played

A "blunder" means a move played by diegoami carrying NAG `$2` (Mistake), `$4` (Blunder), or `$9` (Miss).

Each blunder section shows, in order: the movetext played since the previous diagram (or since the
start of the game, for the first blunder) so the diagrams read as a continuous story; the diagram
itself; and, when the source PGN attaches a side variation at that exact decision point, the engine's
full suggested refutation line (`**Better was:** 8. dxc6 Qxd1+ 9. Kxd1 bxc6 ...`), not just the first
move. If the attached variation's first move is identical to what was actually played, the page says
so explicitly instead of inventing an alternative. If no variation is attached at that point at all,
the "Better was" line is omitted rather than guessing.

It also rewrites `docs/index.md`, a table linking to every game with date/players/result/opening/blunder
count.

The script is idempotent: it wipes and fully regenerates `docs/games/` each run, so it always matches
exactly what's currently in the chosen source directory.

## Setup

The project uses a local venv (`.venv/`) with `python-chess` installed from `requirements.txt`, plus
the system `stockfish` binary (`/usr/games/stockfish`) for `analyze_games.py`. If `.venv/` doesn't
exist yet, create it first:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## After running

These scripts only regenerate files locally — they do **not** commit or push. After running:

1. Run `git status` / `git diff --stat docs/ analyzed_games/` to show the user what changed (new
   games added, blunder counts changed, etc.).
2. Let the user review, then ask before staging/committing/pushing — don't push to GitHub on your
   own initiative.

If a PGN has no player named `diegoami` in the White/Black headers, the script still generates a page
for it but notes that diegoami isn't a player and skips the blunder section — that's expected, not a
bug to fix.
