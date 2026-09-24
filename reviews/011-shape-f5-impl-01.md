# Review 011 — shape F-5, round 01

- **Revision covered:** `30b383377dbec5af87127e7fd8cddda39eef4ff2` (branch `shape-f5`, pull
  request #11). After `git fetch origin`, `git rev-parse origin/shape-f5` equals the pull request's
  `headRefOid`. The merge base with `origin/main` is `0fd6b4cf7dfb5a544b05b36e7790719e39d29696`,
  which is `origin/main` itself. The change is one commit on top of it.
- **Files checked:** `PLAN.md`, `ROADMAP.md`, `docs/book-plan.md`. The list comes from
  `gh pr view 11 --json files`. It is identical to
  `git diff --name-only $(git merge-base origin/main origin/shape-f5)..origin/shape-f5`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent.
- **Mode:** Claude Code.

What was read (all from `origin/shape-f5`):

- the rules: `PRINCIPLES.md`, `CLAUDE.md` and its slot, `ROADMAP.md`, `PLAN.md`,
  `reviews/README.md`;
- the code the scope depends on: `pgn_postmortem/collection.py`, `pgn_postmortem/site.py`,
  `pgn_postmortem/analysis.py` (`win_percent`);
- the site fixtures and golden files.

A read-only python-chess count was also run over the owner's analyzed book (`book/analyzed/` in
the owner's workspace). It found 148 games, 12 of them with `Result "*"`, all dated 2012, all
carrying `PostmortemAnalysis`, and none ending in checkmate, stalemate or insufficient material.
Their final White win percentages are 88.0, 100 (mate), 50.0, 0 (mate), 98.4, 97.6, 98.0, 6.7,
92.6, 98.1, 93.2 and 54.9. Every threshold from 55% to 85% gives the same 8 × 1–0, 2 × 0–1 and
2 × ½–½; 50% and 90% change the outcome. The block's claims "12 of the 148" and "any value from
60% to 85% gives the same result" therefore hold.

The following claims were confirmed against the code:

- The identity really includes the result: `game_id` hashes `Result`
  (`pgn_postmortem/collection.py:195`). The file stem, and so the article's file name, is built
  from that id (`collection.py:214-224`, `site.py:391-396`). Leaving the PGN's `Result` untouched
  keeps the identity, the analysis match and the page names stable.
- The "inaccuracys" defect is real. `plural(n, word)` appends `s` (`site.py:210-211`), and the
  conclusion calls it with `"inaccuracy"` (`site.py:677-679`). The golden files only ever show
  "one inaccuracy" (`tests/golden/site/games/2021-12-24-9137b96576.html:65`), which is why no test
  caught it.
- The PLAN.md renumbering is consistent. The ROADMAP F-1 row reads "1, 2, 4, 5 … iteration 3 is
  F-5", the F-5 row reads 3, and the PLAN table has rows 3/4/5/6+. No other file on the branch
  refers to iterations 3–5; `reviews/004-…` mentions "rows 1–4" as a historical record.
- `docs/book-plan.md`'s new status line is accurate on the facts. F-1.1 landed (`1c51ac4`) and F-1.2
  was merged in PR #8 (`05c6270`).

## Findings

1. **blocking** — The scope's list of places that show a result is incomplete, and done-when 1 does
   not cover the gap. `ROADMAP.md:131-132` says "wherever the site shows a result: the infobox, the
   lead, the conclusion and the index". The site also prints the result as the last token of the
   moves section: `tokens.append(esc(RESULTS.get(article.result, article.result)))`
   (`pgn_postmortem/site.py:631`). An implementation could leave a bare "\*" at the end of the
   moves. It would pass done-when 1 ("shows 1–0 in the infobox, lead, conclusion and index") while
   contradicting the player value ("every game in the book reads as finished") and the "never a
   bare \*" rule. Fix: add the moves section to the list in the scope and in done-when 1 (and 2–4).

2. **blocking** — The out-of-scope item on checkmate and stalemate misstates the code on `main`,
   and it contradicts the scope. `ROADMAP.md:152-153` puts out of scope "presuming results for
   games that ended by a rule the board shows (checkmate or stalemate are already decided by the
   moves and need no presumption)". On `main`, nothing derives a result from the board:
   - for a `Result "*"` game that ends in checkmate, the infobox prints "\*" (`site.py:517`), the
     lead says "Its result is not recorded" (`site.py:478-479`) and the index prints "\*"
     (`site.py:758`);
   - an unanalyzed game of this kind would, under the scope (`ROADMAP.md:134-135`), get "the result
     wasn't recorded" wording next to a checkmate on the board;
   - an analyzed one falls inside the scope anyway, because `white_cp` counts a checkmate as a full
     mate (`site.py:128-129`), so the presumption rule already applies. Done-when 4 ("a final forced
     mate gives the win") does not say whether it means an `[%eval #N]` or a mate on the board.

   None of the owner's 12 games is affected (checked above), so the fix is small. Either bring into
   scope a result read from the board (checkmate → win; stalemate or insufficient material → draw;
   analyzed or not, ahead of the percentage rule), or keep it out of scope with a correct reason and
   an explicit statement of what such a game shows. Then make done-when 4 say which case it tests.

3. **blocking** — The owner decisions lack their reasons, and one lacks its default.
   `PRINCIPLES.md:109-110` requires each owner decision to be "Recorded with a recommended default,
   the reason, and an owner-decision mark". At `ROADMAP.md:155-160`:
   - the marker decision gives the default ("mark it 'presumed'") but not why it was recommended;
   - the threshold decision gives the default (80%) but not why. The fact that 60–85% gives the same
     result on the owner's games is a reason the choice matters little, not the reason for 80%;
   - "F-5 lands now, before F-1.3" gives neither a recommended default nor a reason.

   Add one clause each. For example: "presumed", because a reader otherwise takes an inferred score
   for a recorded one; 80%, because it is closer to "much higher winning chances" in the owner's
   request; before F-1.3, because F-1.3's selection needs a result for every game.

4. **blocking** — Done-when 1–3 cannot tell the owner's 70% from another threshold. As written
   (`ROADMAP.md:140-143`: "≥70% for White", "≤30%", "in between"), fixtures at, say, 90%, 10% and
   50% would pass an implementation that used 60%, 80%, or the old default. They would also pass one
   that ignored the library parameter of `ROADMAP.md:136`. The owner's own data cannot catch this
   either, because every threshold from 55% to 85% gives the same results there. The owner's
   decision is therefore not enforced by any check. Fix: require boundary fixtures under the
   default, e.g. about 72–75% → win and about 65–68% → draw, mirrored for Black. Also require one
   test that setting the parameter (e.g. 80%) turns the ~75% game into a draw.

5. **non-blocking** — Done-when 5 needs to say where "no bare \*" applies. `ROADMAP.md:145`: "an
   unrecorded, unanalyzed game shows 'not recorded' wording and no bare '\*'". The scope keeps the
   article's PGN section as the source has it (`ROADMAP.md:134`), and that section contains
   `[Result "*"]` and a trailing `*` (`site.py:689`, `709`). A literal page-wide check is therefore
   unsatisfiable. Say "outside the PGN section: infobox, lead, moves, conclusion, index". Also note
   that the lead already has "not recorded" wording today (`site.py:479`). Only the "\*" part of
   this item can be shown failing first, so the fail-first evidence should target that part.

6. **non-blocking** — The block does not say where the new fixtures come from. The slot marks
   `tests/fixtures/site/analyzed/**` as generated output, "written once by
   `pgn-postmortem analyze`" and never hand-edited (`CLAUDE.md:73-74`, `115-116`). Stockfish will
   not easily produce games that end at a chosen 72% or 68%. One sentence would settle it before the
   session starts: say whether the tests build games in memory, with the `PostmortemAnalysis` header
   and hand-written `[%eval]` comments, or whether new source games are added and the analyzed
   fixture is regenerated. Done-when 7 also needs a fixture where one side has at least two
   inaccuracies; no current golden page has one.

7. **non-blocking** — Some edge cases of the rule are unstated:
   - an analyzed game whose final node has no `[%eval]` and is not a mate (`white_cp` returns
     `None`, `site.py:130`). Suggest that it falls back to the "not recorded" wording;
   - a threshold parameter set below 60%. The conclusion would then say of a presumed winner that
     "the result came from outside the position on the board: a resignation, the clock or an
     adjudication" (`site.py:664-671`), which is false for a presumed result. Suggest bounding the
     parameter (e.g. above 50% and at most 100%) or noting the interaction;
   - whether the parameter is also a command-line option of `site`, or API only
     (`ROADMAP.md:136`).

8. **non-blocking** — The block's fields differ slightly from *The block* format. The format's last
   field is "**Open questions:** owner decisions marked as such" (`ROADMAP.md:186`). F-5 has
   "**Owner decisions**" and an extra "**Mode:**" instead (`ROADMAP.md:155`, `161`). This is
   acceptable, but an "Open questions: none open; the owner's decisions follow" line would match
   the format. "**Mode:** Claude Code (the owner's standing choice)" also reads differently from
   the slot's "the owner picks the mode of each change when it starts" (`CLAUDE.md:51-52`) and from
   PLAN's "Claude Code (owner, 2026-09-24)" (`PLAN.md:40`). Suggest the same wording as PLAN.

9. **non-blocking** — The new status sentence in `docs/book-plan.md:10-12` is slightly inaccurate.
   It says the "Existing spike" section "lists what the `book-poc` branch holds beyond that". That
   table (`docs/book-plan.md:150-158`) also lists the package layout, the reading and the parallel
   analysis, which F-1.1 reused and which are now on `main`, so they are not "beyond" it. Suggest
   "lists what the `book-poc` spike holds, parts of which F-1.1 reused". Outside the diff, and only
   as a note: `docs/book-plan.md:57-61` ("caches results…", "PGNs that already carry evals need no
   Stockfish at all") and `:122` still describe trusting source evals. This contradicts the slot's
   decided item that every game is re-analyzed. The file's own status paragraph subordinates it to
   the slot, but a later tidy-up could align the text.

Nothing else changed: the diff touches only the three files above, with no code, tests or golden
files. The scope agrees with the slot's decided items. It presumes only for games that carry the
library's own analysis (`PostmortemAnalysis`), so a source's `[%eval]` is never trusted. It leaves
the identity rule and every PGN untouched, and it uses the move grading's win-percentage model.
F-5 is sized as one small iteration. The original wording is quoted identically in the queue row,
the block and the PLAN row. Whether the owner said it, and made these decisions, is checked by the
owner's merge, not by this review.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
Blocking findings remain: 1, 2, 3 and 4.
