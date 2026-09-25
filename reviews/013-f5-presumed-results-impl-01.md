# Review 013 — F-5, a result for games whose result was not recorded (implementation, round 01)

- **Revision covered:** `e1c4fdd1e60ce7b602c28dfe029144a2b3ccca41` (head of
  `iteration-3-presumed-results`, pull request #13). I checked out
  `origin/iteration-3-presumed-results` after a fetch. `git rev-parse HEAD`
  matched `gh pr view 13 --json headRefOid`. The merge base with `origin/main` is
  `d1fb5d839ea5659355a85e7cb1022e53c2f77a1c` (= `origin/main`).
- **Files checked (19):** I took them from `gh pr view 13 --json files`, and
  they matched `git diff --name-only d1fb5d8..e1c4fdd` exactly:
  `CLAUDE.md`, `README.md`, `pgn_postmortem/__init__.py`,
  `pgn_postmortem/site.py`, `tests/test_presumed_results.py`,
  `tests/fixtures/site/synthetic/README.md` and the 13 PGNs in
  `tests/fixtures/site/synthetic/`: `checkmate`, `insufficient-material`,
  `mate-black`, `mate-white`, `no-result-header`, `not-recorded`,
  `stalemate-analyzed`, `stalemate`, `white-27`, `white-34`, `white-59`,
  `white-66` and `white-73`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code
  subagent. It had not seen the implementation.
- **Mode:** Claude Code (`PLAN.md`, iteration 3). The contract is F-5's block in
  `ROADMAP.md`.

## What I ran

- **Gates** (fresh venv in the reviewer's worktree, with
  `pip install -r requirements-dev.txt` and `pip install -e .`, and Stockfish on
  PATH):
  - `ruff check .` gave "All checks passed!".
  - `pytest -q` gave "101 passed", with nothing skipped.
- **CI:** `gh pr checks 13` shows test (3.11), test (3.13) and GitGuardian all
  passing. The run's `headSha` is `e1c4fdd…`.
- **Golden files:**
  - I regenerated the library site with the slot's command into a scratch
    directory. `diff -r` against `tests/golden/site/` found no differences.
  - `git diff --stat d1fb5d8..e1c4fdd` is empty for `scripts/`, `examples/`,
    `tests/golden/`, `tests/fixtures/site/analyzed/`,
    `tests/fixtures/collection/` and `data/`.
- **Fixture evals:** I checked them against the library's own
  `pgn_postmortem.analysis.win_percent`:
  - 275 → 73.35 (`white-73`) and −275 → 26.65 (`white-27`), both inside their
    windows.
  - −186 → 33.52 (`white-34`, window 32–35) and 186 → 66.48 (`white-66`,
    window 65–68).
  - 100 → 59.10 (`white-59`) and 500 → 86.31 (`stalemate-analyzed`).
  - The inaccuracy counts match the grading rule. In `white-73`, Black loses
    about 11 points on 2…Nc6 and about 10.8 on 3…a6, so Black made two
    inaccuracies. `white-27` is the mirror image, with two for White.
- **Positions:**
  - `stalemate*.pgn`: 50. Qf7 stalemates Kh8.
  - `insufficient-material.pgn`: 60. Kxd2 leaves bare kings.
  - `checkmate.pgn`: 2…Qh4# is checkmate.
  - `mate-white` and `mate-black` end in legal, non-terminal positions. The
    test asserts `not is_game_over()`.
- **Rendered site:** I ran `pgn-postmortem site tests/fixtures/site/synthetic`
  and pulled the infobox, lead, end of the moves, conclusion and index entry
  for all 13 games.
  - Every page shows the expected result in all five places.
  - The two unrecorded games read "Not recorded", "Its result is not
    recorded; …", "(result not recorded)", "The score stops after …; the result
    was not recorded." and "result not recorded".
  - No page has a `*` outside `<pre class="pgn">`, and every PGN section still
    ends in ` *`.
  - No conclusion contradicts the shown result. `white-73` reads "…ended 1–0
    … was clearly ahead: … 73%", the presumed draws give White's chances
    without naming a winner, and `mate-*` read "…clearly ahead: … 100%".

## Breaks I made (each on `pgn_postmortem/site.py`, then restored)

For each break I cleared `__pycache__` and set `PYTHONDONTWRITEBYTECODE`. A
first pass without this reused stale bytecode for two breaks whose edit kept
the file size unchanged, so those results were taken again. I ran
`tests/test_presumed_results.py` and `tests/test_site.py` each time:

| break | result | tests that went red |
|---|---|---|
| presumption before the board (order swapped) | 2 failed | `…board_decides…[stalemate-analyzed]`, the expected-table test |
| `60` hard-coded instead of `presume_threshold` | 5 failed | `…default_threshold_is_70_not_60`, `…threshold_parameter_is_used`, `…[white-34]`, the wording rule, the table |
| index shows the header's result | 12 failed | every presumed/board case (index place) |
| lead uses the header's result | 12 failed | the same cases (lead place) |
| infobox uses the header's result | 12 failed | the same cases (infobox place) |
| end of the moves uses the header's result | 12 failed | the same cases (moves place) |
| old `plural` (`word + "s"`) | 1 failed | `test_counts_of_two_or_more_inaccuracies_read_inaccuracies` |
| mate score's sign flipped | 3 failed | both `mate-*` cases, the table |
| lower bound 50 instead of 55 | 6 failed | `…outside_55_to_95_is_rejected[*]` |
| stalemate check removed | 3 failed | `stalemate`, `stalemate-analyzed`, the table |
| `elif article.presumed` branch disabled | 1 failed | `test_a_presumed_win_is_not_said_to_come_from_outside_the_position` |
| `>=` made `>` on the threshold | **0 failed** | see finding 1 |
| `build_site`'s up-front `check_presume_threshold` removed | **0 failed** | see finding 2 |

The suite was 101 passed again after the restores, and `git status` was clean.

## The contract, item by item

1. **Passes.** The test is
   `test_an_unrecorded_result_is_presumed_from_the_final_evaluation[white-73]`.
   `assert_shows` reads all five places from the parsed HTML: the infobox row,
   `p.lead`, the last `p.moves`, the paragraph after `h2#conclusion` and the
   index `span.result`.
2. **Passes.** The same test covers `white-27` (26.65%, shown 0–1) and
   `white-34` (33.52%, shown ½–½).
3. **Passes.** `white-66` (66.48%) is ½–½ by default and 1–0 at 60. The
   hard-coded-60 break goes red.
4. **Passes.** `white-73` is ½–½ at 80.
5. **Passes.** Both `build_site` and `shown_result` reject 54.9, 95.1, 0, 50,
   100 and NaN. The bounds 55 and 95 are accepted. `not low <= t <= high`
   rejects NaN, as the comment says.
6. **Passes.** The unanalyzed checkmate, stalemate and insufficient-material
   games show the board's result. `stalemate-analyzed`, with an impossible
   +5.00, proves that the board decides first. The swap break is caught only
   by that case, which is its purpose.
7. **Passes.** `#8` gives 1–0 and `#-8` gives 0–1 in positions that are not
   game over.
8. **Passes.** Two tests cover it: the not-recorded wording for `Result "*"`
   and for a missing header, and no `*` outside the PGN section on all 13
   pages and the index.
9. **Passes.** For every game the test checks:
   - the source header is `*`, and the game object's header is still `*` after
     the build;
   - the id is the source's `game_id`, and differs from an id computed with
     the shown result;
   - the page is at `file_stem(game, id).html`;
   - the PGN section has `[Result "*"]` and the `PostmortemId`, and ends in
     ` *`.
10. **Passes.** The counts read "Black made two inaccuracies" and "White made
    two inaccuracies", and no page contains "inaccuracys".

Wording rule ("never 'came from outside the position' for a presumed win"):
`white-59` at threshold 55 reads "Ada Example was ahead: the engine gives 59%
winning chances in the final position." A recorded result below 60% keeps the
old sentence (`site.py:751` is the only new branch).

Decided items: the grading still uses win %. Annotations are still stripped:
`Collection.read(..., keep_analysis=True)` only, and `is_analyzed` needs the
library's marker header, so a source's own `[%eval]` never presumes anything.
The PGN is not written back. There is no marker (owner decision) and no CLI
option (owner: a library parameter). Nothing touches F-1.3, F-6 or F-7.

## Findings

1. **non-blocking.** No test pins "at least" at the threshold boundary.
   - Evidence: `pgn_postmortem/site.py:225` and `:227` use
     `white >= presume_threshold`, as the scope says ("at least 70%"). Changing
     both to `>` leaves all 101 tests green. No fixture sits exactly on a
     threshold.
   - Real games will almost never land exactly on 70.0, so this is a guard
     against a regression rather than a live defect.
   - Suggested fix: a one-line test, such as
     `shown_result(read("white-73.pgn").game, win_percent(275)) == "1-0"`
     (73.35… is inside 55–95).
2. **non-blocking.** No test pins `build_site`'s up-front bounds check.
   - Evidence: `pgn_postmortem/site.py:992`. Removing it leaves every test
     green, because `shown_result` checks the threshold again
     (`site.py:213`) inside the article loop, before anything is written.
   - The claim "raises `ValueError` before anything is written" therefore
     holds for any non-empty collection. For an empty collection it holds only
     because of line 992, and no test covers that case.
   - Suggested fix: add `build_site([], tmp_path, presume_threshold=10)` to
     `test_a_threshold_outside_55_to_95_is_rejected` if the up-front check is
     meant to be the contract.
3. **non-blocking.** The README wording is slightly off.
   - Evidence: `README.md:214`, "the game's PGN, its id and its file name keep
     the source's `*`".
   - A file name never contains `*`. What is meant is that the id, and so the
     file name, is computed from the source's `*`.
   - Suggested fix: "…its id and so its file name are those of the source's
     `*`" or similar.
4. **non-blocking (no change required).** I judged the scope creep and accept
   it.
   - `shown_result` is exported from `pgn_postmortem/__init__.py:21`. This
     widens the public API, but it is the natural hook for F-1.3, which needs a
     result for every game. It is documented in the module docstring.
   - Treating an empty `Result` like a missing one (`site.py:214`) reads the
     scope's "missing" sensibly.
   - Leaving other non-standard values (`1/2`, `?`) as written respects the
     out-of-scope rule "presuming anything for a game whose `Result` is
     recorded". The PR body records both choices.
   - The artistic-license wording ("Not recorded", "(result not recorded)",
     "result not recorded", "The score stops after …", "X was ahead: …") is
     recorded in the PR body, as `ROADMAP.md` *Artistic license* requires.
5. **non-blocking (process note).** `ROADMAP.md` still lists F-5 as
   `accepted`.
   - The PR does not move F-5 to `in review` or `landed`.
   - This matches the precedent: F-1's row stayed `accepted` through F-1.1 and
     F-1.2. Whether to update it at landing is the owner's call.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
