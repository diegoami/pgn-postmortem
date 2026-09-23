# pgn-postmortem

[![CI](https://github.com/diegoami/pgn-postmortem/actions/workflows/ci.yml/badge.svg)](https://github.com/diegoami/pgn-postmortem/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)

Turn a folder of PGN chess games into a set of Markdown post-mortems you can browse on GitHub. Every
blunder a chosen player made gets a board diagram, the move the engine preferred, how the mistake
should have been punished, and an opening-theory breakdown showing where the game left known lines.

Everything runs locally with [Stockfish](https://stockfishchess.org/), and the output is plain Markdown
and SVG. There's no account and no server, and the site lives in git.

**[→ Live demo](https://diegoami.github.io/pgn-postmortem/)**: five classic games, from Chigorin–Steinitz
(1892) to Carlsen–Anand (2014). The same pages are also [browsable on GitHub](examples/docs/index.md).

<table>
<tr>
<td width="50%"><img src="examples/docs/games/1/blunder_4_move32w.svg" alt="Position before 32. Bb4"></td>
<td>

### Move 32. Bb4 by Mikhail Chigorin (Blunder)

**Moves since the previous diagram**: 29. Ne6+ Kf6 30. Re7 Rge2 31. d5 Rcd2

**Better was:** 32. Rxb7 Bh5 33. Rb3 Rxd5 34. Nf4 Rxd6 35. Nxh5+ Ke7 +-

**Best continuation:** 32... Rxh2+ 33. Kg1 Rdg2# -+

<sub>Excerpt from [game 1](examples/docs/games/1.md): World Championship 1892, round 23. Chigorin was
winning, then walked into mate in two.</sub>

</td>
</tr>
</table>

## Features

- **Independent engine analysis.** Stockfish re-evaluates every position itself. Any annotations the
  PGN already carries are ignored, since site exports (chess.com's, for example) are inconsistent about
  what they attach where.
- **Judged by win probability, not raw centipawns.** Evals are converted to win % using
  [lichess's logistic fit](https://lichess.org/page/accuracy), and a move is flagged by how many win %
  points it threw away (default thresholds are lichess's own: 10 / 20 / 30 for Inaccuracy / Mistake /
  Blunder). Going from mate-in-4 to mate-in-9 is a huge centipawn swing but costs nothing, so it isn't
  flagged. The same swing in an equal position is.
- **Two engine lines per mistake.** *Better was* is what should have been played. *Best continuation*
  is how the mistake should have been punished, which is useful when the real opponent missed it.
- **Opening theory.** Each game is matched against the ~3,800 named lines in
  [lichess-org/chess-openings](https://github.com/lichess-org/chess-openings). The page shows the
  position where the game left known theory, who left it, and which named lines were still available
  at that point.
- **Any player, any collection.** Filter to one player (`--player yourname`) to review your own games,
  or use `--player '*'` to annotate both sides of master games.
- **Standard, reusable output.** The analyzed PGNs are ordinary PGN files: an eval comment on every
  move, standard NAGs (`$2`/`$4`/`$6`), and engine lines as variations ending in position symbols (`±`,
  `-+`, ...). They load into any chess GUI.
- **Incremental and deterministic.** Only new games are sent to Stockfish. Pages are fully regenerated
  on each run and the output is byte-identical, which the test suite checks against `examples/`.

## Quickstart

Requires Python 3.10+ and a `stockfish` binary on your `PATH` (`apt install stockfish`,
`brew install stockfish`, ...).

```bash
git clone https://github.com/diegoami/pgn-postmortem.git && cd pgn-postmortem
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # preconfigured for the bundled examples/
scripts/update_games.sh     # analyze new games, then regenerate docs/
```

### With your own games

1. Edit `.env` and set `CHESS_PLAYER` to your username as it appears in the PGN `White`/`Black`
   headers, and `CHESS_DATA_DIR` to a directory of your own.
2. Put your games in `$CHESS_DATA_DIR/daily_games/` as `1.pgn`, `2.pgn`, ..., **one game per file**.
3. Run `scripts/update_games.sh`, then open `$CHESS_DATA_DIR/docs/index.md`, or push the directory to
   GitHub to browse it there.

A handy setup is to keep your games in a **separate repository** (`daily_games/`, `analyzed_games/`,
`docs/`), so this one stays pure tooling and your games repo can be published independently, for
example with GitHub Pages.

## How it works

```
daily_games/*.pgn ──analyze_games.py──▶ analyzed_games/*.pgn ──publish_games.py──▶ docs/
   (your PGNs)        (Stockfish)         (evals + NAGs +        (Markdown)        index.md
                                            engine lines)                           games/<id>.md + SVGs
```

**[`scripts/analyze_games.py`](scripts/analyze_games.py)** keeps only the mainline of each game,
evaluates every position, and writes a clean annotated copy. For each flagged move it attaches two
variations, each capped at `--pv-length` half-moves:

```pgn
32. Bb4 $4 { -999.98 } ( 32. Rxb7 Bh5 33. Rb3 Rxd5 34. Nf4 Rxd6 35. Nxh5+ Ke7 $18 )
32... Rxh2+ { -999.99 } ( 32... Rxh2+ 33. Kg1 Rdg2# $19 ) 0-1
```

The first variation hangs off the position *before* the move (**Better was**). The second hangs off
the position *after* it (**Best continuation**). Games already present in `analyzed_games/` are
skipped; `--force` redoes them all.

**[`scripts/publish_games.py`](scripts/publish_games.py)** reads the analyzed PGNs and writes:

| Output | Contents |
|---|---|
| `docs/index.md` | One row per game: date, players, result, opening, blunder and inaccuracy counts |
| `docs/games/<id>.md` | Game info, opening-theory section, every flagged move in order (inaccuracies folded under `<details>`), full PGN |
| `docs/games/<id>/*.svg` | Board before each flagged move, with the move played as a red arrow, plus the opening-deviation position |

A "blunder" on these pages means a move by `--player` rated Mistake (`$2`), Blunder (`$4`) or Miss
(`$9`). Note that the opening matching only covers *named* lines in the dataset, so a "deviation" means
"no longer in a named line", not "a bad move".

Each source file must contain **exactly one game**. Every output path is derived from the filename, and
python-chess silently reads only the first game of a multi-game file, so a file with more than one game
is skipped with a warning rather than losing games without a trace.

## Configuration

Every setting can be passed as a flag or set in `.env` (see [`.env.example`](.env.example)). A flag
always wins.

| Flag | `.env` variable | Default | Meaning |
|---|---|---|---|
| `--player` | `CHESS_PLAYER` | *(required)* | Whose moves to review (case-insensitive), or `*` for both sides |
| `--data-dir` | `CHESS_DATA_DIR` | repo root | Directory containing `daily_games/`; outputs are written next to it |
| `--time` | `ANALYSIS_TIME` | `0.3` | Seconds of search per position |
| `--depth` | `ANALYSIS_DEPTH` | — | Fixed search depth instead of a time limit |
| `--inaccuracy-threshold` | `ANALYSIS_INACCURACY_PCT` | `10` | Win % points lost to flag an Inaccuracy |
| `--mistake-threshold` | `ANALYSIS_MISTAKE_PCT` | `20` | … a Mistake |
| `--blunder-threshold` | `ANALYSIS_BLUNDER_PCT` | `30` | … a Blunder |
| `--pv-length` | — | `8` | Max half-moves per engine line |
| `--force` | — | off | Re-analyze games already in `analyzed_games/` |
| `--source` | — | `daily_games` | Which directory `publish_games.py` reads (`update_games.sh` uses `analyzed_games`) |

## Claude Code skill

[`.claude/skills/publish-games`](.claude/skills/publish-games/SKILL.md) is a
[Claude Code](https://claude.com/claude-code) skill for this workflow. Say "I added new games, publish
them" and it runs the pipeline using your `.env`.

## Development

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest          # unit tests, a golden-file test against examples/, and a Stockfish smoke test
.venv/bin/ruff check .
```

If you intentionally change the page output, regenerate the golden files:

```bash
.venv/bin/python scripts/publish_games.py --player '*' --data-dir examples --source analyzed_games
```

## Credits

- [python-chess](https://github.com/niklasf/python-chess) for PGN parsing, the engine protocol and the
  SVG boards
- [Stockfish](https://stockfishchess.org/) for the analysis
- [lichess-org/chess-openings](https://github.com/lichess-org/chess-openings) (CC0) for the opening
  names, bundled in `data/openings/`
- [lichess's accuracy page](https://lichess.org/page/accuracy) for the win % model and default
  thresholds

## License

[MIT](LICENSE)
