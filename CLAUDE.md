> Guidance for Claude Code. OpenCode uses [`AGENTS.md`](AGENTS.md); the shared
> principles and the verdict protocol are in [`PRINCIPLES.md`](PRINCIPLES.md).
> **Read it before implementing.**

# The Claude Code mode

This file records the Claude-specific process and the project slot.

## The process

- Claude **implements** the change on a branch, and opens a pull request when a
  remote exists.
- The review is a **fresh-context session** — a new session that has not seen
  the implementation. **The reviewer is the same model family by default; no
  cross-family reviewer is required.** The mechanism may instead be an
  **external process** from another family (for example `codex exec`, or
  `opencode run -m <provider>/<model>`); when it is, record the tool and the
  model id in the review.
- There is **no design stage** and **no AGREE/BLOCK marker**. The review is
  recorded per [`reviews/README.md`](reviews/README.md).
- **Fallback:** a new session, or the external process, recorded. The rules are
  in the protocol.
- The builder fixes findings in the same change; a finding the builder disagrees
  with goes to the owner, not around the reviewer.
- The **owner may review** as an independent option, but an owner is not
  automatically a fresh context — and is not one if they directed or wrote the
  change.
- The **owner merges** (`PRINCIPLES.md`), unless the project slot records
  `merge: auto`. The owner may also ask for a review by OpenCode's process
  instead, when a cross-family check is wanted.

Materiality, fallback, waiver and the defect path are in `PRINCIPLES.md`; the
bootstrap applies as written there — one review, not two stages.

## Project slot

<!-- SLOT:BEGIN -->

- **product:** pgn-postmortem. It turns chess games (PGN) into analyzed
  post-mortems, and is growing into a library that turns a player's whole
  collection of games into a Wikipedia-style site and an EPUB book about that
  player, with a pipeline around it that fetches games and publishes the
  output. It is for chess players who want to reread their own games, on a
  phone and offline, without operating a chess GUI. The owner is its first
  user, with their own archive (github.com/diegoami/DA_chessgames, chess.com,
  lichess). The direction is in [`docs/book-plan.md`](docs/book-plan.md) and the
  queued work in [`ROADMAP.md`](ROADMAP.md). The owner's own book lives in
  `diegoami/chessgamescollection`, the owner's workspace that uses the library
  (decided 2026-09-24, `docs/book-plan.md`).
- **harness:** adopted from `harness_template` release `r4` (commit
  `39c29e3`) on 2026-09-24. Modes: both; the owner picks the mode of each
  change when it starts (the iteration table in [`PLAN.md`](PLAN.md)). The
  owner's usual way of working is Claude Code mode, with releases reviewed
  by a model that is not Claude. Those milestone reviews are not in `r4`:
  they are on `harness_template`'s untagged `main`, and the owner plans to
  take them from its next tagged release (expected to be `r5`), adopted as
  its own reviewed change before F-1's first release at the end of F-1.4
  (owner, 2026-09-24). Since those rules want a release's claims written
  before its work, F-1's claims are its done-when items in `ROADMAP.md`,
  fixed when #3 landed (`7476e54`) before any F-1 work began; with no earlier
  tag, F-1's first milestone review covers the range from that commit.
- **paths to inspect:** `scripts/` (the code), `tests/`, `README.md`,
  `docs/book-plan.md`, `ROADMAP.md`, `.claude/skills/publish-games/SKILL.md`,
  `.github/workflows/`, `pgn_postmortem/` (the library of F-1). The older
  spike toward the book, which F-1.1 reused parts of, is on the branch
  `book-poc`, not on `main`.
- **the canonical source:** `scripts/*.py` for the Markdown pipeline's behaviour,
  `pgn_postmortem/` for the library's; `README.md` for what a
  stranger needs. Generated, never edited by hand or cited as a source:
  `examples/docs/**` (written by `scripts/publish_games.py`) and
  `examples/analyzed_games/**` (written by `scripts/analyze_games.py`),
  `tests/golden/site/**` (written by `pgn-postmortem site`, command below) and
  `tests/fixtures/site/analyzed/**` (written once by `pgn-postmortem analyze`,
  command in `tests/test_site.py`); change the code and regenerate. `data/openings/*.tsv` is a copy of the
  third-party lichess-org/chess-openings dataset (CC0): refresh it from
  upstream, never edit it.
- **paths to normally ignore:** `.venv/` (the local environment),
  `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/` (tool
  output); `data/openings/*.tsv` (about 3,800 rows; grep it, do not read it
  whole); `examples/docs/**` and `examples/analyzed_games/**` (generated, see
  above; open one file when a check points at it); any workspace `.cache/`
  (downloaded archives and cloned repositories); `.claude/worktrees/` (agent
  worktrees: full copies of the repository, git-ignored).
- **never read or echo:** `.env` and `.env.*` other than `.env.example` (the
  owner's player name and local data paths); the value of any API-key variable
  (`DEEPSEEK_API_KEY`, or whatever a config names in `api_key_env`); `~/.ssh/`
  and `gh` credentials; absolute paths of the owner's machine (e.g. the
  location of the owner's games repository) in any committed file.
- **merge:** owner
- **design:** required
- **the gates table:**

  | gate | command | covers | when | repeats | failure model |
  |---|---|---|---|---|---|
  | lint | `.venv/bin/python -m ruff check .` | style, import order, bugbear, pyupgrade (rules in `pyproject.toml`) | every change, locally; CI on every push to `main` and every pull request | 1 | deterministic |
  | tests | `.venv/bin/python -m pytest -q` | unit tests (win %, move and position classification, openings lookup, PGN reading, `.env` loading); a golden-file test that regenerating `examples/` reproduces `examples/docs/` byte for byte; the single-player filter; a Stockfish smoke test (a forced mate must be flagged with both engine lines attached); the library (`pgn_postmortem/`) on the fixture collection in `tests/fixtures/collection/`: reading (multi-game files, globs across directories, player aliases, duplicates kept once by the owner's identity rule, comments, variations and NAGs stripped, file names with zero-padded dates that list in date order), analysis (a forced mate flagged in `[%eval]` output, nothing analyzed on a second run while games only read into the output directory are still analyzed, analyses kept when games are read into the output directory again, also under a file name from before the padding, the same output with two workers as with one, a stop at the first engine failure) and its command line run end to end as a subprocess, through `python -m` and through the installed `pgn-postmortem` script; the site (`pgn_postmortem/site.py`) built from the already-analyzed fixture in `tests/fixtures/site/` (no Stockfish): a golden-file test that it renders to `tests/golden/site/` byte for byte, one article per game with every link relative and resolving (files and anchors), the fixture's critical moments as listed by hand, each with its question and an answer hidden in a closed `<details>`, games without analysis (a source's own `[%eval]` included) built with no critical moment, the analyzed copy of a game preferred when read with its unanalyzed one, headers with `<`, `>`, `&` and quotes escaped into well-formed pages, a malformed `Date` (`²019.01.01`) filed as undated instead of stopping the build, a rebuild removing the stale pages it wrote whatever their names and never a file it did not write, and the `site` subcommand as a subprocess; results for games whose result was not recorded (ROADMAP F-5), on the hand-written fixtures in `tests/fixtures/site/synthetic/` (not generated; its README says what each game is): a result presumed from the final `[%eval]` at the default 70% threshold (a win at 73%, a loss at 27%, a draw at 34% and at 66%) in the infobox, lead, end of the moves, conclusion and index, the threshold parameter used, winning chances exactly at the threshold counting as a win for either side, and any value outside 55–95 rejected before anything is written, by `build_site` up front even for an empty collection, the board first (checkmate, stalemate, insufficient material, analyzed or not), a mate score giving the win to the side with the mate, "not recorded" wording with no bare `*` outside the PGN section, the `Result` header, `PostmortemId` and file names unchanged, a presumed win never said to come from outside the position, and counts of two or more reading "inaccuracies"; moves that changed the expected result (ROADMAP F-6), on the hand-written fixtures in `tests/fixtures/site/swings/` (not generated; its README says what each move is): a White swing from level to Black winning and a Black swing from Black winning to level, each of 10–20 points with a different engine first choice, made critical moments with their question, better line, refutation and a note saying how the expected result changed; no moment for a band change in favour of the side that moved, for one costing less than 10 points, for a 10–20-point loss inside one band, or for a band change that was the engine's first choice (no line stored before it, or only the previous move's refutation starting with the move played); a 20-point moment that is also a swing shown once, its note saying the expected result changed, and a 20-point moment that is not a swing saying nothing about it; chances exactly at the upper or lower edge counting as White or Black winning, the `outcome_bands` pair used, and invalid pairs (lower ≥ upper, a value outside its half, NaN, infinities) rejected by `build_site` up front even for an empty collection; swings counted in the infobox, the lead (whose wording stays true for them), the index and the build report; unanalyzed games still without moments; and the 10-point floor following the inaccuracy threshold in use | every change, locally; CI on Python 3.11 and 3.13 with Stockfish and the package (`pip install -e .`) installed | 1 | deterministic; the Stockfish tests search to a fixed depth, and each game starts from a fresh engine state (`ucinewgame`), so the output does not depend on which worker analyzed which game; they are skipped locally when no `stockfish` binary is found (CI always installs it) |


  Only the two gates above decide a merge. After a merge, one **post-merge
  check** runs that cannot block it: `.github/workflows/pages.yml` builds and
  deploys the demo site from `examples/docs/` on a push to `main` that touches
  `examples/docs/**` or the workflow. It depends on network and GitHub
  availability, so a red run is re-run once. A second red run is
  investigated: only a failure caused by this repository (the workflow or the
  content of `examples/docs/`) is a defect, handled by the defect path in
  `PRINCIPLES.md`; an outage of GitHub or the network is not.

  A change to the page output updates the golden files in the same commit:
  `.venv/bin/python scripts/publish_games.py --player '*' --data-dir examples --source analyzed_games`
  for the Markdown pipeline, and
  `.venv/bin/python -m pgn_postmortem site tests/fixtures/site/analyzed --player "Ada Example" --alias adaex --alias "Example, Ada" --out tests/golden/site`
  for the library's site.
- **conventions:** English everywhere: page and book text, comments,
  commits, records. Commit messages are an imperative summary line and a body
  saying why. Dependencies are pinned in `requirements*.txt`. Nothing is
  hand-edited in generated output. **Planning is not building**: while the
  owner is planning, the output is records (roadmap rows, design records,
  owner decisions), never code; a long or costly run on the owner's data (for
  example analyzing the whole archive with Stockfish) starts only when the owner
  asks for it.
- **decided, and not to be re-opened:**
  - Moves are graded by win % lost (lichess's logistic fit and its 10/20/30
    thresholds), not raw centipawns: mate-in-4 becoming mate-in-9 is
    deliberately not flagged.
  - Annotations in source PGNs are ignored and stripped (chess.com exports
    attach them inconsistently; old collections carry stale Fritz/Hiarcs notes
    in German), and every game is re-analyzed.
  - The current pipeline takes one game per file and skips a multi-game file
    with a warning, instead of silently reading only its first game.
  - Book prose comes from DeepSeek by default, with every other user bringing
    their own key for any OpenAI-compatible API, and falls back to templates
    without a key. The Claude API is ruled out on cost.
  - The book is in English; its chapters are best wins, best *losses* and best
    draws (no "worst games" chapter); every game gets its own article.
  - The deliverable is the tool and the process. The owner hosts nothing and
    maintains no one else's repository or pages; Stockfish runs wherever the
    user runs the tool.
  - Architecture: first a library (PGN collections in, site and EPUB out),
    then a pipeline around it (fetch in, publish out).
- **open work:** [`ROADMAP.md`](ROADMAP.md), including F-1's open questions
  (the licence among them); the direction, and the decisions still open there
  (the licence, whether the pipeline is a separate package, the Markdown
  pages, the selection weights), in [`docs/book-plan.md`](docs/book-plan.md).

<!-- SLOT:END -->
