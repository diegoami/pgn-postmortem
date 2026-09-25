# Review 023, F-10 (lichess links), implementation round 01

- **Revision covered:** `3c73ba1cedcc6fb4143bcfddb28790802900e5a1`, the head of pull request #23
  (branch `iteration-7-lichess-links`). The checked-out `HEAD` equals the PR's `headRefOid`.
- **Base:** `335b6e359ea8a5157ff2aba5cee6f173b656a108` (`git merge-base origin/main HEAD`, equal to
  `origin/main`).
- **File list and how it was obtained:** `gh pr view 23 --json files` and
  `git diff --name-only <merge-base>..HEAD` give the same 24 files:
  - `CLAUDE.md`, `README.md`, `pgn_postmortem/site.py`;
  - `tests/fixtures/site/lichess/README.md`, `promotion.pgn`, `setup-blunder.pgn`,
    `standard-fen.pgn` (new);
  - `tests/golden/site/assets/style.css` and `tests/golden/site/games/{2019-03-14-bf58e2afa0,
    2019-04-02-5d1415e1ac, 2020-06-01-9705c13f05, 2021-09-10-a9c90416b2, 2021-12-24-9137b96576,
    undated-5ce208cdcb}.html`;
  - the same seven files under `tests/golden/site-no-history/`;
  - `tests/test_lichess_links.py` (new), `tests/test_quiz.py`, `tests/test_site.py`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that did
  not see the implementation.
- **Mode:** Claude Code.
- **Contract:** F-10's row and block in `ROADMAP.md`, the three points in the completion note of
  `reviews/022-shape-f10-impl-02.md`, PLAN.md iteration 7, and `CLAUDE.md`'s slot.

## What was checked

- **Gates, in a fresh venv** (`pip install -r requirements-dev.txt && pip install -e .`, Stockfish
  on PATH, Node v24.21.0):
  - `ruff check .`: all checks passed;
  - `pytest -q`: 205 passed, none skipped;
  - `node --test 'tests/js/*.test.mjs'`: 32 passed.

  CI on the head is green: `test (3.11)` and `test (3.13)`.
  The first commit (`570ca8b`, the narrowed check alone) also passes on its own: 197 passed.
- **Golden sets:** both regenerated with the slot's documented commands into a scratch directory.
  `diff -r` against `tests/golden/site/` and `tests/golden/site-no-history/` is empty. The committed
  changes are exactly as the PR describes:
  - one CSS rule (`.infobox .lichess`);
  - a game link under the final position in all six articles;
  - a position link inside the one answer of the four articles that have a critical moment.

  `index.html` and `quiz.html` are unchanged in both sets. Nothing changed in `scripts/`,
  `examples/` or `pgn_postmortem/static/history.js`.
- **The game URL:** `lichess_game_url` (`pgn_postmortem/site.py:652-665`) produces one form:
  - bare SAN with `rstrip("+#")`;
  - spaces as `%20` and `=` as `%3D` via `quote(..., safe="")`;
  - no query and no fragment.

  An independent script checked every built article of the golden set, the lichess set and the
  swings set. For each, the script parsed the article's `<pre class="pgn">` with python-chess and
  rebuilt the expected URL. It matched every time. It also found no game link where the game is
  set up or has no moves.
- **The position URL:** `moment_html` passes `review.board_before`, the question's board
  (`site.py:930`, `site.py:966`). The same script decoded each position link (`_` back to spaces)
  and found each one among the positions before a mainline move. The test
  `test_every_critical_moment_has_one_position_link_to_the_position_before_its_move` checks each
  link against the exact move its answer names.

  I checked some by hand as well:
  - `2020-06-01` gives the position before 3... Nf6 (Black to move, `3_3`);
  - `2021-12-24` gives the position before White's 5th move (`w_KQkq_-_1_5`);
  - `setup-blunder.pgn` gives the position after 30... h6. That is neither the header's position
    nor the one after 31. Ra7.
- **Placement and attributes:**
  - The position link is the last `<p>` inside `<details class="answer">`.
  - The game link is in `td.figure` inside `table.infobox`.
  - Both links have `target="_blank" rel="noopener noreferrer"` exactly, with `href` escaped by
    `attr`.
  - The link texts are those in the block.
- **Narrowed `check_links`** (`tests/test_site.py:154-236`):
  - An absolute `href` or `src` passes only as an `<a href>`. It must be of the `pgn/` form inside
    `table.infobox`, or of the non-`pgn/` form inside `details.answer`. It needs something after
    the prefix, no `?` or `#`, and both attributes with exact values.
  - `target` fails on any element that is not such a link.

  I read all 20 planted cases (`BAD`, `tests/test_site.py:250-271`). They cover:
  - other sites;
  - `http`, protocol-relative and root-relative links;
  - other lichess paths;
  - each form in the wrong place;
  - a query, a fragment and empty paths;
  - a missing `target`, a wrong `target`, and `rel` without `noreferrer`;
  - `<img src>` and `<link>`;
  - `target` on a relative link.

  Each case asserts that the unplanted site passes first. The two positive controls check that
  the matching count goes up by one.
- **Completion-note points:**
  - Only `target` was added to the escape test's `ATTRIBUTES` (`tests/test_site.py:371`), and
    `check_links` enforces `target` only on lichess links (`tests/test_site.py:234-235`). The
    escape test also asserts `.games == 3`.
  - The no-moves game is built directly as a `CollectedGame`, after asserting that
    `Collection.read` skips it (`tests/test_lichess_links.py:184-201`, both standard and set-up).
  - There is one fixed URL form, and the tests compare with `unquote` against the bare SAN string.
- **Set-up fixture:** `setup-blunder.pgn` has a `FEN` header and one critical moment. The test
  asserts no game link, one position link inside the answer, the FEN worked out by hand, and
  `check_links(...).positions >= 1` with `.games == 0` (`tests/test_lichess_links.py:169-181`). The
  README marks the fixtures as hand-written.
- **Docs:** the gates-table "covers" cell in `CLAUDE.md`, README's site section and "Lichess links"
  paragraph, and `site.py`'s module docstring no longer say that every link is relative. They
  describe the two links and the narrowed check.
- **Reproduction: one break at a time.** I applied each break by a script. I cleared
  `__pycache__`, ran `pytest -p no:cacheprovider`, then restored the file. `git status` was clean
  afterwards. The new tests that went red:

  | break | new tests red (besides golden-file tests) |
  |---|---|
  | FEN after the move (`review.node.board()`) | set-up-game, every-moment-position |
  | `+`/`#` kept | every-game-link, promotion-encoding |
  | position link moved after `</details>` | set-up-game, every-moment-position, new-tab, `check_links` in quiz/site tests (31 failed) |
  | `rel` dropped | set-up-game, new-tab, `check_links` everywhere (35 failed) |
  | `check_links` accepting any `https://` absolute link | 12 planted cases, among them another site, another lichess page, and each form in the wrong place |
  | `check_links` accepting any lichess-prefixed link in any place | 6 planted wrong-place/empty cases |
  | game link for set-up games | every-game-link, set-up-game |
  | game link for games without moves | no-moves[standard] |
  | spaces as `+` | every-game-link, standard-FEN, promotion-encoding |
  | `target` allowed on any element | `a target on a relative link` |
  | "has a `FEN` header" deciding the game link | every-game-link, standard-FEN |
  | FEN spaces as `%20` instead of `_` | set-up-game, every-moment-position |

- **lichess, by plain `curl` GET (2026-09-25):**
  - The promotion fixture's game link
    (`.../analysis/pgn/e4%20d5%20exd5%20c6%20dxc6%20Qb6%20cxb7%20Qxf2%20Kxf2%20Nf6%20bxc8%3DQ`,
    with a check and a promotion that mates) returned HTTP 200. The page's data carries
    `"inlinePgn":"e4 d5 exd5 c6 dxc6 Qb6 cxb7 Qxf2 Kxf2 Nf6 bxc8=Q"`.
  - The golden `2021-12-24` position link
    (`.../analysis/r1b1kbnr/pppp1ppp/8/4N1q1/2BnP3/8/PPPP1PPP/RNBQK2R_w_KQkq_-_1_5`) returned
    HTTP 200 with `"fen":"r1b1kbnr/pppp1ppp/8/4N1q1/2BnP3/8/PPPP1PPP/RNBQK2R w KQkq - 1 5"`.

## Findings

1. **non-blocking**: "a set-up position" is decided by the starting board, not by the literal
   "(a `FEN` header)" of the block.
   - The code is `if board.fen() != chess.STARTING_FEN or game.next() is None:`
     (`pgn_postmortem/site.py:659`). `ROADMAP.md:569` says "a game that starts from a set-up
     position (a `FEN` header)", and done-when 2 repeats the parenthetical.
   - My judgement: the implementation follows the block's intent.
     - The block's reason for excluding set-up games is that a `[FEN …]` tag in the path is
       unverified. That reason does not apply when the game starts from the standard position,
       because the link carries no FEN tag.
     - The choice matches the identity rule, where such a header "counts the same as none"
       (`README.md:181`, `collection.py:194`).
     - It is pinned by `standard-fen.pgn` and by
       `test_a_standard_start_spelled_out_in_a_fen_header_still_gets_its_game_link`.
     - A break that switches to "has a `FEN` header" turns two tests red.
   - The PR discloses the choice, and README, `CLAUDE.md` and the docstring describe it.
   - Since the block lists "no game link for set-up positions" among the items "confirmed by the
     owner's merge", the owner should see this reading at merge. The landing could also align the
     block's wording ("a `FEN` header other than the standard start").
2. **non-blocking**: a game in a lichess variant that starts from the standard FEN gets a
   standard-chess game link.
   - `lichess_game_url` compares `game.board().fen()` with `chess.STARTING_FEN`
     (`pgn_postmortem/site.py:658-659`). python-chess gives, for example, an Atomic or
     King of the Hill board the standard starting FEN.
   - I read a hand-made `[Variant "Atomic"]` game through the `site` command. It got
     `.../analysis/pgn/e4%20d5%20exd5`, which lichess opens as standard chess. The position links
     would also open as standard chess.
   - This is not in F-10's contract. The rest of the site, and the Stockfish analysis, already
     treat every game as standard chess, so it is an existing gap that F-10 inherits, not a
     regression.
   - If lichess exports of variant games can reach the collection, suggest a ROADMAP note, or
     skipping the links for a `Variant` header other than `Standard`, for the owner to decide.
3. **non-blocking**: the game link sits in the final-position cell, not in its own infobox row.
   - It is `lichess = f'\n<div class="lichess">…</div>'` appended after the caption
     (`pgn_postmortem/site.py:908`, `site.py:917`).
   - My judgement: this meets "in each article's infobox". It keeps every row's `th`/`td` pair
     that existing tests read. It puts the link next to the board it opens. It needs one CSS rule.
   - Nothing to change. It is recorded here because the block and the owner's decision named only
     "the infobox".

No other defects were found. The owner's check on a served preview of the owner's book is still
pending, as the PR says. It is the owner's step before merging and not part of this review.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged on 2026-09-25 as `f3b4dea` (pull request #23), on the owner's go. The clean round, 01, covers `3c73ba1`. CI on the merge commit passed on Python 3.11 and 3.13: https://github.com/diegoami/pgn-postmortem/actions/runs/36173249312. F-10's done-when (`ROADMAP.md`, F-10's block):

1. **Game links:** each game from the standard start that has moves has one game link in the infobox. It decodes to the mainline's bare SAN without `+`/`#`, with no query or fragment, and a fixture with checks, a mate and a promotion covers this.
2. **Set-up games:** the hand-written set-up fixture has a critical moment and no game link, and its position link is asserted checked. A game without moves, built directly for `build_site`, has no game link.
3. **Position links:** one per critical moment, inside its closed answer, with the FEN of the position before the move; none elsewhere.
4. **The narrowed `check_links`:** only the two lichess forms in their two places, with `target="_blank" rel="noopener noreferrer"`. `target` is allowed nowhere else, and 20 planted bad links are all rejected.
5. **Golden sets:** both regenerated (the CSS rule, game links in all six articles, position links in the four with moments).

**The owner's check:** a served preview of the owner's book at `3c73ba1` (148 game links, 675 position links; the Pedroni game's game link and a position link): "Checked, looks fine, merge". It was recorded on the PR by the orchestrator (https://github.com/diegoami/pgn-postmortem/pull/23#issuecomment-5837419007), not signed by the owner.

**The gates:** `ruff check .` is clean, `pytest -q` gives 205 passed, and the script gate gives 32 passed.

**Owner decisions on the review's findings:**
- **Finding 1:** set-up games are decided by the starting board, which is accepted. F-10's plan text gets aligned in a later record change.
- **Finding 2:** games of a variant getting a standard-chess link goes into the roadmap as a note for later.
- **Finding 3:** the game link's placement in the final-position cell stays as it is.

— Implementer, Claude Opus 5.5 (claude-opus-5-5)
