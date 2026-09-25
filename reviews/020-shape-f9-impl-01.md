# Review 020 — shape F-9 (pull request #20), round 01

- **Revision covered:** `51176ff51be1c04721a841d9bba095e6cb7dc368` (branch `shape-f9`), on top of
  `origin/main` at `2479e922bd01c1823cdce8cfbe7885679771405b`.
- **Target proof:** after `git fetch origin`, `git rev-parse origin/shape-f9` gives
  `51176ff51be1c04721a841d9bba095e6cb7dc368`, equal to `headRefOid` from
  `gh pr view 20 --json headRefOid,files`. One commit on the branch (`51176ff`).
- **Files checked:** `PLAN.md`, `ROADMAP.md`. The pull request's file list
  (`gh pr view 20 --json files`) equals
  `git diff --name-only $(git merge-base origin/main origin/shape-f9)..origin/shape-f9`. Files were
  read with `git show origin/shape-f9:<path>`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that did
  not see the shaping.
- **Mode:** Claude Code.
- **Read against:** `PRINCIPLES.md`, `CLAUDE.md` and its slot (the three gates, the golden-set
  commands), `ROADMAP.md` (*The block*, *The agent's job*, *Artistic license*, F-6's and F-8's
  blocks), `PLAN.md`, `reviews/README.md`, and on `main`: `pgn_postmortem/site.py`,
  `pgn_postmortem/collection.py`, `pgn_postmortem/cli.py`, `pgn_postmortem/static/history.js`,
  and the fixture headers in `tests/fixtures/site/`.

## What holds

- F-9's block has every field of *The block* (original request, player value, scope, done when,
  out of scope, depends on, open questions). The original request is verbatim and matches the queue
  row. "Each new assertion is shown failing first" is there.
- Three owner decisions are marked as such. Each has a recommended default, a reason and the
  alternative not chosen. The proposed items are listed apart under "Proposed with this shaping,
  confirmed by the owner's merge". Whether the owner made the decisions can't be checked from the
  repository; the owner's merge is that check.
- The block is consistent with the code on `main` on these points:
  - moments are numbered `moment-1…k` in move order per article (`moment_html`);
  - "points lost" is available per moment as `MoveReview.before - after`;
  - answers are stored as `pgn-postmortem:KEY:revealed:ID:MOVE` with `MOVE` from `move_key`
    (`31b`), so "keyed by game and move" is F-8's key;
  - with the moments taken from the same `review_moves` output as the articles, F-6's swings, mates
    (a mate counts as 100) and the thresholds and bands in use all carry over. F-5's presumed
    results don't affect moments, and the line doesn't show a result.
- `--no-history`, the strip test and both golden sets (`tests/golden/site/`,
  `tests/golden/site-no-history/`, with their documented commands) are in the done-when. The fixture
  behind the golden sets (`tests/fixtures/site/analyzed/`) has the player as White and as Black and
  under aliases in another case (`AdaEx` for `--alias adaex`, `Example, Ada`). A hand-listed
  expectation there can catch a wrong "own" rule.
- **Counts reproduced**, read-only, with the library's own functions: `Collection.read(...,
  keep_analysis=True)`, then `review_moves` and the side's name match. The input was the owner's
  analyzed book (`chessgamescollection`, `book/analyzed/`), with player `Diego Amicabile` and
  aliases `diegoami`, `Amicabile, Diego`, `Amicabile`, `Amicabile Diego`, `Diego , Amicabile`.
  - 148 games were kept, none where both sides match;
  - 675 critical moments, 334 of them the owner's;
  - the worst is 30… Rd2, 2007.04.21, at 97.07 points (100.0 → 2.93);
  - 13 moves cost ≥ 50 points, the 13th exactly 50.0 (24… Qf7, 2007.01.13).
- `PLAN.md`'s row 6 agrees with the block: the request is verbatim, the done-when points to F-9's
  block, the mode is Claude Code (the standing choice), effort is medium and the reviewer is a
  fresh-context session. Its out-of-scope list is the remaining requests.
- Nothing else changed. In `ROADMAP.md`, the F-9 row changes (status `accepted`, iteration 6,
  "Shaped below") and the block is added. `PLAN.md` gets one row.

## Findings

1. **blocking — the library has no player, and the block names only the command line.**
   - **Evidence:** `ROADMAP.md:458` says "played by the player (by the site's `--player` and
     `--alias` names)", and `ROADMAP.md:470` says "Without a player (no `--player`/`--alias`…)".
     On `main`, the site builder can't know the player:
     - `build_site` (`pgn_postmortem/site.py:1174`) takes the games and options, with no player or
       aliases;
     - `Collection.build_site` (`pgn_postmortem/collection.py:380–385`) passes only `**options`,
       and `Collection` doesn't keep the names it read with;
     - `CollectedGame` carries no side;
     - `cmd_site` uses `--player` only for the title.

     The library is the product (the decided architecture: first a library), so the block needs to
     say how it gets the player.
   - **What the block should say:**
     - the parameter or parameters (e.g. `build_site(..., player=None, aliases=())`);
     - whether `Collection.read(..., player=…).build_site(out)` gets a quiz page without naming the
       player again;
     - that the names match as `Collection.read` matches them (letter case and surrounding spaces
       ignored, `player_names`), so the games kept and the moments called "own" follow one rule.
       F-4 plans to change that rule, and it should then change in one place;
     - the no-player case in library terms;
     - what a game with both sides matching gives.
   - **Done-when:** the "exactly the player's own" test should state that it covers an alias in
     another case (`AdaEx`) and the player as Black. Both are in the fixture.

2. **blocking — a stale `quiz.html` survives a rebuild, and the done-when can't see it.**
   - **Evidence:** `build_site` removes stale pages only in `out_dir/games/`
     (`pgn_postmortem/site.py:1246`, `(out_dir / "games").glob("*.html")`). `quiz.html` sits at the
     site's root, next to `index.html`.
   - **The failure:** a site built with a player and then rebuilt without one keeps the old
     `quiz.html`. It lists another build's moments and links to anchors that may no longer be those
     questions. The scope's "there is no quiz page" (`ROADMAP.md:470`) would then be false.
     `ROADMAP.md:479` ("without a player, there is no quiz page") would be tested on a fresh
     directory and would pass.
   - **What the block should add:**
     - a rebuild without a player removes a `quiz.html` the builder wrote (its `GENERATOR` line,
       `is_generated`);
     - it never removes a `quiz.html` the builder didn't write;
     - a test for each.

3. **non-blocking — the tie rule is not total, and "date" is undefined for partial and missing
   dates.**
   - **Evidence:** `ROADMAP.md:460` says "Ties are broken by date, then move order."
   - **The owner's book:**
     - exact ties occur: 5 pairs among the 334. One pair is in a single game: 43. bxc5 and 53. Kd2 in
       `7e1ffab381`, both 40.108;
     - 25 dates have more than one game;
     - one date is partial (`2007.12.??`);
     - a mate-for to mate-against move loses exactly 100.0, so exact ties are structural.
   - **Suggestion:**
     - say whether the order uses the exact loss or the displayed, rounded one;
     - end the rule with a total key, e.g. then the article order (the file stem: date, then id,
       undated last, which is how `build_site` orders articles), then move order;
     - test two games on one date and an undated game.

4. **non-blocking — the quiz lines' new `data-` attributes are not named.**
   - **Evidence:** F-8 fixed the history's `data-` attributes as "only the named ones … and where
     they belong":
     - `CLAUDE.md`'s tests gate;
     - `site.py`'s docstring: "these `data-` attributes and no others";
     - F-8's proposed items, confirmed by its merge.

     The quiz lines need a game and a move per line, which is new. `history.js`'s `indexGames`
     (`pgn_postmortem/static/history.js:143–145`) reads every `li[data-game]` in the document, and
     it runs on a page only when `section#history` exists. Reusing `data-game`/`data-moves` or the
     index's section on the quiz page would need care.
   - **Suggestion:** name the attributes, e.g. `data-game` and `data-move` on each quiz line. Say
     that the "only the named ones, where they belong" test extends to `quiz.html`.

5. **non-blocking — nothing ties a quiz line's key to the answer it links to.**
   - **Evidence:** these two done-when items are checked apart:
     - `ROADMAP.md:477` checks that the link reaches an existing `moment-N` anchor;
     - `ROADMAP.md:484` checks that a line is marked when its stored key is present.

     A line whose key is computed differently from the article's `data-move` would pass both, e.g.
     from the board after the move instead of `move_key(review.board_before)`. The scope's promise,
     "revealing an answer in an article marks it here", would still be broken.
   - **Suggestion:** assert that, for every quiz line, the answer inside its linked `#moment-N`
     carries the same `data-game`/`data-move` as the line. Ideally also add a Node test that opens
     that answer on the golden article page and then renders the golden quiz page with the same
     storage.

6. **non-blocking — "Clear history removes the marks" doesn't say where the button is.**
   - **Evidence:** the button exists only in the index's `HISTORY_SECTION`
     (`pgn_postmortem/site.py:606`). The block (`ROADMAP.md:468`, `ROADMAP.md:486`) doesn't say
     whether the quiz page gets its own.
   - **Suggestion:** state it. If the quiz page gets no button, the test is: after the index's
     clear, the quiz page shows no marks when loaded or restored from the back/forward cache.

7. **non-blocking — a player with no own moments is not covered.**
   - **The case:** a site with a player but no analyzed games, or no own critical moments, e.g. a
     fresh `read` before `analyze`.
   - **Suggestion:** say whether it gets an empty quiz page with a sentence and the index link, or
     no page, and test it.

8. **non-blocking — the records the implementation must update are not listed.**
   - **Evidence:** F-8's block named its `README.md` and `site.py` updates. F-9 adds a page to the
     site's layout, new `data-` attributes and new tested behaviour. Places to update:
     - the site layout in `site.py`'s opening docstring;
     - the history paragraph and its "no others" list;
     - `README.md`;
     - the "covers" cells of the tests and script gates in `CLAUDE.md` (gates discipline 1).
   - **Suggestion:** list them in scope or done-when, so the review can check them.

9. **non-blocking — the queue is not quite current (partly pre-existing).**
   - **Evidence:**
     - `ROADMAP.md:13`: F-1's iteration cell still says "(iterations 3 and 4 are F-5 and F-6, 5 is
       F-8)", without "6 is F-9".
     - `ROADMAP.md:20`: F-8's status is still `accepted`, but F-8 landed (#18, merge `3adbe08`,
       completion `9611197`) and F-9's block says "F-8 (landed)" (`ROADMAP.md:505`). This was
       already so on `main`, but the change touches the neighbouring row.
   - **Suggestion:** set F-8 to `landed` with its PR and commit, as F-5's and F-6's rows are, and
     add F-9 to F-1's iteration note.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
Two blocking findings remain (1 and 2).
