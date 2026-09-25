# Review 020 — shape F-9 (pull request #20), round 02

- **Revision covered:** `d5d61829c4aebb5b3213be5b089dbb46756c84e1` (branch `shape-f9`), on top of
  `origin/main` at `2479e922bd01c1823cdce8cfbe7885679771405b`.
- **Target proof:** after `git fetch origin`, `git rev-parse origin/shape-f9` gives
  `d5d61829c4aebb5b3213be5b089dbb46756c84e1`, equal to `headRefOid` from
  `gh pr view 20 --json headRefOid,files`. The branch has three commits: `51176ff` (the shaping),
  `8509c2b` (round 01's record) and `d5d6182` (the answer).
- **Files checked:** `PLAN.md`, `ROADMAP.md`, `reviews/020-shape-f9-impl-01.md`. The pull request's
  file list equals
  `git diff --name-only $(git merge-base origin/main origin/shape-f9)..origin/shape-f9`. Files were
  read with `git show origin/shape-f9:<path>`, and the round's changes with
  `git diff 51176ff d5d6182`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a Claude Code subagent. It continues the
  round-01 reviewer session, which did not see the shaping, and re-read the current revision.
- **Mode:** Claude Code.

## What changed since round 01

- `reviews/020-shape-f9-impl-01.md` is byte-identical to the round-01 review as written (`cmp`).
- `d5d6182` changes only `ROADMAP.md`: F-1's iteration note, F-8's row and F-9's block. `PLAN.md`
  is unchanged since `51176ff`. Nothing else changed.

## Round-01 findings, checked

1. **Blocking 1 (the library has no player): resolved.**
   - **What the block now says** (`ROADMAP.md:457–463`):
     - `build_site` gains `player` and `aliases`;
     - `Collection.build_site` passes on the names its collection was read with;
     - the `site` command passes `--player`/`--alias`;
     - names match "exactly as `Collection.read` matches them", ignoring letter case and surrounding
       spaces. That is `player_names`'s rule on `main`;
     - no player means no quiz page;
     - a game where both sides match counts both.
   - **The done-when** tests case and spaces, and both sides (`ROADMAP.md:497–498`).
   - **Both sides counting is sensible:** each such move was made by one of the player's names, and
     the owner's book has no such game (0 of 148, round 01).
   - A gap remains in how `Collection` keeps the names; see finding 1 below.
2. **Blocking 2 (a stale `quiz.html`): resolved.**
   - **Scope** (`ROADMAP.md:485`): a `quiz.html` the builder wrote is removed on a rebuild without a
     player, and one it didn't write never is.
   - **Done-when** (`ROADMAP.md:503`) tests both. See finding 2 below for a wording error.
3. **The tie rule: resolved, and the rule is now total.**
   - **The rule** (`ROADMAP.md:468–470`): the exact, unrounded points, then the game's position in
     the index, then the article's file name, then move order.
   - **Why it is total:** on `main` the index lists each game once, dated years first and then
     undated. Within a year the games follow the articles' order, sorted by file stem (`build_site`,
     `index_html`). Every game has one position, and within a game every move has one ply.
   - The file-name step can never decide anything, since the index position already follows the
     stem. It is harmless.
4. **The `data-` attributes: resolved.**
   - Each line carries the game id and the move under F-8's names, and F-8's "only these" list is
     extended by exactly those two on the quiz page.
   - The done-when extends F-8's attribute test to the quiz page.
   - The example key `30b` for 30… Rd2 is what `move_key` gives.
   - The quiz page has no `section#history`, so `history.js`'s index code won't treat its lines as
     index entries.
5. **Tying a line's key to its answer: resolved.** A new done-when item checks that each line's
   `data-` game and move equal those on the answer it links to.
6. **Where "Clear history" is: resolved.** The index's button is the only one, and it removes the
   quiz page's marks too.
7. **A player with no own moments: resolved.** The page says so instead of showing an empty list,
   and this is tested.
8. **The files to update: resolved.** They are listed: `README.md`, `site.py`'s docstring, and
   `CLAUDE.md`'s "covers" cells for the tests and script gates.
9. **The queue: resolved.**
   - F-1's note now says "6 is F-9".
   - F-8 is `landed` "in #18 (`3adbe08`), 2026-09-25". `3adbe08` is "Merge pull request #18"
     (2026-09-25 15:49 +0200), and `gh pr view 18` reports the same merge commit.
   - The "phone check deferred to the live book" matches F-8's completion note
     (`reviews/018-f8-reading-history-impl-02.md` on `main`, done-when 3).

**The proposed items** (`ROADMAP.md`, the end of F-9's block) are clearly marked "Proposed with this
shaping, confirmed by the owner's merge". They now include:
- the `player`/`aliases` parameters and how they match;
- both sides counting when both match;
- the tie rule;
- the two `data-` attributes;
- the "none" page;
- the index's button as the only clear;
- removing a stale `quiz.html`.

## Findings

1. **non-blocking — `Collection` doesn't keep its names today, and no test checks that it does.**
   - **Evidence:** `ROADMAP.md:458–459` says "`Collection.build_site` passes on the names its
     collection was read with". On `main`, `Collection.__init__(self, games, report)` keeps no names,
     and `Collection.read` uses them only to filter (`pgn_postmortem/collection.py`). So the block
     implies a new stored attribute without saying so.
   - **Why it matters:** the done-when tests don't cover this route. `cmd_site` calls the module's
     `build_site` directly, so the golden sets exercise only the command line. An implementation
     where `Collection.build_site` passes nothing would pass every listed check, and a library user's
     `Collection.read(..., player=…).build_site(out)` would silently get no quiz page.
   - **Suggestion:**
     - say that `Collection` keeps the names `read` was given;
     - say what happens with a `Collection(games)` built directly (no names) and with a
       `player=`/`aliases=` passed explicitly to `Collection.build_site`;
     - say whether `build_site(collection, out)`, the module function given a `Collection`, uses them
       too. As written it does not, which differs from the method;
     - add a done-when line: `Collection.read(ANALYZED, player=…, aliases=…).build_site(out)` writes
       the quiz page.
2. **non-blocking — the generator mark is not F-8's.**
   - **Evidence:** `ROADMAP.md:485` says "it carries F-8's generator mark". `GENERATOR` and
     `is_generated` (`pgn_postmortem/site.py`) came in `0602071` ("Escape-test the site, survive odd
     dates, delete only pages it wrote"), before F-8, with F-1.2's rebuild rule.
   - **Suggestion:** say "the builder's generator mark (`GENERATOR`)".
3. **non-blocking — the no-player rule is stated twice.** `ROADMAP.md:461` ("No player") and
   `ROADMAP.md:489` ("Without a player") agree. The second could be dropped or point to the first.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
