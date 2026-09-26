# Review 028: F-12, the Pages demo shows the library's site (pull request #28), round 02

- **Revision covered:** `98cacfe974799ccce06f122b560626ddb3cecd0e` (branch `iteration-8-pages-demo`),
  on top of `origin/main` at `83406cfa145eee4d5fdd06748c8787c2c622ac4b` (the merge base). Five
  commits: `9a02a20`, `48d77a2`, `44368e5`, `02d40e5` (round 01's record), `98cacfe` (the answer).
- **Target proof:** after `git fetch origin`, `git rev-parse origin/iteration-8-pages-demo` gives
  `98cacfe…`, which equals `headRefOid` from `gh pr view 28 --json headRefOid,files`. The checks
  below ran in a scratch worktree of that commit (removed afterwards); the main checkout stayed on
  `iteration-8-pages-demo` at the same commit, clean.
- **Files checked:** the pull request's file list (`gh pr view 28 --json files`), which equals
  `git diff --name-only $(git merge-base origin/main origin/iteration-8-pages-demo)..origin/iteration-8-pages-demo`:
  - `.github/workflows/pages.yml`
  - `CLAUDE.md`
  - `README.md`
  - `ROADMAP.md`
  - `examples/site/analyzed/1892-02-28-9b0f13d4d6.pgn`
  - `examples/site/analyzed/1956-03-28-347a64e837.pgn`
  - `examples/site/analyzed/1966-07-27-60ec9cded6.pgn`
  - `examples/site/analyzed/2006-11-27-5e65903b8b.pgn`
  - `examples/site/analyzed/2014-11-15-2e47c73beb.pgn`
  - `reviews/028-f12-pages-demo-impl-01.md`
  - `tests/test_demo.py`
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that did
  not see the implementation or round 01's session.
- **Mode:** Claude Code, implementation review.
- **Read against:** F-12's block in `ROADMAP.md` (the spec), `CLAUDE.md`'s slot, `PRINCIPLES.md`,
  `reviews/README.md`, round 01's record, the PR body and the builder's answer comment
  (`gh pr view 28 --comments`).

## Checks run (2026-09-26)

- **The gates, on `98cacfe`** (from the worktree root, with the main checkout's `.venv/bin/python`;
  the tests imported the worktree's `pgn_postmortem`):
  - `ruff check .`: `All checks passed!`
  - `pytest -q`: `219 passed in 13.23s` (Stockfish on PATH, so the Stockfish tests ran). Round 01
    had 216; the three new cases are the three new broken-copy tests.
  - `node --test 'tests/js/*.test.mjs'` (Node v24.21.0): `tests 32`, `pass 32`, `fail 0`.
- **Since round 01** (`git diff 02d40e5..origin/iteration-8-pages-demo`): only `tests/test_demo.py`
  and the tests row of `CLAUDE.md` changed. `git diff --stat 44368e5..98cacfe` shows no change to
  `.github/workflows/pages.yml` (its only commit in the range is `48d77a2`), so the dispatch run
  36241545554 on `44368e5`, which round 01 checked, still covers the workflow as it is.
- **The builder's reproductions, re-taken** on the committed directory in the worktree, then
  restored with `git checkout`:
  - `sed -i 's/depth 22/depth 12/'` on the 1892 game: `1 failed, 2 passed`, failing at
    `tests/test_demo.py:47` with `'Stockfish 19, depth 12', not …`;
  - every `{ [%eval …] }` removed from all five (`grep -c %eval` gives 0 for each): `2 failed,
    1 passed`, at `tests/test_demo.py:50` (`no [%eval] after …`) and `tests/test_demo.py:72`
    (`no critical moment in the site`).
- **Further breaks** (scratch copies, each run through the three checks):
  - evals stripped from one game only, or only the last `[%eval]` of one game removed:
    `check_analyzed` fails;
  - every eval rewritten to `0.00`: `check_analyzed` passes, `check_site` fails (no moment);
  - a trailing space in the marker: `check_analyzed` fails;
  - the last move of a game dropped, or a `Result` changed: `check_same_games` fails (the id
    covers moves, result and date);
  - a player's name changed, or the `PostmortemId` header rewritten: all pass. The id excludes
    names and is recomputed on reading (`game_id`, the owner's identity rule), and the site is
    unharmed apart from the name, so not a finding;
  - every variation stripped (NAGs and evals kept): all pass. See finding 1.
- **The moment check is not vacuous:** the built demo site has 9 `id="moment-…"` elements, the
  same 9 the build report counts, and the unbroken copy is checked first in each broken-copy test
  (`tests/test_demo.py:147`).
- **The committed analysis** is unchanged since round 01. Its headers are the seven standard ones,
  `ECO` (four games), `PostmortemId` and `PostmortemAnalysis "Stockfish 19, depth 22"`, and no
  machine path appears under `examples/site/` or in `tests/test_demo.py`
  (`grep -rnE '/home|/Users|/tmp|C:\\|diego|\.cache'` finds nothing). The 2006 game ends
  `35. Qh7# ( 35. Qh7# $18 ) 1-0` with no eval after the mate, as the answer says.

## Round 01's findings

1. **Resolved.** `check_analyzed` now requires the marker to read exactly `Stockfish 19, depth 22`
   (`tests/test_demo.py:47`) and an `[%eval]` after every mainline move whose position is not game
   over (`tests/test_demo.py:48-50`), and `check_site` requires at least one critical moment
   (`tests/test_demo.py:70-72`). Each fails on the break it claims, reproduced above, and the three
   breaks stay in the suite (`tests/test_demo.py:134-136`). The `CLAUDE.md` tests row describes
   exactly this.
2. **Left as is, by the owner's decision** of 2026-09-26. `WORKFLOW_OPTIONS`
   (`tests/test_demo.py:35`) still matches `.github/workflows/pages.yml:51`.

## Findings

1. **non-blocking**: stripping the engine lines is not caught.
   - **Where:** `tests/test_demo.py:71-72` asks only for at least one moment.
   - **What I reproduced:** with every `( … )` variation removed from a scratch copy (evals, NAGs
     and markers kept), all three checks pass. The site then builds 6 critical moments instead of
     9 (swings need the engine's line, so they drop out), and the remaining answers say "The
     analysis records no better move than 34... Qe3??." instead of giving the better line and the
     refutation.
   - **Why it isn't blocking:** the done-when asks for the marker only, and round 01 suggested "at
     least one critical moment" as enough. It is also an unlikely break: the library's own reading
     strips comments, variations and NAGs together, which the eval check catches.
   - **Suggested fix, optional:** assert the count seen today (9 moments), which would catch this
     and any partial loss. The builder may leave it.
2. **non-blocking**: one sentence of the post-merge paragraph says a branch dispatch builds nothing.
   - **Where:** `CLAUDE.md:132-133`, "its deploy job runs only on `main`, so a dispatch on a branch
     builds and deploys nothing".
   - **What is wrong:** read plainly, the branch dispatch builds nothing, but it does build (the
     `build` job runs, as done-when 2 relies on and run 36241545554 shows). The workflow's own
     comment has it right: "on a branch the build is checked and nothing is deployed"
     (`pages.yml:81-82`).
   - **Suggested fix:** "builds but deploys nothing". This was already in round 01's revision.

## What holds

- **Done-when 1** is met, and now beyond it: five games, the marker with the block's engine and
  depth, an eval after every move that doesn't end the game, the same `PostmortemId`s as
  `examples/daily_games/`, five articles each listed once, at least one moment, no `quiz.html`,
  and links passing `check_links`. Every break named in the test's docstring is a permanent test
  matching its own message.
- **The workflow** (`pages.yml`) is as round 01 found it and matches the block: a non-editable
  install and the block's exact command, built first into `_site`; Jekyll into `_site/markdown`
  with `baseurl: "${BASE_PATH}/markdown"`; the block's triggers plus `workflow_dispatch`; the
  deploy guarded to `main` and concurrency scoped by ref; no Stockfish.
- **`CLAUDE.md`, `README.md`, `ROADMAP.md`:** the generated-paths and ignore lists, the widened
  defect clause, the README's demo line (library site, `/markdown/`, the owner's book) and the
  single `ROADMAP.md` edit (done-when 3's closing line) are unchanged since round 01 and still
  match the block.
- **Out of scope stayed out:** nothing under `pgn_postmortem/`, `tests/golden/` or `examples/docs/`
  changed; there is no quiz page, redirect or Stockfish step.
- **The PR:** its body's test description and check output are labelled as of `44368e5` and are
  true for it; the answer comment gives the current test and the gate counts on `98cacfe`, which
  match mine.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
