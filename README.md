# pgn-postmortem

Turns a folder of PGN chess games into a browsable set of GitHub-viewable Markdown pages, highlighting
every blunder a chosen player made — with a board diagram before each one, the engine's refutation,
how the game actually continued, and an opening-theory breakdown showing where (and if) the player
left known theory.

Works with any standard PGN collection and any player name — nothing here is tied to a particular
chess site, person, or data location; all of that is configuration (see below), not something baked
into the repo. Move-quality detection comes from an independent local
[Stockfish](https://stockfishchess.org/) analysis pass (see below), not from whatever annotations (if
any) the source PGN happens to carry.

## Workflow

```
daily_games/*.pgn  --[analyze_games.py]-->  analyzed_games/*.pgn  --[publish_games.py]-->  docs/
```

1. **`daily_games/<id>.pgn`** — your source PGNs, one file per game, numbered sequentially. Some PGN
   sources attach their own move-quality review, but it can be inconsistent (e.g. chess.com exports
   were found to attach a side variation demonstrating a punishment line rather than a genuine
   alternative to the move it actually flagged) — not reliable enough to build blunder detection on
   directly.

   **Each file must hold exactly one game.** Every output path these scripts generate
   (`docs/games/<id>.md`, `docs/games/<id>/blunder_*.svg`, `analyzed_games/<id>.pgn`, ...) is derived
   from just the source filename - there's no second index for "which game within the file", so a
   second game packed into the same file has nowhere to go. Worse, `python-chess`'s PGN reader silently
   reads only the *first* game in a multi-game file and drops the rest with no error - exactly the kind
   of silent data loss that's easy to miss until a game is just... gone. Both scripts detect this case
   and skip the whole file with a warning rather than guessing; split multi-game PGN exports into one
   file per game before dropping them in.

2. **`scripts/analyze_games.py`** re-analyzes each game independently with a local Stockfish engine
   and writes a clean copy to **`analyzed_games/<id>.pgn`**: mainline moves only (the source's own
   variations/NAGs stripped), an eval comment on every move (pawns, White's POV, e.g. `{+0.23}`), our
   own NAG when a move's centipawn loss crosses a threshold (`$6` Inaccuracy ≥50cp, `$2` Mistake
   ≥100cp, `$4` Blunder ≥300cp), and, for a flagged move, two side variations capturing Stockfish's own
   view of the position, each ending in a standard PGN position-evaluation NAG (`$10`/`$14`.../`$19`,
   i.e. `=`, `+=`, `=+`, `±`, `∓`, `+-`, `-+`, always from White's POV):
   - off the position *before* the move: the engine's actual best move there and how it refutes the
     blunder, e.g. `( 8. dxc6 Qxd1+ 9. Kxd1 bxc6 10. e4 Nd7 11. a3 Nb6 $10 )` — read on the page as
     **Better was**
   - off the move's own resulting position: the engine's best continuation from there, i.e. how the
     blunder *should* have been punished, in case the real opponent missed it — read on the page as
     **Best continuation**, shown even if it happens to match what the opponent actually played next

   Both lines are capped at `--pv-length` half-moves (default 8).

   ```bash
   .venv/bin/python scripts/analyze_games.py            # 0.3s of search per position (default)
   .venv/bin/python scripts/analyze_games.py --depth 18  # or a fixed depth instead
   ```

   `analyzed_games/` is meant to be committed to git, so rebuilding the docs doesn't require
   re-running the (slower) Stockfish pass unless `daily_games/` changed.

3. **`scripts/publish_games.py --player <name>`** reads a source directory of PGNs (default
   `daily_games/`, but pass `--source analyzed_games` to use the Stockfish-analyzed version) and
   writes **`docs/`**:
   - `docs/index.md` — a table linking to every game, with date/players/result/opening/blunder count
   - `docs/games/<id>.md` — per-game page: info table; an **Opening theory** section (see below); one
     section per blunder by `<name>` (the movetext since the previous diagram, the engine's refutation
     under **Better was:** and its punishment line under **Best continuation:** — each with its eval
     symbol, both shown before the board diagram with a red arrow for the move played); and the full
     PGN in a collapsible block
   - `docs/games/<id>/<id>.pgn`, `docs/games/<id>/blunder_*.svg`, and `docs/games/<id>/opening_deviation.svg`
     — the downloadable PGN and board diagrams referenced by the page above

   `--player` is matched case-insensitively against the PGN's `White`/`Black` headers and is
   **required** — there's no default. A game where that name isn't a player still gets a page, just
   without a blunders section.

   The **Opening theory** section uses `scripts/openings.py`, backed by the
   [lichess-org/chess-openings](https://github.com/lichess-org/chess-openings) dataset
   (`data/openings/*.tsv`, downloaded once and committed to this repo). It shows, in order: the
   **Opening moves** played while still in cataloged theory; a diagram of the position right before the
   game left it; a sentence naming who played that first move — `<name>`, or the opponent (in which
   case `<name>` never actually got the chance to deviate); and a few example cataloged lines that were
   still available at that point. Note this only covers *named* lines in that dataset, not every
   reasonable book move, so a "deviation" it reports isn't necessarily objectively bad — just unnamed
   in this particular dataset.

   ```bash
   .venv/bin/python scripts/publish_games.py --player "Magnus Carlsen" --source analyzed_games
   ```

   Both scripts are idempotent — output directories are fully regenerated on each run, so they always
   match exactly what's in the source directory. Neither script commits or pushes; review the diff
   and push when ready.

A "blunder" always means a move played by `--player` carrying NAG `$2` (Mistake), `$4` (Blunder), or
`$9` (Miss).

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`scripts/analyze_games.py` also needs the `stockfish` binary on the system (`/usr/games/stockfish` on
Debian/Ubuntu — installed via `apt install stockfish`).

## Configuration

Both scripts need to know **who** (`--player`) and, optionally, **where your games live**
(`--data-dir`, if not this repo's own checkout). Passing these as flags every time gets old fast, so
either can also come from a `.env` file instead:

```bash
cp .env.example .env
# then edit .env:
#   CHESS_PLAYER=yourusername
#   CHESS_DATA_DIR=/path/to/your/games   (omit to use this repo's own checkout)
```

`.env` is gitignored — it's local machine config, never committed, and this repo never hardcodes a
player name or a games location itself. A flag on the command line always overrides `.env`.

`--data-dir` (or `CHESS_DATA_DIR`) just needs `daily_games/` in it; `analyzed_games/` and `docs/` get
written alongside. It doesn't need to be this repo, or even a git repo at all — a common setup is a
**separate sibling repo** holding just the games/analysis/generated pages, so this repo stays pure,
reusable tooling with no game data of its own, and the games repo can be published under GitHub Pages
independently. Nothing here assumes that split, though — dropping `daily_games/` straight into this
repo works too.

If you're using a Claude Code skill (see `.claude/skills/publish-games/`) to automate steps 2–3, it
relies on the same `.env` — configure that once and the skill needs no per-project edits.

## Adding new games

1. Drop each PGN export into `daily_games/` (in whichever data dir you're using) as the next number,
   e.g. `daily_games/3.pgn` — one game per file (see above).
2. Run `scripts/update_games.sh` — a one-line wrapper for the two steps below, using `.env` for
   `--player`/`--data-dir`:
   ```bash
   scripts/update_games.sh
   ```
3. Review with `git status` / `git diff` (in the data dir), then commit and push.

`scripts/update_games.sh` just chains:
```bash
.venv/bin/python scripts/analyze_games.py
.venv/bin/python scripts/publish_games.py --source analyzed_games
```

**Already-analyzed games are skipped automatically.** `analyze_games.py` treats a game as done once
`analyzed_games/<id>.pgn` exists — the Stockfish pass is the slow part, and a game's own source PGN
never changes once added, so re-running after adding new games only analyzes the new ones. Pass
`--force` to redo everything (e.g. after changing the analysis logic itself, as happened a few times
while building this). `publish_games.py` has no such skip — it's cheap, and always fully regenerating
`docs/` means every page reflects the current script logic, not just whatever was true when it was
first generated.
