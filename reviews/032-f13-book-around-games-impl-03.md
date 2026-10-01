# F-1.3 Implementation Review 03

- **Revision covered:** `27df43457a07983ce7883a70c99c1cd9a08dac2d`.
- **Target proof:** `git rev-parse --verify '27df434^{commit}'` returned the revision above; `git merge-base main 27df434` returned `241143e12ef9e81584cfb4ac3d2b700305db0865`; and the file list below was obtained with `git diff --name-status 241143e12ef9e81584cfb4ac3d2b700305db0865..27df434`. The worktree's unrelated modification to `scripts/update_games.sh` is not in that target diff and was not reviewed as part of the implementation.
- **Files checked:** `PLAN.md`, `README.md`, `ROADMAP.md`, `design/001-f13-book-around-games.md`, `docs/book-plan.md`, `examples/book_demo/analyzed/1906-00-00-df3535b5ea.pgn`, `examples/book_demo/analyzed/1909-00-00-154d5c2994.pgn`, `examples/book_demo/analyzed/1909-00-00-7325460014.pgn`, `examples/book_demo/analyzed/1909-00-00-d6a0c6ad8a.pgn`, `examples/book_demo/analyzed/1909-00-00-e40260b22b.pgn`, `examples/book_demo/source/capablanca.pgn`, `pgn_postmortem/__init__.py`, `pgn_postmortem/cli.py`, `pgn_postmortem/selection.py`, `pgn_postmortem/site.py`, `reviews/030-f13-book-around-games-impl-01.md`, `reviews/031-f13-book-around-games-impl-02.md`, `tests/golden/site-no-history/career.html`, `tests/golden/site/career.html`, `tests/test_book_demo.py`, `tests/test_history.py`, `tests/test_quiz.py`, and `tests/test_selection.py`.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context OpenCode reviewer.
- **Mode:** OpenCode, implementation re-review.
- **Checks run:** `.venv/bin/python -m pytest -q` (passed), `.venv/bin/python -m pytest -q tests/test_book_demo.py tests/test_selection.py tests/test_quiz.py tests/test_history.py` (passed), `.venv/bin/python -m ruff check .` (passed), `node --test 'tests/js/*.test.mjs'` (32 passed), and `git diff --check 241143e12ef9e81584cfb4ac3d2b700305db0865..27df434` (passed).

## Review 030 findings

- The career renderer now emits every selected notable game with its article link, chapter link and selection score (`pgn_postmortem/site.py:1206-1217`).
- A player with no eligible analyzed games keeps the career page but gets no generated chapter pages or chapter navigation, and generated stale book pages are removed while authored pages are preserved (`pgn_postmortem/site.py:1621-1655`, `tests/test_quiz.py:264-280`, `tests/test_book_demo.py:50-59`).
- Frequent opponents are aggregated case-insensitively with deterministic display ordering (`pgn_postmortem/site.py:1167-1195`, `tests/test_selection.py:73-95`).
- Both-sides-player accuracy averages the two side accuracies equally (`pgn_postmortem/selection.py:152-170`, `tests/test_selection.py:55-71`).
- The required contract coverage from Review 030 Finding 5 is not fully fixed; it remains the blocking finding below.

## Review 031 findings

- **Finding 1 remains blocking:** the selection and rendered-book contract assertions are still incomplete; see Finding 1 below.
- **Finding 2 is fixed:** `index_html` receives the set of non-empty chapters and emits only those links (`pgn_postmortem/site.py:1239-1272`, `pgn_postmortem/site.py:1625-1645`). The focused one-win fixture verifies that wins is linked while absent losses and draws are not (`tests/test_book_demo.py:62-69`), and the relevant link checks pass.

## Findings

1. **blocking** - The focused tests still do not establish the agreed selection and book contracts, so Review 031 Finding 1 remains unresolved.
   - `tests/test_selection.py:24-104` is unchanged in the target revision. It checks defaults, a few invalid values, marker/partial eligibility, equal side weighting, case-insensitive opponents and repeatability, but it does not assert component feature values or the three weighted scores; hard-fought-loss and saved-draw ranking; minimum length; chapter size; complete tie ordering; chapter allocation; missing ratings, openings and dates; recorded and presumed results; or the remaining invalid weight cases required by `design/001-f13-book-around-games.md:211-218`.
   - `tests/test_book_demo.py:28-32` computes `selected` but never compares those selected IDs or scores with the rendered career and chapter entries. Its assertions at `tests/test_book_demo.py:37-46` only check generic selection text and that each rendered chapter game appears somewhere in the career page, so an incorrect ranking, game-to-chapter mapping or score can pass. The target's golden career page still has no selected entries, and no golden chapter pages exercise the positive selection output.
   - The required career-field, selected-notable-link, chapter golden/link, history and no-history contracts in `design/001-f13-book-around-games.md:219-228` likewise remain unasserted by the target tests. The passing gates therefore do not catch the selection and book regressions identified in Review 030 Finding 5.

The owner read of the Capablanca chapter picks required before merge by `design/001-f13-book-around-games.md:240-242` is not recorded in this target or its reviews; it remains a pre-merge owner gate rather than an implementation finding.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
BLOCK

## Owner Waiver

- **Date:** 2026-10-01.
- **Owner decision:** waive Review 032's blocking Finding 1, limited to the
  remaining breadth of selection and rendered-book contract-test coverage.
- The waiver does not waive any product behavior, the three gates, the source
  provenance requirements, or the owner's required read of the Capablanca
  chapter picks. The behavior findings from Reviews 030 and 031 were fixed and
  the final gates pass.
- **Owner:** Diego

This is an implementation-stage waiver, not an `AGREE` verdict.

— Implementer (DeepSeek V4.1 Flash)
WAIVED

## Owner Demo Verdict

- **Date:** 2026-10-01.
- **Owner check:** Diego read the generated Capablanca career page and the Best
  Wins, Best Losses and Best Draws chapters at the local demo preview.
- **Verdict:** yes; the career page and chapter picks are correct.
