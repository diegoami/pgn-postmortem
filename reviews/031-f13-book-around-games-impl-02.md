# F-1.3 Implementation Review 02

- **Revision covered:** `ea6ea08921c33055aecded1cf53e100cc6b03619`.
- **Target proof:** `git rev-parse HEAD` matched the target exactly; `git merge-base main ea6ea08` returned `241143e12ef9e81584cfb4ac3d2b700305db0865`; and the file list below was obtained with `git diff --name-only 241143e12ef9e81584cfb4ac3d2b700305db0865..ea6ea08`. The worktree's unrelated modification to `scripts/update_games.sh` is not in that target diff and was not reviewed as part of the implementation.
- **Files checked:** `PLAN.md`, `README.md`, `ROADMAP.md`, `design/001-f13-book-around-games.md`, `docs/book-plan.md`, `examples/book_demo/analyzed/1906-00-00-df3535b5ea.pgn`, `examples/book_demo/analyzed/1909-00-00-154d5c2994.pgn`, `examples/book_demo/analyzed/1909-00-00-7325460014.pgn`, `examples/book_demo/analyzed/1909-00-00-d6a0c6ad8a.pgn`, `examples/book_demo/analyzed/1909-00-00-e40260b22b.pgn`, `examples/book_demo/source/capablanca.pgn`, `pgn_postmortem/__init__.py`, `pgn_postmortem/cli.py`, `pgn_postmortem/selection.py`, `pgn_postmortem/site.py`, `reviews/030-f13-book-around-games-impl-01.md`, `tests/golden/site-no-history/career.html`, `tests/golden/site/career.html`, `tests/test_book_demo.py`, `tests/test_history.py`, `tests/test_quiz.py`, and `tests/test_selection.py`.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context OpenCode reviewer.
- **Mode:** OpenCode, implementation re-review.
- **Checks run:** `.venv/bin/python -m pytest -q` (passed), `.venv/bin/python -m ruff check .` (passed), `node --test 'tests/js/*.test.mjs'` (32 passed), focused Python tests for selection, the book demo, quiz behavior and history (passed), and `git diff --check` (passed).

## Review 030 findings

- The career renderer now iterates selected chapter games and emits each article link, chapter link and selection score (`pgn_postmortem/site.py:1206-1217`).
- A player with no eligible analyzed games no longer gets chapter files or index book navigation, and generated stale chapter files are removed (`pgn_postmortem/site.py:1621-1630`, `1642-1655`).
- Career opponent keys are casefolded while retaining deterministic display ordering (`pgn_postmortem/site.py:1167-1195`).
- Both-sides-player accuracy now averages the two side accuracies instead of weighting by move count (`pgn_postmortem/selection.py:152-170`), and the focused test would distinguish the old implementation (`tests/test_selection.py:55-71`).

## Findings

1. **blocking** — The focused tests still do not establish the agreed selection and book contracts.
   - `tests/test_selection.py:24-104` checks defaults, a few invalid values, marker/partial eligibility, equal side weighting, case-insensitive opponents and repeatability, but it does not assert known component feature values or weighted scores. It also does not cover the required hard-fought-loss and saved-draw rankings, minimum length, chapter size, complete tie key, chapter allocation, missing ratings/openings/dates, or the remaining invalid weight cases from `design/001-f13-book-around-games.md:211-218`.
   - `tests/test_book_demo.py:25-42` computes `selected` but never compares it with the career notable-game links or chapter entries. Its career assertion only checks that the page contains the generic text `selection score`, so an incorrect game-to-chapter mapping could pass. The changed golden files contain no selected chapter entries, and the history test therefore does not exercise history output on a chapter page.
   - `tests/test_quiz.py:264-280` checks a no-player rebuild and a fresh no-analysis build, but does not rebuild from a populated book to verify stale generated chapter cleanup or preservation of an authored chapter file.
   - These are required verification contracts, not optional extra coverage. Passing gates therefore still leave the implementation vulnerable to the selection and book regressions identified in Review 030 Finding 5.

2. **blocking** — A partially empty chapter set produces broken index navigation.
   - `pgn_postmortem/site.py:1626-1630` correctly omits an empty chapter file, but `pgn_postmortem/site.py:1642-1645` passes only one boolean to `index_html`, and `pgn_postmortem/site.py:1267-1272` then emits links to all three chapter files whenever any one chapter is non-empty.
   - A player collection with one eligible win and no eligible loss or draw therefore gets `chapters/best-wins.html` but an index that links to the absent `best-losses.html` and `best-draws.html`. This violates the relative-link/output contract and is not covered by the no-analysis test, which exercises the all-empty case only. Pass the available chapters to the index renderer and emit only links for files actually generated, with a focused one-chapter fixture assertion.

Residual risk remains around the unverified owner read of the Capablanca chapter picks required by the design; no such owner verdict is present in this target review.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer.
BLOCK
