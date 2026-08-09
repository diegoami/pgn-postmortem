# chess_with_claude

Publishes diegoami's daily chess.com games as browsable GitHub pages, with a diagram of the board
before every blunder he made and the engine's refutation line.

## Workflow

```
daily_games/*.pgn  --[analyze_games.py]-->  analyzed_games/*.pgn  --[publish_games.py]-->  docs/
```

1. **`daily_games/<id>.pgn`** — raw PGNs as downloaded from chess.com, one file per game, numbered
   sequentially. These carry chess.com's own move-quality review (NAGs like `$2`/`$4`/`$9` and side
   variations), which turned out too inconsistent to build blunder detection on directly — chess.com
   sometimes attaches a side variation to demonstrate a punishment line rather than a genuine
   alternative to the move it actually flagged.

2. **`scripts/analyze_games.py`** re-analyzes each game independently with a local Stockfish engine
   and writes a clean copy to **`analyzed_games/<id>.pgn`**: mainline moves only (chess.com's
   variations/NAGs stripped), an eval comment on every move (pawns, White's POV, e.g. `{+0.23}`), our
   own NAG when a move's centipawn loss crosses a threshold (`$6` Inaccuracy ≥50cp, `$2` Mistake
   ≥100cp, `$4` Blunder ≥300cp), and, for a flagged move, two side variations capturing Stockfish's own
   view of the position:
   - off the position *before* the move: the engine's actual best move there and how it refutes the
     blunder, e.g. `( 8. dxc6 Qxd1+ 9. Kxd1 bxc6 10. e4 Nd7 11. a3 Nb6 )` — read on the page as
     **Better was**
   - off the move's own resulting position: the engine's best continuation from there, i.e. how the
     blunder *should* have been punished, in case the real opponent missed it — read on the page as
     **Best continuation**

   Both lines are capped at `--pv-length` half-moves (default 8).

   ```bash
   .venv/bin/python scripts/analyze_games.py            # 0.3s of search per position (default)
   .venv/bin/python scripts/analyze_games.py --depth 18  # or a fixed depth instead
   ```

   `analyzed_games/` is committed to git, so rebuilding the docs doesn't require re-running the
   (slower) Stockfish pass unless `daily_games/` changed.

3. **`scripts/publish_games.py`** reads a source directory of PGNs (default `daily_games/`, but pass
   `--source analyzed_games` to use the Stockfish-analyzed version) and writes **`docs/`**:
   - `docs/index.md` — a table linking to every game, with date/players/result/opening/blunder count
   - `docs/games/<id>.md` — per-game page: info table; an **Opening theory** line (see below); one
     section per blunder by diegoami (the movetext since the previous diagram, a board diagram with a
     red arrow for the move played, the engine's refutation under **Better was:**, and its punishment
     line under **Best continuation:**); and the full PGN in a collapsible block
   - `docs/games/<id>/<id>.pgn` and `docs/games/<id>/blunder_*.svg` — the downloadable PGN and board
     diagrams referenced by the page above

   The **Opening theory** line uses `scripts/openings.py`, backed by the
   [lichess-org/chess-openings](https://github.com/lichess-org/chess-openings) dataset
   (`data/openings/*.tsv`, downloaded once and committed to the repo): it reports how far the game's
   moves match a cataloged named opening line, and who played the first move that doesn't — diegoami,
   or the opponent (in which case diegoami never actually got the chance to deviate). Note this only
   covers *named* lines in that dataset, not every reasonable book move, so a "deviation" it reports
   isn't necessarily objectively bad — just unnamed in this particular dataset.

   ```bash
   .venv/bin/python scripts/publish_games.py --source analyzed_games
   ```

   Both scripts are idempotent — output directories are fully regenerated on each run, so they always
   match exactly what's in the source directory. Neither script commits or pushes; review the diff
   and push when ready.

A "blunder" always means a move played by **diegoami** (White or Black, detected from the PGN
headers) carrying NAG `$2` (Mistake), `$4` (Blunder), or `$9` (Miss).

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`scripts/analyze_games.py` also needs the `stockfish` binary on the system (`/usr/games/stockfish` on
Debian/Ubuntu — installed via `apt install stockfish`).

## Adding a new game

1. Drop the chess.com PGN export into `daily_games/` as the next number, e.g. `daily_games/3.pgn`.
2. Run `scripts/analyze_games.py` to (re-)generate `analyzed_games/`.
3. Run `scripts/publish_games.py --source analyzed_games` to regenerate `docs/`.
4. Review with `git status` / `git diff`, then commit and push.

The `publish-games` Claude Code skill (`.claude/skills/publish-games/`) automates steps 2–3.
