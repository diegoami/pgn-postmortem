# Review 028: F-12, the Pages demo shows the library's site (pull request #28), round 01

- **Revision covered:** `44368e523df677e8d8c8dcd579e7c66462d25622` (branch `iteration-8-pages-demo`),
  on top of `origin/main` at `83406cfa145eee4d5fdd06748c8787c2c622ac4b` (the merge base). Three
  commits: `9a02a20`, `48d77a2`, `44368e5`.
- **Target proof:** after `git fetch origin`, `git rev-parse origin/iteration-8-pages-demo` gives
  `44368e5…`, which equals `headRefOid` from `gh pr view 28 --json headRefOid,files`. The local
  checkout was on the same commit, clean, and the checks below ran on it.
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
  - `tests/test_demo.py`
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that did
  not see the implementation.
- **Mode:** Claude Code, implementation review.
- **Read against:** F-12's block in `ROADMAP.md` (the spec), `CLAUDE.md`'s slot, `PRINCIPLES.md`,
  `reviews/README.md`, and review 027-02 with its Completion section (four findings carried into
  this change). The PR body was read with `gh pr view 28`.

## Checks run (2026-09-26)

- **The gates, on `44368e5`:**
  - `.venv/bin/python -m ruff check .`: `All checks passed!`
  - `.venv/bin/python -m pytest -q`: `216 passed in 11.56s` (Stockfish on PATH, so the Stockfish
    tests ran).
  - `node --test 'tests/js/*.test.mjs'` (Node v24.21.0): `tests 32`, `pass 32`, `fail 0`.
  - CI on the PR (run 36241635824, head `44368e5`): `test (3.11)` and `test (3.13)` pass.
- **The committed analysis:** each of the five files has `[PostmortemAnalysis "Stockfish 19, depth
  22"]` and a `PostmortemId` equal to its file name's id. The headers present are only the seven
  standard ones, `ECO` (four games) and the two `Postmortem*` headers. No absolute path appears
  under `examples/site/` (`grep -rnE '/home|/Users|C:\\|diego|\.cache'` finds nothing). I re-ran the
  block's command on a scratch copy of `examples/daily_games/3.pgn` (Najdorf–Fischer 1966) with
  local Stockfish at depth 22. The output is byte-identical to
  `examples/site/analyzed/1966-07-27-60ec9cded6.pgn`.
- **The GitHub dispatch run** https://github.com/diegoami/pgn-postmortem/actions/runs/36241545554:
  `workflow_dispatch` on `iteration-8-pages-demo`, head `44368e5`, conclusion `success`, `build`
  success, `deploy` skipped. Its log shows `Successfully installed chess-1.11.2
  pgn-postmortem-0.1.0`, `Wrote 5 article(s) to _site: 5 analyzed, 0 not analyzed yet, 9 critical
  moment(s).`, `baseurl: "/pgn-postmortem/markdown"` and `Destination:
  /github/workspace/_site/markdown`. I downloaded its artifact (`gh run download`) and extracted
  `artifact.tar`. It holds 39 files, the same list the PR gives:
  - **root:** `index.html`, `assets/style.css` and five `games/<date>-<id>.html`. There is no
    `quiz.html` and no link to one, and the root has `data-site="pgn-postmortem-demo"` and the
    block's title. All seven files are byte-identical to my local build with the workflow's command.
  - **`/markdown/`:** `index.html`, `index.md`, `assets/css/style.css`, `games/{1..5}.{html,md}`,
    and each game's PGN and diagrams.
  - **Rewritten links (027-02, finding 2):** `markdown/index.html` has
    `href="/pgn-postmortem/markdown/games/1.html"` … `games/5.html`, and the stylesheet link starts
    with the same prefix. `markdown/games/1.html` has
    `src="/pgn-postmortem/markdown/games/1/opening_deviation.svg"`.
- **Breaking the new test** (scratch copies and a monkeypatched `build`, run against
  `tests/test_demo.py`'s checks; the working tree stayed clean):
  - an index that lists one article twice: fails with "the index does not list each article once";
  - a broken relative link planted in one article: `check_links` fails with
    "broken: games/1966-07-27-60ec9cded6.html: href='../missing.html'";
  - the four breaks the suite keeps (a game removed, a marker stripped, a game replaced, a game
    added) pass as parametrized tests in the gate run above;
  - every `{ [%eval …] }` comment stripped, with the markers kept: all three checks pass, and the
    site has "0 critical moment(s)" (finding 1);
  - every marker rewritten to `depth 3`: `check_analyzed` passes (finding 1);
  - a duplicate copy of one game under another file name: passes, since the library reads it as five
    games and builds five articles. It is harmless to the demo, so it is not a finding.

## Findings

1. **non-blocking**: the test doesn't notice if the analysis's content is gone.
   - **Where:** `tests/test_demo.py:35-40` checks only that the `PostmortemAnalysis` header is
     present.
   - **What I reproduced:** I stripped every `[%eval]` comment from a scratch copy and kept the
     markers. `check_analyzed`, `check_same_games` and `check_site` all pass, and the site builds
     "5 analyzed, … 0 critical moment(s)". Such a demo would show none of the "what would you play?"
     questions the README now advertises. A marker that records another depth (`depth 3`) also
     passes.
   - **Why it isn't blocking:** done-when 1 asks only for the marker, and the test meets it.
   - **Suggested fix:** also assert that the demo site has at least one critical moment, or the
     count of 9 seen today. Optionally, assert that every marker ends in `depth 22`, the block's
     depth.
2. **non-blocking**: the test copies the workflow's options instead of reading them.
   - **Where:** `tests/test_demo.py:32`, `WORKFLOW_OPTIONS = ("--title", "pgn-postmortem demo —
     five classic games", "--site-key", "pgn-postmortem-demo")`, which duplicates
     `.github/workflows/pages.yml:51`.
   - **What drift it misses:** if one changes and the other doesn't (for example a `--player` added
     to the workflow), the test still passes and builds a different site from the one deployed. The
     two agree today.
   - **Suggested fix:** leave it as is and accept the post-merge run as the check, or parse the
     `pgn-postmortem site` line from `pages.yml` in the test. The builder can choose.

## What holds

- **Done-when 1.** The new test asserts exactly five games, each with the marker, the same
  `PostmortemId`s as `examples/daily_games/` (ids are content hashes, `game_id` in
  `pgn_postmortem/collection.py`, so a changed or replaced game changes its id), and exactly five
  articles whose links pass `check_links`. It also checks that each article is listed once in the
  index and that there is no `quiz.html`. Each break the done-when names stays in the suite, matched
  on its own message, and I reproduced the index and link checks failing myself.
- **The workflow matches the block:**
  - `pip install -r requirements.txt .` (non-editable, so `history.js` is carried) and the block's
    exact command with `--out _site`, built first, before `configure-pages` and the Jekyll step
    (`pages.yml:47-51`);
  - Jekyll uses the same staging and `_config.yml` as before, plus
    `baseurl: "${BASE_PATH}/markdown"` from `configure-pages`' `base_path` (`pages.yml:71`), into
    `_site/markdown` (`pages.yml:76`);
  - the triggers are exactly the block's list, plus `workflow_dispatch` (`pages.yml:12-22`);
  - no Stockfish is used.
- **027-02's findings:**
  - finding 1 is handled both ways: the deploy is guarded with
    `if: github.ref == 'refs/heads/main'` (`pages.yml:83`), and the concurrency group is
    `pages-${{ github.ref }}` (`pages.yml:32`). The dispatch run is green with deploy skipped;
  - finding 2 is shown above, on the artifact;
  - finding 3: the README sentence now reads "The Markdown pages this README describes are at the
    demo's `/markdown/`, and are also browsable on GitHub" (`README.md:16-18`);
  - finding 4: done-when 3's closing line refers to `CLAUDE.md`'s widened clause
    (`ROADMAP.md:778`). This is the only `ROADMAP.md` change, and 027's Completion section asked for
    it.
- **`CLAUDE.md`:**
  - the post-merge paragraph describes both parts, the triggers, the main-only deploy and no
    Stockfish, and it still "cannot block" a merge;
  - its defect clause adds `pgn_postmortem/**`, `pyproject.toml`, `requirements.txt` and
    `examples/site/analyzed/`;
  - `examples/site/analyzed/**` is added to the generated paths, with the command, and to the paths
    to normally ignore;
  - the tests row's covers cell describes the new test accurately.
- **`README.md`:** the demo line names the library's site of the five games, `/markdown/`, and the
  owner's book at `https://diegoami.github.io/chessgamescollection/`. Nothing else in the README
  changed.
- **Out of scope stayed out:** the file list has nothing under `tests/golden/`, `examples/docs/` or
  `pgn_postmortem/`, and there is no quiz page, redirect or Stockfish step.
- **The PR's claims hold:** the run URL, the artifact's contents, the analysis headers and the gate
  counts match what I found.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
