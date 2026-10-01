# F-1.3 Implementation Review 01

- **Revision covered:** `77a45f22a68b7d106c8ce38e7676c03dca30eed5`.
- **Target proof:** `git rev-parse HEAD` matched the target exactly; `git merge-base main 77a45f2` returned `241143e12ef9e81584cfb4ac3d2b700305db0865`; and the file list below was obtained with `git diff --name-only 241143e12ef9e81584cfb4ac3d2b700305db0865..77a45f2`. The worktree's unrelated modification to `scripts/update_games.sh` is not in that target diff and was not reviewed as part of the implementation.
- **Files checked:** `PLAN.md`, `README.md`, `ROADMAP.md`, `design/001-f13-book-around-games.md`, `docs/book-plan.md`, `examples/book_demo/analyzed/1906-00-00-df3535b5ea.pgn`, `examples/book_demo/analyzed/1909-00-00-154d5c2994.pgn`, `examples/book_demo/analyzed/1909-00-00-7325460014.pgn`, `examples/book_demo/analyzed/1909-00-00-d6a0c6ad8a.pgn`, `examples/book_demo/analyzed/1909-00-00-e40260b22b.pgn`, `examples/book_demo/source/capablanca.pgn`, `pgn_postmortem/__init__.py`, `pgn_postmortem/cli.py`, `pgn_postmortem/selection.py`, `pgn_postmortem/site.py`, `tests/golden/site-no-history/career.html`, `tests/golden/site-no-history/chapters/best-draws.html`, `tests/golden/site-no-history/chapters/best-losses.html`, `tests/golden/site-no-history/chapters/best-wins.html`, `tests/golden/site-no-history/index.html`, `tests/golden/site/career.html`, `tests/golden/site/chapters/best-draws.html`, `tests/golden/site/chapters/best-losses.html`, `tests/golden/site/chapters/best-wins.html`, `tests/golden/site/index.html`, `tests/test_book_demo.py`, `tests/test_history.py`, `tests/test_quiz.py`, and `tests/test_selection.py`.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context OpenCode reviewer.
- **Mode:** OpenCode, implementation review.
- **Checks run:** Ubuntu `.venv/bin/python -m pytest -q` (`226 passed`), Ubuntu `.venv/bin/python -m ruff check .` (passed), `node --test 'tests/js/*.test.mjs'` (32 passed), `git diff --check`, golden-page generation through the test suite, and focused checks of the demo's source/analyzed IDs, Stockfish marker, complete evaluations, no-analysis output, opponent aggregation, both-sides accuracy, and career output.

## Findings

1. **blocking** — The career page omits the required notable games and their chapter scores.
   - `pgn_postmortem/site.py:1201-1204` renders only three chapter links under “Featured chapters”; it never iterates over the selected chapter games and never emits their article links, chapter names, or selection scores.
   - The agreed design requires notable games to be exactly the selected chapter games, linked with their chapter and score (`design/001-f13-book-around-games.md:154-156`). The generated `tests/golden/site/career.html:46-51` confirms the omission: it contains only the three chapter links.
   - This was reproduced against the committed Capablanca analysis: chapter pages were generated, but `career.html` contained no `selection score` text. Add the notable-game view and golden/link assertions.

2. **blocking** — A player build with no analyzed games incorrectly creates empty chapter pages and book navigation.
   - `pgn_postmortem/site.py:1608-1616` writes all three chapter pages whenever `names` is non-empty, even when `select_chapters` returns no eligible games. `pgn_postmortem/site.py:1628` passes `bool(names)`, so the index always links to those pages as well.
   - The agreed matrix requires `career.html` to remain but chapter pages and chapter links to be omitted when a player has no analyzed games, and requires generated chapter pages to be removed on a rebuild (`design/001-f13-book-around-games.md:169-177`).
   - Reproduced with the unanalyzed fixture: the output contained `career.html`, all three `chapters/best-*.html` files, and `best-wins.html` in `index.html`. The existing `tests/test_quiz.py` no-analysis coverage checks only the quiz, so it does not catch this regression. Fix generation, navigation, stale cleanup, and add the matrix assertions.

3. **blocking** — Frequent-opponent aggregation is not case-insensitive.
   - `pgn_postmortem/site.py:1167-1168` uses the displayed opponent string directly as the dictionary key. `display_name` normalizes ordering but does not casefold, so `Rival` and `RIVAL` become two opponents.
   - The design requires opponents to be counted case-insensitively after `display_name`, with alphabetical tie ordering (`design/001-f13-book-around-games.md:147-149`).
   - Reproduced by changing two fixture opponent headers to `Rival` and `RIVAL`: the career output contained separate `<li>Rival: 1</li>` and `<li>RIVAL: 1</li>` entries. Aggregate by a casefolded key while retaining the deterministic displayed spelling/order.

4. **blocking** — Both-sides-player accuracy uses a move-count-weighted mean instead of the specified mean of the two side accuracies.
   - `pgn_postmortem/selection.py:152-161` puts every qualifying move from both player-colored sides into one `player` list and averages that list. The contract says a game where both sides match the player uses the mean of both sides' accuracy (`design/001-f13-book-around-games.md:85-86`), which gives each side equal weight regardless of move count.
   - On the committed `tests/fixtures/site/quiz/both-sides.pgn`, the two side accuracies were `0.9766874874` and `0.9854062630`; the specified mean is `0.9810468752`, while the implementation returned `0.9813033097` from 8 and 9 qualifying moves. This can change weighted chapter scores and rankings. Compute each side's accuracy separately, then average them for the both-sides case; keep opponent features neutral as specified.

5. **blocking** — The implementation tests do not establish the agreed selection and book contracts.
   - `tests/test_selection.py:24-60` checks default construction, two invalid option values, marker/partial eligibility, and repeatability, but does not assert the required component feature values, weighted scores, hard-fought-loss ranking, saved-draw ranking, minimum-length behavior, chapter limit, complete tie key, chapter allocation, both-sides behavior, missing ratings/openings/dates, or invalid weight cases.
   - `tests/test_book_demo.py:17-30` proves the five source/analyzed IDs and headers and that pages/links exist, but does not assert that chapters contain the selected entries or that the career page exposes notable games. The golden chapter pages are empty under the default fixture length, so they cannot catch selection output regressions.
   - The agreed done-when explicitly requires these feature, ranking, career, stale-page, history and link assertions (`design/001-f13-book-around-games.md:211-239`). The current passing gates therefore leave the four behavioral defects above undetected. Add focused hand-written fixtures and assertions before approval.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
BLOCK
