# Review 021-f9-quiz-list, implementation, round 01

- **Revision covered:** `6ed9b8b6a9c32bab0dc1b725aada7570a5aa6cab` (pull request #21, branch
  `iteration-6-quiz-list`). `git rev-parse HEAD` in the reviewer's worktree after checking out
  `origin/iteration-6-quiz-list` equals `gh pr view 21 --json headRefOid`. The merge base is
  `4654e0c`, which is `origin/main`.
- **Files checked (30):** `gh pr view 21 --json files` lists the same 30 paths as
  `git diff --name-only 4654e0c..HEAD`:
  `CLAUDE.md`, `README.md`, `pgn_postmortem/__init__.py`, `pgn_postmortem/cli.py`,
  `pgn_postmortem/collection.py`, `pgn_postmortem/site.py`, `pgn_postmortem/static/history.js`,
  `tests/fixtures/site/quiz/{README.md, blunder-2015.pgn, both-sides.pgn, opponents-only.pgn, others.pgn, tie-2012.pgn, tie-999.pgn, ties-2014.pgn}`,
  `tests/golden/site-no-history/{assets/style.css, index.html, quiz.html}`,
  `tests/golden/site/{assets/style.css, index.html, quiz.html}` and its six `games/*.html`,
  `tests/js/quiz.test.mjs`, `tests/test_history.py`, `tests/test_quiz.py`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that had
  not seen the implementation.
- **Mode:** Claude Code.
- **Contract:** F-9's block in `ROADMAP.md` on `main`, plus F-8's and F-6's blocks; the three points
  in the completion note of `reviews/020-shape-f9-impl-02.md`; PLAN.md iteration 6; CLAUDE.md's slot.

## Gates (run by the reviewer on the revision above, fresh venv, `pip install -r requirements-dev.txt` and `pip install -e .`)

- **lint:** `.venv/bin/python -m ruff check .` gives `All checks passed!`
- **tests:** `.venv/bin/python -m pytest -q` gives `175 passed`. Stockfish was on PATH, so nothing
  was skipped.
- **script:** `node --test 'tests/js/*.test.mjs'` (Node v24.21.0) gives `tests 32`, `pass 32`,
  `fail 0`. That is 20 tests from F-8 and 12 new ones in `tests/js/quiz.test.mjs`.
- **CI:** run 36155805645 is on head `6ed9b8b`. `test (3.11)` and `test (3.13)` both succeeded.
- **Golden sets:** I regenerated both sets with the two documented commands in CLAUDE.md (one with
  history, one with `--no-history`) into a scratch directory. `diff -r` against
  `tests/golden/site/` and `tests/golden/site-no-history/` shows no differences.
  - The six changed articles in `tests/golden/site/games/` change only in lines of the inlined
    script. Every added or removed line appears in the `history.js` diff.
  - Beyond the script, the two index pages change only by the `quiz-link` paragraph, and the two
    stylesheets only by the `.quiz .rank` and `.quiz .lost` rules.
  - The `site-no-history` articles are untouched, as the pull request says.

## The contract, item by item

- **Only the player's own moments, with the same rules as the articles.** I checked this outside
  the page code.
  - On the analyzed fixture, `make_articles` gives four moments. Only `3... Nf6` (Black, "AdaEx")
    is Ada Example's, and it is the golden quiz's only line.
  - The quiz fixture gives the seven lines the README expects: aliases, `  ADA EXAMPLE ` matched
    regardless of case and spaces, both sides of `both-sides.pgn`, and two swings under 20 points.
  - `own_colors` (`pgn_postmortem/site.py`) matches names as `Collection.read` does:
    `strip().casefold()` against `player_names`.
  - `number` comes from `enumerate(article.moments, 1)`, which numbers moments the same way as
    `moves_html`.
- **Total order.** The sort key is `(-self.loss, self.position, self.filename, self.ply)`. The
  value is `MoveReview.loss`, `max(before - after, 0)`, which is exactly the value `review_moves`
  grades.
  - The fixture proves the index step on real pages: 999 comes before 2012 and 2014, while
    `sorted(tied) != tied`.
  - The file-name and exact-points steps are proved on entries set equal with
    `dataclasses.replace`.
  - **The year-999 fixture is sound.**
    - The index sorts years as numbers (`index_years`) and, within a year, articles by file name.
      A shorter year is therefore the only input where the index order and the file-name order
      differ, so no four-digit fixture could prove this step.
    - The fixture's README documents it.
    - The test guards its own premise. If file stems ever zero-padded the year, the assertion
      `sorted(tied) != tied` would fail loudly instead of passing silently.
    - For every real four-digit archive, the index step and the file-name step give the same
      result. That is the contract's rule, not a defect.
- **Links and data.** Every line links to `games/<file>.html#moment-N`, and `check_links` covers
  the quiz page.
  - `test_each_line_links_to_its_question_and_carries_its_game_and_move` compares each line's
    `data-game`/`data-move` with the linked moment's `<details data-move>` and the article's
    `data-game`.
  - On the owner's book (below) I checked all 334 lines with my own script: 0 mismatches.
- **No player.** Neither name, blank names (`"  "`, `""`, `" "`), and the `site` command without
  `--player`/`--alias` all give no page and no link, and the index has no `quiz-link`. A player
  with no own moment gets the "none" page, analyzed or not.
- **Stale pages.** A rebuild without a player removes a `quiz.html` that carries `GENERATOR`, and
  a foreign one survives. See finding 2 for a rebuild *with* a player.
- **Exactly two new `data-` attributes.** `test_the_data_attributes_are_the_named_ones_and_only_those`
  pins the quiz page to `{html data-site, li data-game, li data-move}`. With `--no-history`,
  `quiz.html` has no `<script>`, no `data-` attribute and no `class="seen"`, and the strip test
  asserts `"quiz.html" in with_history`.
- **Marks from F-8's history** (`history.js`):
  - The marks read `revealed:ID:MOVE` under the site's prefix, the same key the article writes.
  - The script inserts each mark before `.meta` and never moves a line.
  - The redraw is registered in `again` for `pageshow`/`persisted`.
  - The quiz page has no clear button and no write of its own; the only write is F-8's existing
    storage probe.
  - `openStorage` returning null ends `start`, so without storage there are no marks.
- **The library route (completion-note point 1).**
  - `Collection` keeps `player` and `aliases`, reading the aliases once as a tuple.
  - `Collection.build_site` passes `self`.
  - `test_a_collection_read_for_a_player_builds_the_quiz` covers the method, the module function
    given the collection, names given to the builder, and a one-pass alias iterator.
  - `test_a_collection_without_names_builds_no_quiz` covers a collection built directly from its
    games, and a plain list.
- **The design choice that `build_site(collection)` with no names uses the collection's names**
  (`site.py:1420`) **is acceptable.**
  - The block says only that `build_site` gains `player`/`aliases` and that the method passes on
    the collection's names. Round 02's finding 1 left open whether the function does the same.
    Making the function and the method agree is the least surprising answer.
  - It is documented in both docstrings and in README.
  - It changes nothing for callers without names.
  - One side effect: a library user cannot switch the quiz off for a named collection, except by
    passing a blank `player=""`, which is undocumented. That is harmless, and not a finding.
- **Documentation.**
  - README (the site section and the library example), the `site.py` module and `build_site`
    docstrings, `cli.py`, `__init__.py`, and CLAUDE.md's tests and script "covers" cells are all
    updated.
  - Completion-note point 2: the docstring and README say "generator marker (`GENERATOR`)".
  - Completion-note point 3: the no-player rule is stated once in each document the change owns.
  - No absolute local path or owner name appears in the diff.

## Reproduction: my own breaks

Each break was applied alone and run with a fresh `PYTHONPYCACHEPREFIX`, with the pytest cache
off. Each file was then restored, and `git status` is clean afterwards. All 16 went red:

| break | red tests (among others) |
|---|---|
| R1 all moments of a player's game counted (opponents' included) | `test_the_quiz_lists_exactly_the_players_own_critical_moments` and 7 more |
| R2 order by rounded points | `test_the_tie_rule_goes_on_to_the_file_name_then_move_order` |
| R3 index-order tie step dropped (file name straight after points) | `test_the_quiz_is_in_worst_first_order_with_the_tie_rule` (on the 999 fixture), `test_the_tie_rule_…` and 5 more |
| R4 anchor numbered among the player's own moments only (wrong `moment-N`) | `test_each_line_links_to_its_question_and_carries_its_game_and_move` |
| R5 `data-move` from the moment number instead of the move | `test_each_line_links…`, `test_the_data_attributes_are_the_named_ones_and_only_those`, both golden tests |
| R6 stale builder-written `quiz.html` left | `test_a_rebuild_without_a_player_removes_the_quiz_page_the_builder_wrote` |
| R7 `Collection.read` forgets its names | `test_a_collection_read_for_a_player_builds_the_quiz` |
| R8 foreign `quiz.html` removed | `test_a_quiz_page_the_builder_did_not_write_is_never_removed` |
| R9 blank names treated as a player | `test_without_a_player_there_is_no_quiz_page_and_no_link` |
| R10 `data-` attributes written without the history | the no-history golden test, the strip test, `test_without_the_history_the_pages_carry_none_of_it` |
| R11 only one side counted when both match | `test_names_match_regardless_of_case_and_spaces_and_both_sides_count` and 7 more |
| R12 case-sensitive names | `test_names_match…` and 7 more |
| J1 quiz not redrawn on a bfcache restore | "a quiz shown again from the back/forward cache redraws the marks", "Clear history on the index removes the marks" |
| J2 a viewed game counts as answered | "a question is marked answered when its game and move are in this site's history" |
| J3 old marks not removed on a redraw | "Clear history on the index removes the marks", the bfcache test |
| J4 answered lines moved to the end | "the order never changes, and the quiz stores nothing" and 2 more |

**The sites I built and read:** the fixture site with and without the history, and the quiz
fixture for Ada Example.
- The golden `quiz.html` (with and without the history) differs only in `data-site`, the line's
  two attributes and the script.
- The quiz fixture's page lists the README's seven lines in order, with `Carl &lt;Foe&gt; &amp; Co`
  escaped.

## The owner's book (read only, no Stockfish)

I built the book from `chessgamescollection`'s `book/analyzed/` (148 files) at this head into a
scratch directory, with the six names from the brief.
- **The build's summary:** 148 articles, 675 critical moments, and "The quiz lists 334 of them".
- **The quiz page:** 334 `<li>` lines. The first is `30... Rd2`, 97 points, "21 April 2007 · vs.
  Lothar Stadler", linking to `games/2007-04-21-4af60b321d.html#moment-5`.
- **An independent recount** through `critical_moments` and the headers, outside the quiz code,
  gives the same numbers:
  - 675 moments, 334 of them the player's own;
  - the worst costs 97.07 points, on 2007.04.21;
  - exactly 13 cost 50 points or more, the 13th at exactly 50.0;
  - no game has the player on both sides.
- `check_links` on the built book passes: 1757 links, all resolving. Every quiz line's
  `data-game`/`data-move` equals its answer's.
- F-9's cited counts are confirmed. Done-when 4 (the owner's preview and verdict) is still
  pending, as the pull request says. It is the owner's, not this review's.

## Judgements asked for

- **F-9's `ROADMAP.md` block left unchanged for completion-note points 2–3.** Defensible, but it
  should not be forgotten.
  - The only place the no-player rule is stated twice is the block itself: `ROADMAP.md:461` "No
    player" and `:489` "Without a player". "F-8's generator mark" is at `:485`. The owner deferred
    both fixes to this implementation, so the literal fix is two wording edits in that block.
  - The edits are non-material: they change no behaviour and no assertion.
  - The implementer applied both points in every document the change owns, and disclosed in the
    pull request that the block itself is untouched.
  - `ROADMAP.md` is not in this change's file list, so this is not a numbered finding.
  - Recommendation: the owner either asks for the two edits in this pull request, or has them made
    with F-9's landing update of `ROADMAP.md` (the row's status), and records which.

## Findings

1. **non-blocking — the lead's "N questions from M games" counts games that give no question.**
   - Evidence: `pgn_postmortem/site.py:1204` builds `of_games` from all the player's games, and
     `:1220` prints "`{N questions} from {of_games}`".
   - The golden page says "One question from six games of Ada Example's", though the one question
     comes from one game. The quiz fixture says "Seven questions from six games", though they come
     from five. The owner's book says "334 questions from 148 games", though only 122 games give a
     question.
   - "From" reads as the questions' source. The implementer chose this wording under artistic
     license, and it is pinned by `tests/test_quiz.py:350,353`.
   - Suggestion: "334 questions, from 122 of Diego Amicabile's 148 games", or "in Diego
     Amicabile's 148 games".
2. **non-blocking — a rebuild with a player overwrites a foreign `quiz.html` without saying so.**
   - Evidence: `pgn_postmortem/site.py:1445` calls `write_text(out_dir / QUIZ_PAGE, …)` whatever is
     there. With a hand-written `quiz.html` in the output directory, a build for Ada Example
     replaced it, and `report.removed == []`.
   - The block's "A `quiz.html` the builder didn't write is never removed" sits under "Stale
     pages", which is about a rebuild without a player. The code meets that item as written
     (`:1456`). README's "(never one it did not write)" (`README.md:239`) is scoped the same way.
   - The same overwrite already applies to `index.html` and to the articles, so this is consistent
     with F-1.2.
   - Suggestion: leave it as is, or say in README that the site's own file names are overwritten.
     No change is needed for the contract.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
