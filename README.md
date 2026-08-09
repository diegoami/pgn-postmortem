# chess_with_claude

Turns a folder of PGN chess games into a browsable set of GitHub-viewable Markdown pages, highlighting
every blunder a chosen player made — with a board diagram before each one, the engine's refutation,
how the game actually continued, and an opening-theory breakdown showing where (and if) the player
left known theory.

Works with any standard PGN collection and any player name — nothing here is tied to a particular
chess site or person. Move-quality detection comes from an independent local
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

## Where the games live

By default, both scripts treat this repo's own checkout as the data directory — drop `daily_games/`
in here and everything works standalone. If you'd rather keep the games/analysis/generated pages in a
**separate repo** from these scripts (e.g. to keep this repo purely reusable tooling, or to publish the
games repo under GitHub Pages on its own), pass `--data-dir /path/to/games-repo` to either script, or
set `$CHESS_DATA_DIR`. `<data-dir>` just needs `daily_games/` (and will get `analyzed_games/`/`docs/`
written into it); it doesn't need to be a git repo at all, though committing it is how you'd track
changes and publish via GitHub Pages.

### This project's own setup

This instance of the tool is configured for user **diegoami**, whose games live in a separate sibling
repo, **[chessgamescollection](https://github.com/diegoami/chessgamescollection)**:

```
projects/
├── chess_with_claude/     (this repo: scripts, venv, requirements.txt)
└── chessgamescollection/  (daily_games/, analyzed_games/, docs/)
```

```bash
git clone git@github.com:diegoami/chessgamescollection.git ../chessgamescollection
.venv/bin/python scripts/analyze_games.py --data-dir ../chessgamescollection
.venv/bin/python scripts/publish_games.py --player diegoami --data-dir ../chessgamescollection --source analyzed_games
```

The `publish-games` Claude Code skill (`.claude/skills/publish-games/`) automates this pairing for
diegoami specifically — see that file if you're adapting it for a different player/data-dir.

## Adding a new game

1. Drop the PGN export into `daily_games/` (in whichever data dir you're using) as the next number,
   e.g. `daily_games/3.pgn`.
2. Run `scripts/analyze_games.py` to (re-)generate `analyzed_games/`.
3. Run `scripts/publish_games.py --player <name> --source analyzed_games` to regenerate `docs/`.
4. Review with `git status` / `git diff`, then commit and push.
