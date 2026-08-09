---
name: publish-games
description: Regenerate the docs/ pages (main index + one page per game) from analyzed_games/ (or daily_games/), including SVG diagrams of the board before every blunder diegoami made and the engine's full refutation line. Use when the user adds/updates PGN files and wants the published GitHub pages refreshed, or says things like "publish the games", "regenerate the game pages", "update docs for the new games".
---

# Publish daily games

The scripts live in this repo (chess_with_claude); the games, analysis, and generated pages live in a
separate sibling repo, **chessgamescollection**, expected at `../chessgamescollection` by default (both
scripts accept `--data-dir` to point elsewhere). If that directory doesn't exist, clone it first:
`git clone git@github.com:diegoami/chessgamescollection.git ../chessgamescollection`.

Inside chessgamescollection there are two source-of-truth directories, and `docs/` is generated from
one of them — never hand-edit files under `docs/`, always regenerate with the scripts below.

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
`$4` Blunder ≥300cp, for the side that played the move). A flagged move gets two side variations
(each capped at `--pv-length` half-moves, default 8), each ending with a standard PGN
position-evaluation NAG (`$10 =`, `$14 +=`, `$15 =+`, `$16 ±`, `$17 ∓`, `$18 +-`, `$19 -+`, always from
White's POV, via `classify_position()`):
- off the position *before* the move, when Stockfish's top choice there differed from what was played:
  its full line, e.g. `( 8. dxc6 Qxd1+ 9. Kxd1 bxc6 10. e4 Nd7 11. a3 Nb6 $10 )` — read downstream as
  **Better was**
- off the move's own resulting position: Stockfish's best continuation from there (how the blunder
  should have been punished, in case the real opponent missed it), attached unconditionally — even
  when it happens to match what the opponent actually played next — read downstream as
  **Best continuation**

These are attached in a way that never disturbs the real mainline (a side variation is only ever added
to a node *after* that node's real next move already exists as `variations[0]`) — if you touch
`analyze_game()` in `scripts/analyze_games.py`, preserve that ordering or `mainline_moves()` will stop
matching the actual game.

`analyzed_games/` is committed to git in chessgamescollection (unlike `docs/`) so re-running the slower
Stockfish pass isn't required just to rebuild the docs.

## Step 2: regenerate docs/ from analyzed_games/

```bash
.venv/bin/python scripts/publish_games.py --source analyzed_games
```

(Omit `--source` to fall back to raw `daily_games/` instead — same script, same output shape, just
trusts chess.com's own annotations rather than the Stockfish pass.)

For every `<source>/<id>.pgn` it writes:
- `docs/games/<id>.md` — game info table, an **Opening theory** section, one section per blunder,
  full PGN in a collapsible block
- `docs/games/<id>/<id>.pgn` — a copy of the source PGN (downloadable from the page)
- `docs/games/<id>/blunder_*.svg` — one board diagram per blunder by `diegoami`, showing the position
  right before the move with a red arrow for the move played
- `docs/games/<id>/opening_deviation.svg` — board diagram right before the game left cataloged opening
  theory (only written if it did)

A "blunder" means a move played by diegoami carrying NAG `$2` (Mistake), `$4` (Blunder), or `$9` (Miss).

**Opening theory** (via `scripts/openings.py`, backed by `data/openings/*.tsv` — the
[lichess-org/chess-openings](https://github.com/lichess-org/chess-openings) named-line dataset,
downloaded once and committed) shows, in order: **Opening moves** (the movetext still within cataloged
theory); a diagram of the position right before the game left it (same red-arrow style as the blunder
diagrams); a sentence naming whoever played that first move (diegoami, or the opponent — in which case
diegoami never had a chance to deviate himself); and, via `OpeningBook.continuations()`, a few example
cataloged lines that were still available there — one per distinct next move, picking the shortest
available example of each for readability. This only covers *named* lines in that dataset, so it's
phrased as "the first move not found in any named line", not a claim that the move was objectively bad.

Each blunder section shows, in order: the movetext played since the previous diagram (or since the
start of the game, for the first blunder); then, when the source PGN attaches the two variations
described in Step 1:
- **Better was:** the engine's full suggested refutation line and its eval symbol, played from *before*
  the blunder (e.g. `8. dxc6 Qxd1+ 9. Kxd1 bxc6 ... =`), not just the first move. If that variation's
  first move is identical to what was actually played, the page says so explicitly instead of inventing
  an alternative.
- **Best continuation:** the engine's best line and eval symbol from *after* the blunder — i.e. how it
  should have been punished — shown even when the opponent's actual reply already matched it.

then the board diagram itself. Either analysis line is omitted rather than guessing if the source PGN
doesn't attach a variation there at all (e.g. daily_games/ as source, or the blunder was the last move
of the game).

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

These scripts only regenerate files locally — they do **not** commit or push, **in either repo**.
After running:

1. Run `git status` / `git diff --stat` **inside chessgamescollection** (not this repo — `docs/` and
   `analyzed_games/` live there now) to show the user what changed: new games added, blunder counts
   changed, etc.
2. Let the user review, then ask before staging/committing/pushing in chessgamescollection — don't
   push to GitHub on your own initiative. If you also changed the scripts themselves in this repo,
   that's a separate commit here, in chess_with_claude.

If a PGN has no player named `diegoami` in the White/Black headers, the script still generates a page
for it but notes that diegoami isn't a player and skips the blunder section — that's expected, not a
bug to fix.
