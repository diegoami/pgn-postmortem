# Review 022: shape F-10 (pull request #22), round 01

- **Revision covered:** `ef3dde91e65fee717e005aa653e5e3add7efa9e7` (branch `shape-f10`), on top of
  `origin/main` at `d1b593e5d52e8c4317d3dbfb72417007e5de1d55` (the merge base).
- **Target proof:** after `git fetch origin`, `git rev-parse origin/shape-f10` gives
  `ef3dde91e65fee717e005aa653e5e3add7efa9e7`, which equals `headRefOid` from
  `gh pr view 22 --json headRefOid,files`. The branch has one commit (`ef3dde9`).
- **Files checked:** `PLAN.md` and `ROADMAP.md`. The pull request's file list
  (`gh pr view 22 --json files`) equals
  `git diff --name-only $(git merge-base origin/main origin/shape-f10)..origin/shape-f10`. The files
  were read with `git show origin/shape-f10:<path>`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that did
  not see the shaping.
- **Mode:** Claude Code.
- **Read against:** `PRINCIPLES.md` (*Owner decisions*, the verdict protocol), `CLAUDE.md` and its
  slot (the three gates and the covers cell of the tests gate, the two golden sets, the decided
  items), `ROADMAP.md` (*The block*, *The agent's job*, *Statuses*, *Artistic license*, F-8's and
  F-9's blocks, and F-10's row on `main`), `PLAN.md`, `reviews/README.md`. From `main`, also:
  `pgn_postmortem/site.py`, `tests/test_site.py`, `tests/test_history.py`, `tests/test_quiz.py`,
  `README.md`, and the fixtures in `tests/fixtures/site/`.
- **Network checks (read-only GETs, 2026-09-25):** each lichess URL form was fetched with `curl`,
  and the page's `page-init-data` JSON was read.

## What holds

- F-10's block has every field of *The block*: original request, player value, scope, done when,
  out of scope, depends on and open questions. It also adds an "Also in the owner's words" line.
  The original request is verbatim and matches F-10's row on `main`. The second quote,
  "Another feature to add is having a link to open the full PGN game on lichess,", is also verbatim.
  The block says "Each new assertion is shown failing first".
- F-10's row keeps its wording and both earlier owner decisions. It drops "Not shaped yet.", adds
  "Shaped below.", and moves from `requested` to `accepted` with iteration 7. `accepted` is a middle
  state, which the agent may set (*Statuses*).
- The two new owner decisions (the link inside the hidden answer; a new tab, with the game link in
  the infobox) each have a recommended default, a reason and the alternatives not chosen. The first
  two decisions point to the row, which carries their defaults and reasons. The proposed items are
  listed separately under "Proposed with this shaping, confirmed by the owner's merge". The
  repository can't show that the owner made these decisions; the owner's merge is that check.
- The block is consistent with the code on `main` in these ways:
  - the infobox is one table (`infobox_html`, `pgn_postmortem/site.py:826`);
  - the answer is `<details class="answer">` inside `moment_html` (`site.py:919`);
  - a moment's diagram is `review.board_before`, the position before the move (`site.py:878`,
    `site.py:225`). "The position before the move (the question's position)" is therefore the
    diagram's position.
- The block is consistent with F-8's rules. The links add no `data-` attribute. F-8's URL and
  network test (`tests/test_history.py:94`) reads only the script, not the pages, so plain links
  don't conflict with it. The strip test (`tests/test_history.py:194`) is unaffected, because the
  links are in both golden sets.
- The decided items hold: the analysis stays our own, nothing is hosted, and Stockfish in the
  browser stays out of scope, as the row says.
- The lichess URL forms:
  - The FEN form works. `https://lichess.org/analysis/rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR_b_KQkq_-_0_1`
    returns 200, and the page's `treeParts` holds that FEN. The same holds for a FEN with an
    en-passant square (`..._w_KQkq_e6_0_3`).
  - The `pgn/` form works too. `https://lichess.org/analysis/pgn/1.e4%20e5%202.Nf3%20Nc6` returns
    200 with `"inlinePgn":"1.e4 e5 2.Nf3 Nc6"`. `#` (`%23`), `O-O`, captures and `=` (`%3D`) all
    reach `inlinePgn` intact. `+` does not: see finding 3.
- F-9 is marked landed in #21 (`f9c54d3`). `gh pr view 21` shows state MERGED, with merge commit
  `f9c54d3542afdf51915e6925e620084c607129c7`. F-1's row adds "7 is F-10".
- PLAN.md's row 7 follows rows 5 and 6: the request is quoted verbatim, the plan is F-10's block,
  F-10 is out of its own out-of-scope list, the mode is Claude Code, the effort is small, and the
  reviewer is a fresh-context session. Nothing else in the diff changes.

## Findings

1. **blocking**: the block conflicts with the standing check "every link relative", and it doesn't
   say how that check changes.
   - **Where it conflicts:**
     - `check_links` (`tests/test_site.py:151-172`) asserts that every `href` and `src` has no
       scheme and no host, and that it resolves to a file inside the site:
       `assert not parts.scheme and not parts.netloc ... f"not relative: {where}"`. This check runs
       on the analyzed and not-analyzed sites (`test_site.py:194`, `:278`) and on the quiz sites
       (`tests/test_quiz.py:195`, `:258`). Every `https://lichess.org/...` link fails it.
     - The escape test's attribute allowlist (`test_site.py:227-230`) has `rel` but not `target`.
     - The gates table's covers cell in `CLAUDE.md` says "one article per game with every link
       relative and resolving (files and anchors)".
     - `README.md:194-195` says "every link is relative, nothing loads from the network".
     - `site.py`'s docstring (lines 15-17) says "Every link is relative and names a file".
   - **What the block says:** only "no new `src`", in done-when 4. It doesn't say that `check_links`
     must be narrowed, how, or that the covers cell, `README.md` and the docstring are updated.
   - **Why it matters:** relaxing an existing gate assertion changes what a check measures.
     *Artistic license* allows extending a check with the reason recorded, never weakening one, so
     this is for the shaping to decide, not for the implementer to improvise. F-9's block had a
     "Files to update" line for the same purpose.
   - **Fix:**
     - State that `check_links` still requires every other `href`/`src` to be relative and
       resolving.
     - State that it exempts exactly the two lichess forms, and only where they may appear: the one
       infobox game link and the one link per answer `<details>`. Any other absolute link still
       fails.
     - State that `target` joins the allowlist.
     - Add "Files to update": `README.md`, `site.py`'s docstring, and the tests gate's covers cell
       in `CLAUDE.md`. The wording should be that internal links are relative, the pages load
       nothing, and the only external links are the lichess links, which the reader taps.
   - **A related note, not a separate finding:** the escape test reads the infobox as a `th`/`td`
     dict over `tr[1:]` (`test_site.py:245`). The block should say the game link is a
     `<tr><th>…</th><td>…</td></tr>` row, or say where else it goes.

2. **blocking**: done-when 2, and the set-up half of done-when 3, can pass without testing
   anything.
   - **The gap:**
     - The only fixtures with a `FEN` header are in `tests/fixtures/site/synthetic/`: `mate-white`,
       `mate-black`, `stalemate`, `stalemate-analyzed` and `insufficient-material`.
     - None of them has a critical moment. `stalemate-analyzed.pgn` is one move, `50. Qf7`, and a
       first move is never graded (`MoveReview` docstring, `site.py:205-207`).
     - The golden fixture (`tests/fixtures/site/analyzed/`) has no set-up game.
   - **The wrong implementation it lets through:** "its critical positions still have their links"
     would hold vacuously. Suppose the implementer wraps both links in `if no FEN header`, or builds
     the FEN by replaying from the standard start. That code passes done-when 2 and 3 as written.
   - **Fix:**
     - Name a new hand-written fixture: a set-up game with at least one critical moment, following
       the convention of `synthetic/`, `swings/` and `quiz/` (not generated, and described in a
       README).
     - Have the test assert that it checked at least one position link in a set-up game.

3. **non-blocking**: lichess reads `+` in the `pgn/` path as a space, and the tests' decoding rule
   isn't stated.
   - **What lichess does:**
     - `.../pgn/1.e4%20f5%202.Qh5%2B%20g6` gives `"inlinePgn":"1.e4 f5 2.Qh5  g6"`.
     - A literal `+` gives the same.
     - `1.e4_e5_2.Nf3` and `1.e4+e5+2.Nf3` both give `"1.e4 e5 2.Nf3"`.
   - **The effect:** check signs never reach lichess. SAN without `+` should still parse, but that
     happens on the client and can't be checked with `curl`.
   - **For done-when 1:**
     - Say that the test decodes `urlsplit(href).path` with percent-decoding only (`unquote`, not
       `unquote_plus`), and that it asserts the URL has no query and no fragment. Otherwise an
       unencoded `#` (which the browser treats as a fragment) or a `quote_plus` form could pass.
     - Alternatively, write the URL in the form lichess reads (`_` separators, `+` dropped) and
       decode it the same way.
   - **For the owner's check:** include a game with a check in it.
   - **The existing fixtures:** the analyzed fixture has `+`, `#` and `O-O`, but no promotion. `=`
     is untested unless a fixture adds one.

4. **non-blocking**: the reason for "no game link for set-up positions" is stated as fact but wasn't
   verified.
   - **What was seen:** `.../pgn/%5BFEN%20%228/P7/8/8/8/8/8/k6K%20w%20-%20-%200%201%22%5D%201.a8%3DQ%2B`
     is accepted, and lichess passes `[FEN "8/P7/8/8/8/8/8/k6K w - - 0 1"] 1.a8=Q` through as
     `inlinePgn`. Whether the board then applies that FEN happens on the client, so it wasn't
     checked here.
   - **Fix:** reword `ROADMAP.md:566` to state the choice ("not attempted; a PGN with a `FEN` tag in
     the path is untested"), or check it by hand. The decision itself is a proposed item that the
     owner's merge confirms.

5. **non-blocking**: a game with no moves isn't covered. `https://lichess.org/analysis/pgn/` with
   an empty path returns 301. No fixture has a zero-move game, so done-when 1 would never meet one.
   A game with only headers, such as a forfeit, would get a link to an empty board. Say whether such
   a game gets no game link (the simplest choice), or leave it out of scope explicitly.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
Two blocking findings remain (1 and 2).
