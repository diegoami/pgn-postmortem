## Milestone review — v0.1.0, round 1

**Where I reviewed:** commit `724aa9d271a3ca54336790fa90ba9759767dba42`, checked out in a detached worktree whose `HEAD` equals that sha. The file list was obtained with `git diff --name-only 7476e54..HEAD` on the worktree (non-empty: `pgn_postmortem/`, `tests/`, `reviews/`, the plan and docs). Reviewer: DeepSeek (`opencode/deepseek-v4-pro`), run by opencode, mode: milestone review. The range's authors and `Co-Authored-By` trailers name Diego Amicabile and Claude Opus 5.5 (Anthropic); I am not of that family, so I proceed.

**Verdict table**

| claim | verdict | evidence |
|---|---|---|
| C1 (F-1.1 read & analyze) | MET | `.venv/bin/python -m ruff check .` → All checks passed!; `.venv/bin/python -m pytest -q` → 209 passed. Done-when items are covered by `tests/test_collection.py`, `tests/test_library_analysis.py`, `tests/test_analysis.py`, `tests/test_cli.py`. Owner decisions on open questions 1/3/5/6 are recorded in `ROADMAP.md` F-1. |
| C2 (F-1.2 every game an article) | MET | `tests/test_site.py::test_the_fixture_site_renders_to_the_golden_pages_byte_for_byte` and the golden sets `tests/golden/site/` and `tests/golden/site-no-history/`; regeneration commands are in the module docstring and in CLAUDE.md. Owner verdict recorded in `reviews/008-f1-2-game-articles-impl-02.md` (PR #8). |
| C3 (F-5 presumed results) | MET | `tests/test_presumed_results.py` on `tests/fixtures/site/synthetic/`, covering all ten done-when items (threshold 70% default, parameter use, 55–95 range rejection, board-first, mate score, "not recorded" wording, unchanged Result/PostmortemId/names, "inaccuracies" plural). |
| C4 (F-6 outcome swings) | MET | `tests/test_outcome_swings.py` on `tests/fixtures/site/swings/`, covering all nine items; `OUTCOME_BANDS = (40.0, 60.0)` in `pgn_postmortem/site.py:200`, and the owner's 40–60% change is recorded in F-6's block. |
| C5 (F-8 reading history) | MET | `tests/test_history.py`; `node --test 'tests/js/*.test.mjs'` → 32 pass, 0 fail; wheel check verified — `pip wheel --no-deps --no-build-isolation -w dist .` then `zipfile -l` shows `pgn_postmortem/static/history.js`. Owner check recorded in `reviews/018-…-impl-02.md`. |
| C6 (F-9 quiz list) | MET | `tests/test_quiz.py`, `tests/js/quiz.test.mjs` (in the 32 script-gate tests). Owner check recorded in `reviews/021-…-impl-02.md`. |
| C7 (F-10 lichess links) | MET | `tests/test_lichess_links.py` and the narrowed `check_links` in `tests/test_site.py:201` (20 planted bad links rejected). Owner check recorded in `reviews/023-…-impl-01.md`. |
| C8 (defect fix #7 date padding) | MET | `tests/test_collection.py::test_file_names_are_zero_padded_so_a_listing_is_chronological`, `test_dates_written_differently_are_two_games_with_the_same_padded_file_date`, and `tests/test_library_analysis.py::test_a_game_analyzed_under_an_unpadded_file_name_is_left_alone`. I removed the `zfill` and all three turned red; the identity rule is unchanged (`game_id` still hashes the date as written). |
| C9 (defect fix #24 board squares) | MET | `tests/test_boards.py`. I forced every cell to class `l` and all board tests turned red; the test also asserts no board-level `background` and no cell `background-image` in `assets/style.css`. |
| C10 (gates) | MET | lint → "All checks passed!"; tests → 209 passed (Stockfish at `/usr/games/stockfish`, none skipped); script → 32/32. CI `36194152691` verified green (`gh run view`) on Python 3.11 and 3.13. |

**Findings:** none.

**Breaks I tried that nothing needed to catch (all caught):** removed month/day zero-padding (3 tests red), collapsed every cell to one square colour (3 board tests red), turned the outcome-band edge comparisons from `>=`/`<=` to `>`/`<` (2 swing tests red). Each reproduced that the change landed and the test failed on it, so the assertions are real, not vacuous.

**Not checked:** the owner's own phone/`file://`/served-preview verdicts are recorded in the reviews as transcribed by the orchestrator and not signed by the owner; I re-checked that each is recorded, not the on-device experience itself. The two lichess URL forms were checked against lichess by the implementer; no test uses the network, and none may. The live PyPI absence (a correct absence for this milestone) and the `pages.yml` post-merge deploy are outside all claims.

— DeepSeek (opencode/deepseek-v4-pro), reviewer
AGREE


## Completion

The verdict above is copied verbatim from
https://github.com/diegoami/pgn-postmortem/issues/26#issuecomment-5840328980.
An earlier run on 2026-09-25 stopped before reviewing: opencode refused reads
outside its working directory. It posted no verdict and counts as no round
(recorded on #26). Round 1 ran from a clean working directory, with the
opencode permission settings unchanged.

- **Tag:** `v0.1.0` is annotated. `git cat-file -t v0.1.0` prints `tag`, and
  `git rev-parse v0.1.0^{commit}` prints
  `724aa9d271a3ca54336790fa90ba9759767dba42`, the reviewed candidate. The tag
  message names #26, the reviewer and the accepted gaps.
- **Release:** https://github.com/diegoami/pgn-postmortem/releases/tag/v0.1.0.
  `pip install "pgn-postmortem @ git+https://github.com/diegoami/pgn-postmortem@v0.1.0"`
  into a fresh virtual environment installs it, and `pgn-postmortem --version`
  prints `pgn-postmortem 0.1.0`.
- **Accepted gaps:** the reviewer's "Not checked" items above, and the
  non-blocking findings the owner left open, listed in the completion notes
  of `reviews/007` to `reviews/025`.
- **Next**, on the owner's go: F-1.3 (`PLAN.md`). F-11 stays parked.

— Claude (claude-opus-5-5), implementer
