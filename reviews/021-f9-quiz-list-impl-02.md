# Review 021-f9-quiz-list, implementation, round 02

- **Revision covered:** `8814cbdd91f031467e64518476b30032c7ca742d` (pull request #21, branch
  `iteration-6-quiz-list`).
  - After fetching and checking out `origin/iteration-6-quiz-list`, `git rev-parse HEAD` equals
    `gh pr view 21 --json headRefOid`. The merge base is `4654e0c`, which is still `origin/main`.
  - It follows round 01's `6ed9b8b` by three commits:
    - `b6b4734`, which records the round-01 review;
    - `ecfb03b`, "Count the games the quiz's questions come from";
    - `8814cbd`, "Fix F-9's block: the generator marker, and the no-player rule once".
- **Files checked (32):** `gh pr view 21 --json files` and `git diff --name-only 4654e0c..HEAD`
  list the same 32 paths. These are round 01's 30 plus `ROADMAP.md` and
  `reviews/021-f9-quiz-list-impl-01.md`.
  - What changed since round 01 (`git diff --stat 6ed9b8b..HEAD`): `CLAUDE.md`, `ROADMAP.md`,
    `pgn_postmortem/site.py`, `reviews/021-f9-quiz-list-impl-01.md`,
    `tests/golden/site-no-history/quiz.html`, `tests/golden/site/quiz.html`, `tests/test_quiz.py`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. It is the
  same reviewer session as round 01, continued for the re-review, as `PRINCIPLES.md` allows.
- **Mode:** Claude Code.
- **Scope of this round:** the owner's decisions after round 01. Finding 1 is fixed in this pull
  request. The two wording edits to F-9's block are made here. Finding 2 is left as it is. I
  re-read the whole diff since `6ed9b8b` and re-checked what it touches.

## Gates (reviewer's run on the revision above)

- **lint:** `.venv/bin/python -m ruff check .` gives `All checks passed!`
- **tests:** `.venv/bin/python -m pytest -q` gives `175 passed`. Stockfish was on PATH, so nothing
  was skipped.
- **script:** `node --test 'tests/js/*.test.mjs'` gives `tests 32`, `pass 32`, `fail 0`,
  `skipped 0`.
- **CI:** run 36157089309, `headSha` `8814cbd…`, concluded `success`. `test (3.11)` and
  `test (3.13)` both passed.
- **Golden sets:** I regenerated both with CLAUDE.md's two documented commands into a scratch
  directory. `diff -r` against `tests/golden/site/` and `tests/golden/site-no-history/` shows no
  differences.
  - Since round 01, only the two `quiz.html` files changed, in their lead line: "One question from
    six games" became "One question from one game".

## The changes since round 01

- **The round-01 record** (`reviews/021-f9-quiz-list-impl-01.md`, `b6b4734`) is byte-identical
  (`cmp`) to the file this reviewer wrote. The commit adds only that file.
- **The count fix** (`ecfb03b`, `pgn_postmortem/site.py` `quiz_html`):
  - It counts `sources = len({entry.article.item.id for entry in entries})`: distinct games, not
    lines and not all of the player's games.
  - The page without questions keeps `of_games`, which counts all of the player's games. That is
    right, since there the sentence speaks of the games that give no question.
  - The docstring says both.
  - `tests/test_quiz.py`: `test_the_lead_says_how_many_questions_from_how_many_games` now expects
    "Seven questions from five games" on the quiz fixture, and checks the five against the lines'
    distinct `data-game`. It also expects "One question from one game" on the analyzed fixture.
  - `CLAUDE.md`'s tests "covers" cell changes by one phrase: "the games they come from (not all the
    player's games)". Nothing else in the file changes (checked by word diff).
- **The ROADMAP edit** (`8814cbd`): `git diff 4654e0c..HEAD -- ROADMAP.md` is one hunk inside F-9's
  scope, three lines added and four removed. It changes the two items and nothing else:
  - "Stale pages" now says "the builder's generator marker, `GENERATOR`, from F-1.2's rebuild
    rule, `0602071`" instead of "F-8's generator mark". `0602071` is "Escape-test the site, survive
    odd dates, delete only pages it wrote", the commit the shaping review named.
  - The duplicate "**Without a player**" bullet is gone. The fuller "**No player**" statement under
    "Who the player is" (`ROADMAP.md:461`) remains.
  - No done-when item, decision, or other block is touched.

## Reproduction

Each break was applied alone and run with a fresh `PYTHONPYCACHEPREFIX` and no pytest cache. Each
file was then restored, and `git status` is clean afterwards.

| break | result |
|---|---|
| B1 the lead counts all the player's games again (`{of_games}`), round 01's behaviour | RED: `test_the_lead_says_how_many_questions_from_how_many_games` and the three golden tests (`test_site`'s and both of `test_history`'s) |
| B2 the lead counts lines instead of distinct games | RED: `test_the_lead_says_how_many_questions_from_how_many_games` |
| B3 the page without questions counts 0 games instead of all the player's | GREEN; see finding 1 |

**The owner's book** (built read-only from `chessgamescollection`'s `book/analyzed/` into a
scratch directory, with the six names from the round-01 brief, no Stockfish):
- The build's summary: 148 articles, 675 critical moments, and "The quiz lists 334 of them".
- The quiz's lead now reads "**334 questions from 122 games of Diego Amicabile's:**".
- The page has 334 lines, drawn from 122 distinct `data-game` values. The first is still
  `30... Rd2`, 97 points, 21 April 2007.
- I compared the whole site with round 01's build of `6ed9b8b` (`diff -r`). The only file that
  differs is `quiz.html`, and in it only that lead line.
- So the owner's preview check, recorded on the pull request at `6ed9b8b` ("Checked, looks fine"),
  still covers everything but that sentence.

## Findings

1. **non-blocking — the "none" page's game count is not pinned by a test.**
   - Evidence: `ecfb03b`'s message says "The page without questions still counts all the player's
     games", and the `quiz_html` docstring says "the page without questions says both". Yet
     replacing `of_games` in the no-questions lead with a count of 0 (B3) leaves every test green.
   - `test_a_player_with_no_own_moments_gets_a_page_that_says_so` checks only `"no questions" in`
     the lead.
   - This code is unchanged since round 01, and I rendered the output to check it: "The quiz has no
     questions: in one game of Ada Example's, no move Ada Example played is a critical moment …",
     which is right.
   - Suggestion: assert the start of that lead ("in one game of Ada Example's") in the existing
     parametrised test. It can wait for a later change.

Round 01's finding 1 is fixed, and its finding 2 is left as is by the owner's decision. The
ROADMAP wording points from the shaping review's completion note are now done in F-9's block.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
