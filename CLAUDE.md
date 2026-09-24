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
  queued work in [`ROADMAP.md`](ROADMAP.md).
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
  `examples/analyzed_games/**` (written by `scripts/analyze_games.py`); change
  the scripts and regenerate. `data/openings/*.tsv` is a copy of the
  third-party lichess-org/chess-openings dataset (CC0): refresh it from
  upstream, never edit it.
- **paths to normally ignore:** `.venv/` (the local environment),
  `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/` (tool
  output); `data/openings/*.tsv` (about 3,800 rows; grep it, do not read it
  whole); `examples/docs/**` and `examples/analyzed_games/**` (generated, see
  above; open one file when a check points at it); any workspace `.cache/`
  (downloaded archives and cloned repositories).
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
  | tests | `.venv/bin/python -m pytest -q` | unit tests (win %, move and position classification, openings lookup, PGN reading, `.env` loading); a golden-file test that regenerating `examples/` reproduces `examples/docs/` byte for byte; the single-player filter; a Stockfish smoke test (a forced mate must be flagged with both engine lines attached); the library (`pgn_postmortem/`) on the fixture collection in `tests/fixtures/collection/`: reading (multi-game files, globs across directories, player aliases, duplicates kept once, comments, variations and NAGs stripped), analysis (a forced mate flagged in `[%eval]` output, nothing analyzed on a second run while games only read into the output directory are still analyzed, the same output with two workers as with one, a stop at the first engine failure) and its command line run end to end as a subprocess, through `python -m` and through the installed `pgn-postmortem` script | every change, locally; CI on Python 3.11 and 3.13 with Stockfish and the package (`pip install -e .`) installed | 1 | deterministic; the Stockfish tests search to a fixed depth, and each game starts from a fresh engine state (`ucinewgame`), so the output does not depend on which worker analyzed which game; they are skipped locally when no `stockfish` binary is found (CI always installs it) |


  Only the two gates above decide a merge. After a merge, one **post-merge
  check** runs that cannot block it: `.github/workflows/pages.yml` builds and
  deploys the demo site from `examples/docs/` on a push to `main` that touches
  `examples/docs/**` or the workflow. It depends on network and GitHub
  availability, so a red run is re-run once. A second red run is
  investigated: only a failure caused by this repository (the workflow or the
  content of `examples/docs/`) is a defect, handled by the defect path in
  `PRINCIPLES.md`; an outage of GitHub or the network is not.

  A change to the page output updates the golden files in the same commit:
  `.venv/bin/python scripts/publish_games.py --player '*' --data-dir examples --source analyzed_games`.
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
  (the licence among them); the direction in [`docs/book-plan.md`](docs/book-plan.md).

<!-- SLOT:END -->
