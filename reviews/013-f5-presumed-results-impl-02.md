# Review 013 — F-5, a result for games whose result was not recorded (implementation, round 02)

- **Revision covered:** `ddc74b9df2e3b8a4e7d077c70a332875390d9d63` (head of
  `iteration-3-presumed-results`, pull request #13).
  - After a fetch I checked out `origin/iteration-3-presumed-results`.
    `git rev-parse HEAD` equals `gh pr view 13 --json headRefOid`.
  - The merge base with `origin/main` is
    `d1fb5d839ea5659355a85e7cb1022e53c2f77a1c`, which is `origin/main`
    itself.
  - The round-01 revision was `e1c4fdd`. The new commits since then are
    `0caf932`, `40762e7` and `ddc74b9`.
- **Files checked (20):** taken from `gh pr view 13 --json files`, and equal to
  `git diff --name-only d1fb5d8..ddc74b9`. They are the 19 files of round 01
  plus `reviews/013-f5-presumed-results-impl-01.md`:
  - `CLAUDE.md`, `README.md`
  - `pgn_postmortem/__init__.py`, `pgn_postmortem/site.py`
  - `reviews/013-f5-presumed-results-impl-01.md`
  - `tests/test_presumed_results.py`
  - `tests/fixtures/site/synthetic/README.md`
  - the 13 PGNs in `tests/fixtures/site/synthetic/`
- **Changes in this round:** `git diff --stat e1c4fdd..ddc74b9` touches
  `CLAUDE.md`, `README.md`, `reviews/013-f5-presumed-results-impl-01.md` and
  `tests/test_presumed_results.py`. `pgn_postmortem/site.py` is unchanged.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a Claude Code subagent. It
  continued the round-01 reviewer session, as `PRINCIPLES.md` (*Reviewer
  sessions*) permits for a re-review, and re-read the current revision.
- **Mode:** Claude Code (`PLAN.md`, iteration 3). The contract is F-5's block in
  `ROADMAP.md`.

## What I ran

- **Round-01 record:** `git show 0caf932:reviews/013-f5-presumed-results-impl-01.md`
  compared with `cmp` against the file I wrote in round 01 is byte-identical.
  The file has not changed since `0caf932`: `git diff --stat 0caf932..ddc74b9 -- reviews`
  is empty.
- **Gates:** I used the reviewer's venv with the package installed editable.
  The dependency files have not changed since round 01.
  - `ruff check .` reports "All checks passed!".
  - `pytest -q -rs` reports "104 passed", with nothing skipped and Stockfish on
    PATH.
- **CI:** `gh pr checks 13` passes on test (3.11), test (3.13) and GitGuardian.
  The run `36112177774` has `headSha` `ddc74b9…`.
- **Reproduced fixes:** each break was made in `pgn_postmortem/site.py`. For
  each one I cleared `__pycache__`, ran pytest with `PYTHONDONTWRITEBYTECODE=1`
  (and `-B` for the single run), then restored the file. `git status` was clean
  afterwards.

  | break | result | red test |
  |---|---|---|
  | `white > presume_threshold` (White's side only, `site.py:225`) | 1 failed, 45 passed | `test_winning_chances_exactly_at_the_threshold_count_as_a_win[white-73.pgn-1-0-275]` |
  | `100 - white > presume_threshold` (Black's side only, `site.py:227`) | 1 failed, 45 passed | `…exactly_at_the_threshold…[white-27.pgn-0-1--275]` |
  | both sides `>` | 2 failed, 44 passed | both cases above |
  | `build_site`'s up-front `check_presume_threshold` removed (`site.py:992`) | 1 failed, 45 passed | `test_build_site_rejects_a_threshold_out_of_range_up_front_even_with_no_games`, "Failed: DID NOT RAISE ValueError" |
  | regression checks: board/presumption swapped; old `plural`; index showing the header's result | 2, 1 and 14 failed | the same tests as in round 01, plus the new boundary cases for the index break |

## Round-01 findings

1. **Fixed** in `40762e7`: `tests/test_presumed_results.py`,
   `test_winning_chances_exactly_at_the_threshold_count_as_a_win`.
   - The test asserts that the fixture's final eval is the stated centipawn
     value.
   - It sets the threshold to exactly the side ahead's chances:
     `win_percent(275)` for White, and `100 - win_percent(-275)` for Black. The
     code computes the same float expression, so the equality is exact and the
     result is deterministic.
   - It then checks `shown_result` and all five display places through
     `assert_shows`.
   - Each side is pinned independently, as the table above shows.
2. **Fixed** in `40762e7`:
   `test_build_site_rejects_a_threshold_out_of_range_up_front_even_with_no_games`.
   - `build_site([], out, …)` raises for 54.9, 95.1 and NaN, and
     `not out.exists()` holds after each.
   - An empty build with the default threshold writes `index.html`.
   - The test goes red when the up-front check is removed.
3. **Fixed** in `ddc74b9`. `README.md:213-215` now says that the article's PGN
   section shows the source's `*`, and that "the game's id, and therefore its
   file name, is computed from that `*` result, not from the result shown".
   - This is accurate. Item 9's test asserts that an id computed from the
     shown result would differ, and that the page is at
     `file_stem(game, id).html`.
4. **Unchanged, as intended.** The owner accepted these choices.
5. **Unchanged, as intended.** F-5's status in `ROADMAP.md` is the owner's call.

## Findings

1. **non-blocking (a correction to my own round-01 evidence).** Round-01
   finding 1 said that changing both comparisons to `>` "leaves all 101 tests
   green".
   - The break I actually ran then changed only White's side (`site.py:225`).
   - The conclusion still held, because no fixture sat on a threshold. In this
     round I ran White's side, Black's side and both, and all three are now
     caught.
   - I note it so that the round-01 record is not read as having measured
     both sides.
2. **non-blocking.** The new `CLAUDE.md` gates row describes the added tests
   accurately: "winning chances exactly at the threshold counting as a win for
   either side" and "by `build_site` up front even for an empty collection". I
   found nothing else new: `site.py`, the fixtures, `scripts/`, `examples/` and
   the golden files are unchanged since round 01.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged by the owner on 2026-09-25 as `88ebc62` (pull request #13); the clean round, 02, covers `ddc74b9`. CI on the merge commit passed on Python 3.11 and 3.13: https://github.com/diegoami/pgn-postmortem/actions/runs/36114715578. F-5's done-when (`ROADMAP.md`, F-5's block), all met with tests checked in rounds 01–02:

1–4. **Presuming from the analysis:** ≥70% gives a win (White and Black), 32–35% and 65–68% give a draw, the threshold parameter is used, and the threshold boundary counts as a win.
5. **The threshold's range:** thresholds outside 55–95% are rejected, including up front in `build_site` and for an empty collection.
6–7. **The board decides first:** checkmate, stalemate and insufficient material decide from the board, and a final mate-score eval decides for the side with the mate.
8. **Nothing is left as a bare "\*":** "not recorded" wording is used, and no bare "\*" appears outside the PGN section.
9. **The source is untouched:** the PGN `Result`, the `PostmortemId` and the file names are unchanged.
10. **The plural is fixed:** "inaccuracies".

**The gates:** `ruff check .` is clean, and `pytest -q` gives 104 passed. The golden files are unchanged, as expected.

Left as accepted by the owner: round-01 finding 4 (the scope choices). Finding 5 (marking F-5 as landed in `ROADMAP.md`) was decided by the owner on 2026-09-25 and happens in the next record change.

— Implementer, Claude Opus 5.5 (claude-opus-5-5)
