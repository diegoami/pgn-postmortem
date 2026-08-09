---
name: publish-games
description: Regenerate the docs/ pages (main index + one page per game) from analyzed_games/ (or daily_games/), including SVG diagrams of the board before every blunder the configured player made and the engine's full refutation line. Use when the user adds/updates PGN files and wants the published GitHub pages refreshed, or says things like "publish the games", "regenerate the game pages", "update docs for the new games".
---

# Publish games

The scripts (`scripts/analyze_games.py`, `scripts/publish_games.py`) are generic — they take
`--player` and `--data-dir` and don't hardcode any particular person or data location. This project's
own choice of player and data location lives in a local, gitignored **`.env`** file (see
`.env.example`), never in a tracked file. If `.env` isn't set up yet, check for it before running
anything:

```bash
test -f .env && cat .env || echo "no .env - see .env.example"
```

If it's missing, ask the user for `CHESS_PLAYER` (and `CHESS_DATA_DIR`, if their games live outside
this repo) rather than guessing or hardcoding a value into any command or file.

There are two source-of-truth directories inside the data directory, and `docs/` is generated from one
of them — never hand-edit files under `docs/`, always regenerate with the scripts below.

- `daily_games/*.pgn` — raw source PGNs, one game per file (see the README's "Adding a new game"
  section for why). Whatever move-quality review the source attached (if any) is treated as unreliable
  for blunder detection — e.g. chess.com exports were found to attach side variations somewhat
  inconsistently (a punishment line rather than a genuine alternative for the flagged move).
- `analyzed_games/*.pgn` — same games, re-analyzed independently with a local Stockfish engine by
  `scripts/analyze_games.py`. This is the preferred source for publishing.

## Quick path: new games were added to daily_games/

```bash
scripts/update_games.sh
```

This just chains Step 1 and Step 2 below with no flags (both read `--player`/`--data-dir` from
`.env`). Use it as the default response to "I added new games, publish them" / "process the new
games". Reach for the individual steps below only when a custom flag is actually needed — e.g.
`--force` to redo already-analyzed games, or `--depth` for a slower/more accurate pass.

## Step 1 (only when daily_games/ changed): re-analyze with Stockfish

```bash
.venv/bin/python scripts/analyze_games.py
.venv/bin/python scripts/analyze_games.py --depth 18  # fixed depth instead of the 0.3s default
.venv/bin/python scripts/analyze_games.py --blunder-threshold 25 --mistake-threshold 15  # stricter
```

(No flags needed if `.env` is configured — `CHESS_DATA_DIR` from there is used automatically. Add
`--data-dir ...` only to override it for this run.)

**Games that already have an `analyzed_games/<id>.pgn` are skipped automatically** — a game's source
PGN never changes once added, so re-running this after adding new games only analyzes the new ones
(the script prints how many it skipped). Pass `--force` to redo everything, which is needed after
changing the analysis logic itself (`analyze_game()`, `classify()`, `classify_position()`, ...) so
existing games pick up the change too - don't forget this when you've just edited that script.

For every `daily_games/<id>.pgn` this writes `analyzed_games/<id>.pgn`: mainline moves only (the
source's variations/NAGs stripped), with our own eval comment on every move (pawns, White's POV, e.g.
`{+0.23}`) and our own NAG when **win percentage lost** (not raw centipawns) crosses a threshold (`$6`
Inaccuracy, `$2` Mistake, `$4` Blunder, for the side that played the move). Centipawns are converted to
a 0-100 win% via `win_percent()`, the same logistic fit [lichess uses](https://lichess.org/page/accuracy)
— this matters because the same cp swing means very different things in an equal position vs. an
already-decided one (e.g. a huge cp swing that still leaves the mover completely winning shouldn't
count the same as an equal-position blunder). Thresholds default to lichess's own (10/20/30 win%
points) and are configurable via `--inaccuracy-threshold`/`--mistake-threshold`/`--blunder-threshold`
on `analyze_games.py`, or `ANALYSIS_INACCURACY_PCT`/`ANALYSIS_MISTAKE_PCT`/`ANALYSIS_BLUNDER_PCT` in
`.env` (a flag always wins over `.env`). Same pattern for search effort: `--time`/`--depth` or
`ANALYSIS_TIME`/`ANALYSIS_DEPTH`. A flagged move gets two side variations (each capped at `--pv-length`
half-moves, default 8), each ending with a standard PGN
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

Each source file must hold exactly one game — `read_single_game()` in `scripts/pgn_io.py` skips (with
a warning) any file with zero or more than one game, rather than silently dropping games. That warning
in the script's output means a file needs to be split, not that something is broken.

`analyzed_games/` is meant to be committed to git (unlike `docs/`) so re-running the slower Stockfish
pass isn't required just to rebuild the docs.

## Step 2: regenerate docs/ from analyzed_games/

```bash
.venv/bin/python scripts/publish_games.py --source analyzed_games
```

(Again, no `--player`/`--data-dir` needed if `.env` is configured. Omit `--source` to fall back to raw
`daily_games/` instead — same script, same output shape, just trusts the source PGN's own annotations
rather than the Stockfish pass.)

For every `<source>/<id>.pgn` it writes:
- `docs/games/<id>.md` — game info table, an **Opening theory** section, then one entry per flagged
  move in move order under "## Blunders by \<name\>" — Mistakes/Blunders/Misses shown plainly,
  Inaccuracies individually folded under a `<details>` block since they're one notch below a real
  blunder (`is_inaccuracy()` decides which) — full PGN in a collapsible block
- `docs/games/<id>/<id>.pgn` — a copy of the source PGN (downloadable from the page)
- `docs/games/<id>/blunder_*.svg` — one board diagram per Mistake/Blunder/Miss by the configured
  player, showing the position right before the move with a red arrow for the move played
- `docs/games/<id>/inaccuracy_*.svg` — same, for Inaccuracies
- `docs/games/<id>/opening_deviation.svg` — board diagram right before the game left cataloged opening
  theory (only written if it did)

A "blunder" means a move played by the configured player carrying NAG `$2` (Mistake), `$4` (Blunder),
or `$9` (Miss) — these count toward the index page's Blunders column. `$6` (Inaccuracy, via
`INACCURACY_NAGS`) is interleaved into the same list (see above) but not counted there.
`find_flagged_moves(steps, colors, BLUNDER_NAGS | INACCURACY_NAGS)` produces the single combined,
move-ordered list both severities are drawn from, so lead-in text between entries flows continuously
regardless of which severity separates them. `--player '*'` (or `CHESS_PLAYER=*`) reports blunders by
both sides in every game instead of filtering to one name — useful when neither side is "the
configured player", e.g. a folder of master games.

**Opening theory** (via `scripts/openings.py`, backed by `data/openings/*.tsv` — the
[lichess-org/chess-openings](https://github.com/lichess-org/chess-openings) named-line dataset,
downloaded once and committed) shows, in order: **Opening moves** (the movetext still within cataloged
theory); a diagram of the position right before the game left it (same red-arrow style as the blunder
diagrams); a sentence naming whoever played that first move (the configured player, or the opponent —
in which case the configured player never had a chance to deviate); and, via
`OpeningBook.continuations()`, a few example cataloged lines that were still available there — one per
distinct next move, picking the shortest available example of each for readability. This only covers
*named* lines in that dataset, so it's phrased as "the first move not found in any named line", not a
claim that the move was objectively bad.

Each entry shows, in order (via `render_flagged_move()`, shared by both severities —
`include_heading=False` for Inaccuracies since their heading becomes the `<details>`'s `<summary>`
instead): the movetext played since the previous diagram (or since the start of the game, for the
first one); then, when the source PGN attaches the two variations described in Step 1:
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

These scripts only regenerate files locally — they do **not** commit or push, **in whichever repo the
data directory turns out to be**. After running:

1. Both scripts print the resolved output paths as they run (e.g. `-> /path/to/analyzed_games/1.pgn`,
   `Wrote docs/index.md ...`) — use that (or `CHESS_DATA_DIR` from `.env`) to find the data directory,
   since it isn't a fixed path relative to this repo. Run `git status` / `git diff --stat` there to
   show the user what changed: new games added, blunder counts changed, etc. If the data directory is
   this same repo, that's just this repo's own `git status`.
2. Let the user review, then ask before staging/committing/pushing — don't push to GitHub on your own
   initiative. If you also changed the scripts themselves, that's a separate commit in this repo.

If a PGN has no player matching `--player`/`CHESS_PLAYER` in the White/Black headers, the script still
generates a page for it but notes that the player isn't in this game and skips the blunder section —
that's expected, not a bug to fix.
