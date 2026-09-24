# Plan: a library that turns a PGN collection into a book

Status: **planning**. This is the direction behind requests F-1 to F-3 in
[`ROADMAP.md`](../ROADMAP.md); it is not a shaped request, and nothing in it is agreed for
implementation. Each request is shaped (and, in OpenCode mode, designed and agreed) before any work
starts. Nothing below is implemented yet, except what the "Existing spike" section lists (on the
`book-poc` branch).

## Goal

A player's games, collected over years and scattered across files, sites and old databases, become a
book about them in the style of the classic "My Memorable Games" collections. It's readable as a
Wikipedia-style website and as an EPUB, offline and on a phone.

Per-game blunder reports aren't the point, since lichess already does those. The point is the book.

## Two layers, built in this order

```
            ┌──────────────── pipeline (layer 2, later) ─────────────────┐
 fetch ───▶ │  PGN files  ──▶  LIBRARY (layer 1, first)  ──▶  files    │ ───▶ publish
 chess.com  │                  read · analyze · select ·     site/      │      folder, rclone,
 lichess    │                  write · render                book.epub  │      GitHub Pages,
 git repos  └────────────────────────────────────────────────────────────┘      email/Kindle
```

**Layer 1, the library.** It's published on PyPI. Its contract is simple: **PGN in, files out.** It
knows nothing about websites, accounts, schedules or hosting. It works as a Python API and as a CLI.

**Layer 2, the pipeline.** A thin wrapper around the library that fetches games from somewhere,
calls the library and puts the output somewhere. It comes later, and it's a separate concern from the
library (it may become a separate package or a template repository).

Nobody hosts anything for anybody: users run both layers on their own machine or in their own CI.

---

## Layer 1: the library

### Input
- One or more PGN collections: files, directories or globs, or PGN text or streams. Multi-game files
  are the normal case.
- **The player:** a name plus aliases (`"Diego Amicabile"`, `"diegoami"`, `"Amicabile, Diego"`, ...),
  matched case-insensitively against White/Black. Games the player isn't in are ignored. A mode with
  no player turns a master-game collection into a book about the collection instead.
- Games are identified by their content, so duplicates across files are kept once. This already
  exists in the spike.
- **Existing annotations are stripped:** comments, variations, NAGs and engine headers. These are
  typically stale notes from old engines.

### Analysis (optional step)
- Stockfish runs where the user runs the library, in parallel, and caches results in a directory the
  user chooses, so it's incremental.
- **Interchange format: standard `[%eval ...]` comments** (what lichess exports use) instead of
  today's own `{ +0.23 }` format. As a result, **PGNs that already carry evals need no Stockfish at
  all**, for example a lichess export with evals.
- Without evals the book can still be built: every game gets an article, but there's no quality-based
  selection and no critical moments.

### Selection: the featured chapters
Measures taken from the evals include the player's accuracy (lichess formula), the opponent's
accuracy, the rating difference, game length, and how long the player stayed in the fight.

- **Best wins:** high accuracy, strong opponent, a real fight, comebacks.
- **Best losses:** hard-fought games where the player played well against a strong opponent and the
  game wasn't decided by one early blunder. (Explicitly *not* a "worst games" chapter.)
- **Best draws:** hard-fought draws, or saves from difficult positions.

The number of games per chapter and the minimum length are configurable. The weights for each measure
are tuning work to do on real collections.

### Structure of the book
- **Career article** ("Diego Amicabile (chess player)"):
  - an infobox: names and handles, active years, number of games, peak ratings per rating pool,
    wins/draws/losses
  - career by year
  - repertoire with scores
  - most frequent opponents
  - notable games
- **Featured chapters:** best wins, best losses, best draws.
- **An article for every game**, not only the featured ones:
  - an infobox: event, date, players, ratings, result, opening
  - a lead paragraph
  - the moves with notes at the critical moments
  - diagrams with captions
  - a conclusion
  - the PGN, which can be downloaded
  - previous/next navigation
- **Revision mode:** at each critical moment, "What would you play?", with the answer revealed on tap.
- **Game index:** by year and event.

### Prose
- **Templates** built from the engine facts. This is the default: free, offline and reproducible.
- **LLM (optional extra, `pip install <name>[llm]`):** any OpenAI-compatible endpoint, with the user
  bringing their own key. DeepSeek is the documented default.
  - It works only from facts the engine gives it.
  - Chess moves it mentions are checked against those facts, and a note that fails the check falls
    back to the template.
  - Responses are cached, so rebuilding costs nothing.
  - Default scope: featured games only. Every game is available as an option.
- **Language:** English.

### Output
- **Static site:** Wikipedia-style, mobile-first, works offline and from `file://`, no server needed.
  Boards are drawn in HTML and CSS with one shared piece set, so a book of thousands of articles stays
  small. The markup is semantic and themeable.
- **EPUB 3:** written directly, since EPUB is just XHTML plus a zip file. That avoids `ebooklib`,
  which is AGPL. Diagrams are inline SVG, and they need testing in Apple Books, Google Play Books and
  Kindle (Send-to-Kindle converts EPUB, and its SVG support must be checked; PNG fallback if needed).
- **Later:** a single-file HTML version, and PDF.

### API sketch (to refine)
```python
from <name> import Collection, Book

games = Collection.read(["games/**/*.pgn"], player="Diego Amicabile", aliases=["diegoami"])
games.analyze(time=0.3, cache="analysis/")          # optional; skipped where [%eval] exists
book = Book(games, title="My Memorable Games", prose="template")   # or an LLM prose object
book.write_site("site/")
book.write_epub("my-games.epub")
```
```bash
<name> build games/ --player "Diego Amicabile" --alias diegoami --site site/ --epub my-games.epub
```

### Demo
The README demo should be a book generated from a well-known public-domain collection, such as
Capablanca's games. It shows at a glance what the library does for "any player", and a live demo site
for it would be built by CI.

---

## Layer 2: the pipeline (after the library ships)
- **Inputs:** PGN collections (local, URL, git repo), chess.com archives, lichess export. Incremental,
  and without duplicates across sources.
- **Outputs:**
  - a local folder
  - rclone (Google Drive, Dropbox, OneDrive, S3, …)
  - GitHub Pages
  - email / Send-to-Kindle for the EPUB
- **Config:** one `pgn-postmortem.toml` per workspace (player, sources, outputs, LLM settings).
- **Running it:** a local CLI with cron or Task Scheduler, a Docker image, or a GitHub template repo
  with a nightly Action (the user owns the repo, the Pages site and their API key).

## Existing spike (`book-poc`, commit `e90ef99`)
| Spike piece | Goes to |
|---|---|
| Package layout, CLI skeleton | Library (restructure around the API above) |
| PGN collection reading, aliases, content IDs, duplicate removal, stripping annotations (`ingest.py`) | Library core |
| Parallel Stockfish analysis (`analysis.py`) | Library (switch to `[%eval]`) |
| chess.com / lichess / git sources (`sources.py`) | Pipeline |
| `pgn-postmortem.toml` config (`config.py`) | Pipeline |
| Legacy Markdown pages (`markdown_site.py`) | Decide: keep as a secondary renderer, or retire |

Tested on real data: 1,791 games from DA_chessgames, chess.com and lichess. 341 games found in more
than one source were merged, and one broken game was skipped.

## Milestones
1. **Library 0.1:**
   - reading collections and analysis with `[%eval]`
   - every game as an article
   - career article
   - three featured chapters
   - template prose
   - static site and EPUB
   - tests, docs, Capablanca demo
   - PyPI release
2. **Library 0.2:** LLM prose as an extra (bring your own key), revision mode polish, EPUB tested on
   e-readers.
3. **Pipeline:** sources, outputs, config, Docker image, GitHub template repo.

## Open decisions
- **Package name.** All free on PyPI as of 2026-09-24: `pgnbook`, `pgn-book`, `pgn2book`,
  `chessbook`, `pgn-memoir`, `chess-memoir`, `memorable-games`, `pgnwiki`, `pgn-postmortem`.
  - Should the library keep this repo's name or get its own?
  - Is the pipeline a separate package or repo?
- **License.** python-chess is GPL-3.0. MIT code can depend on it, but anything that bundles it, such
  as a Docker image, is subject to GPL. Options: keep MIT, or switch to GPL-3.0 for simplicity.
- **Where Diego's own book lives:** a new repo, `chessgamescollection`, or local only.
- **The Markdown pages:** keep them or retire them.
- **Selection weights:** tune them on DA_chessgames once analysis is allowed to run.
