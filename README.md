# pgn-postmortem

[![CI](https://github.com/diegoami/pgn-postmortem/actions/workflows/ci.yml/badge.svg)](https://github.com/diegoami/pgn-postmortem/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)

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

Requires Python 3.11+ and a `stockfish` binary on your `PATH` (`apt install stockfish`,
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

## The library (in progress)

`pgn-postmortem` is growing into a Python library that turns a player's PGN collections into a
Wikipedia-style site and an EPUB book ([`ROADMAP.md`](ROADMAP.md), F-1). So far it reads,
analyzes and writes the site: multi-game files, directories and glob patterns in, the player's games
kept once each with every source comment, variation and NAG stripped, then a parallel Stockfish pass
that writes standard `[%eval]` comments and skips games it has already analyzed, then a static site
with an article for every game.

```bash
.venv/bin/pip install -e .
pgn-postmortem read 'collections/**/*.pgn' --player "Ada Example" --alias adaex --out games/
pgn-postmortem analyze games/ --out analyzed/ --workers 4
pgn-postmortem site analyzed/ --player "Ada Example" --alias adaex --out site/
```

```python
from pgn_postmortem import Collection

games = Collection.read(["collections/**/*.pgn"], player="Ada Example", aliases=["adaex"])
games.analyze("analyzed/", depth=18, workers=4)
Collection.read("analyzed/", keep_analysis=True).build_site("site/", title="Games of Ada Example")
```

Quote a `**` pattern so the library, not the shell, expands it. The scripts above are unchanged by it.

Every game the library writes is named `<date>-<id>.pgn` and carries two headers of its own:

- `PostmortemId`, the game's content id;
- `PostmortemAnalysis`, only on analyzed games: the engine and search limit, e.g. `Stockfish 16, depth 18`.
  `analyze` skips a game when a file in its output directory carries that game's id and this header,
  so games that `read --out` only stripped are still analyzed, even in the same directory. In turn,
  `read --out` leaves such a file alone, so reading new games into an analysis directory keeps the
  analysis already there. The skip ignores which engine and search limit the header records: to redo
  a game with other settings (a deeper search, a newer Stockfish), delete its file and run `analyze`
  again.

Two copies of a game count as one when they have the same start position, moves, result and date.
The players' names are not compared, so a game exported under two of your names or aliases is kept
once. A `FEN` header that spells out the standard starting position counts the same as none. The
`Result` and `Date` headers are compared exactly as written, which has two consequences:

- Copies with a missing, partial or differently written date (`2019.??.??` and `2019.03.14`, or
  `2019.3.14`) are kept twice. The same goes for copies with different results (`1-0` and `*`).
- Two different games with the same moves and result on the same day are kept as one. That can
  happen with a short trap, or an agreed draw in a well-known line, played against two opponents.

The exact rule is in [`pgn_postmortem/collection.py`](pgn_postmortem/collection.py).

### The site

`pgn-postmortem site` writes `index.html` (the games by year), one `games/<date>-<id>.html` article
per game and one stylesheet. Open `index.html` in a browser, or copy the folder to a phone: every link
is relative, nothing loads from the network, there is no JavaScript, and the colours follow the
system's light or dark mode. Each article has an infobox with the final position, a lead paragraph,
the moves, a conclusion and the PGN, all in template prose.

For an analyzed game the moves carry notes (`?!` inaccuracy, `?` mistake, `??` blunder), and each
**critical moment** gets a diagram and a question, "What would you play?", with the answer hidden
until you tap it. A critical moment is a move that cost its side at least 20 points of winning chances
(a mistake or a blunder), computed from the `[%eval]` comments that `analyze` wrote, with the same win
percentage and thresholds that grade the moves.

A move that changed the expected result is a critical moment too, even when it cost less. After each
move the position is *White winning* (65% or more for White), *Black winning* (35% or less) or *level*.
A move counts when it made that worse for its side (winning to level, level to losing, or winning to
losing), cost its side at least 10 points (the inaccuracy threshold in use), and the analysis shows a
better move there: an engine line that `analyze` stored at that position starts with another move. Only
the stored analysis is read, so nothing is analyzed again. Its note says how the expected result changed, for example "an inaccuracy that turned a
level game into a losing one". The bands are `build_site(..., outcome_bands=(35, 65))`: the lower one
above 0 and below 50, the upper one above 50 and below 100.

Games that have not been analyzed, or whose only
evaluations came from their source, still get an article, without notes or questions. Pass the games
and their analysis together (`site games/ analyzed/`) and the analyzed copy of each game is used.
Building again into the same folder removes the pages it wrote before for games that are no longer in
the collection; a file it did not write is never touched.

A game whose result was not recorded (`Result "*"`, or no `Result` header) still gets one. If the game
ended in checkmate, stalemate or insufficient material, the board decides it. Otherwise, if the game
was analyzed, the final position decides it: a win for the side with at least 70% winning chances (a
forced mate counts as 100%), a draw otherwise. The 70 is `build_site(..., presume_threshold=70)`, from
55 to 95. Failing both, the article says the result was not recorded. The result is shown like a
recorded one, in the infobox, the lead, after the moves, in the conclusion and in the index. The
source's `*` is left as it is: the article's PGN section shows it, and the game's id, and therefore its
file name, is computed from that `*` result, not from the result shown.

The site of the test fixture is committed in [`tests/golden/site/`](tests/golden/site/index.html).

## Claude Code skill

[`.claude/skills/publish-games`](.claude/skills/publish-games/SKILL.md) is a
[Claude Code](https://claude.com/claude-code) skill for this workflow. Say "I added new games, publish
them" and it runs the pipeline using your `.env`.

## Development

```bash
.venv/bin/pip install -r requirements-dev.txt -e .
.venv/bin/pytest          # unit tests, a golden-file test against examples/, and the Stockfish tests
.venv/bin/ruff check .
```

If you intentionally change the page output, regenerate the golden files:

```bash
.venv/bin/python scripts/publish_games.py --player '*' --data-dir examples --source analyzed_games
```

and for the library's site (the fixture's analysis is committed, so this needs no Stockfish):

```bash
.venv/bin/python -m pgn_postmortem site tests/fixtures/site/analyzed --player "Ada Example" --alias adaex --alias "Example, Ada" --out tests/golden/site
```

## Credits

- [python-chess](https://github.com/niklasf/python-chess) for PGN parsing, the engine protocol and the
  SVG boards, and the piece set by Colin M.L. Burnett that the site's diagrams use
- [Stockfish](https://stockfishchess.org/) for the analysis
- [lichess-org/chess-openings](https://github.com/lichess-org/chess-openings) (CC0) for the opening
  names, bundled in `data/openings/`
- [lichess's accuracy page](https://lichess.org/page/accuracy) for the win % model and default
  thresholds

## License

[MIT](LICENSE)
