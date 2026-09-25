# Review 014 — shape F-6, round 01

- **Revision covered:** `a30d861a782c1498b73b53268f7d5f2769baf8f4` (branch `shape-f6`, pull request #14).
- **Target proof:** after `git fetch origin`, `git rev-parse origin/shape-f6` gives
  `a30d861a782c1498b73b53268f7d5f2769baf8f4`, which equals `headRefOid` from
  `gh pr view 14 --json headRefOid,files`. The merge base with `origin/main` is `2330744`, which is
  `origin/main` itself. The change is one commit, `a30d861`. I proved the target twice, before and
  after an interruption of this session, with the same result.
- **Files checked:** `PLAN.md` and `ROADMAP.md`. The PR's `files` list and
  `git diff --name-only $(git merge-base origin/main origin/shape-f6)..origin/shape-f6` agree.
  Everything was read with `git show origin/shape-f6:<path>` and `git diff origin/main origin/shape-f6`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent.
- **Mode:** Claude Code.

## What I checked

- **The code on `main`.**
  - `pgn_postmortem/site.py`: `review_moves` picks critical moments by `loss >= thresholds.mistake`.
    `moment_html` looks for the better line and the refutation with `engine_line` and falls back to
    "The analysis records no better move than …".
  - `pgn_postmortem/analysis.py:188-201`: this is where the lines are stored.
- **The owner's data.** I read it without changing it, with python-chess and the library's own
  `review_moves`, `win_percent` and `engine_line`, on the 148 files in the workspace
  `chessgamescollection`, `book/analyzed/`. All 148 carry the analysis marker. I applied the rule as
  written: the bands are ≥65, ≤35 and level in between, taken from White's chances before and after
  the move; a swing moves the band against the side that moved and costs it at least 10 points.
  - **The totals hold:** 390 critical moments. Adding the swings that are not already critical
    moments gives **239 extra moments in 97 games**. Another 362 swings are already 20-point
    moments.
  - **The example game `2008-01-04-4e5d4e182f` holds:**
    - 31… Qa2: 3.4 → 31.5 for White, 28.1 points, critical, not a swing;
    - 37… Rg2+: 25.0 → 41.3, 16.4 points, a swing;
    - 40. Ra4: 48.8 → 31.8, 17.0 points, a swing.

    All three have a better line and a refutation stored. The headers now read
    Event "Festival Verona 2008" and Site "Verona", so the block's label is accurate (review 011,
    round 03, finding 1).
- **Statuses and iterations.**
  - F-5 is `landed` (#13, `88ebc62`, merged 2026-09-25). Review 013's completion note records the
    owner's decision to mark it.
  - F-6 is `accepted`, iteration 4.
  - F-1 is on iterations 1, 2, 5 and 6. Its slices landed in #6 (`ccc0f89`) and #8 (`05c6270`); I
    checked both against the merge log.
  - `PLAN.md` gives 4 = F-6, 5 = F-1.3, 6 = F-1.4, 7+ = the rest. The two files agree, and every
    status is in the *Statuses* vocabulary.
- **The block and the PR body.** F-6's block has all seven fields of the block format, and its
  original request matches the row word for word. The PR body has no gendered pronouns for the
  owner (I searched it for he/him/his/she/her). Nothing outside the F-1, F-5 and F-6 rows, the new
  block and `PLAN.md` rows 4–7+ changed.

## Findings

1. **blocking** — The block's claim that the needed lines are always stored is false on the owner's
   data and in the code.
   - **The claim:** "a move graded inaccuracy or worse always has its better line stored"
     (`ROADMAP.md:225`). The PR body repeats it: "Every new moment already has its engine line".
   - **The code:** `analysis.py:194` stores the better line only
     `if pv_before and pv_before[0] != move`, so no better line is stored when the move played was
     the engine's own first choice. The refutation is also dropped after the game's last move
     (`analysis.py:199`).
   - **The data:** 3 of the 239 new moments are moves the engine itself chose. The loss comes only
     from how the eval changed between one search and the next:
     - `2005-09-24-3bd9df323c`, 45… Qa6 (50.0 → 31.3 for the mover);
     - the same game, 47… Qa6 (50.0 → 33.9);
     - `2008-01-05-ec4df50311`, 18… Qxd4 (42.0 → 31.1).

     Each would become a "What would you play?" question whose answer is "The analysis records no
     better move than" the move played. None of the 390 existing critical moments has this problem.
   - **Fix:** correct the sentence, and say what F-6 does with such a move. Two options:
     - leave out a swing whose move was the engine's first choice, with a done-when item for it;
     - or keep it, and state that its answer says the engine found no better move.

   The reason given for the 10-point floor stays true: below 10 points no line is stored at all.

2. **blocking** — The done-when doesn't cover the prose that the new moments make false.
   - The scope says a swing "counts in the infobox, the lead and the conclusion" (`ROADMAP.md:220`).
   - The lead on `main` says "The engine found N critical moments, where a single move cost at least
     20 points" (`site.py:575`). A swing costs 10–19 points, so this sentence becomes false for
     every game with a swing. Its "no critical moment … 20 points" branch changes meaning as well.
   - The conclusion has no count of critical moments today; it tallies grades. So "counts in … the
     conclusion" doesn't describe anything in the code.
   - None of items 1–7 checks the count or the wording. An implementation that adds the diagrams
     and leaves the lead unchanged passes every item. The regenerated golden files would show it
     only if the fixture has a swing below 20 points.
   - **Fix:** extend item 1 or add an item: the lead and the infobox count the swings, the lead
     doesn't say that every moment cost 20 points, and the conclusion is either named with what
     changes in it or dropped from the scope sentence.

3. **blocking** — The first owner decision has no reason (`ROADMAP.md:252-254`).
   - "Which moments get extra diagrams" gives the recommended default ("the deciding moment") and
     the owner's choice. It gives no reason for that default, and none for the choice.
   - `PRINCIPLES.md`, *Owner decisions*, requires "a recommended default, the reason, and an
     owner-decision mark". The other two decisions have their reasons.
   - **Fix:** add one sentence with the reason.

4. **non-blocking** — Item 6's edge test can't be run at the default bands on an `[%eval]` fixture.
   - Exactly 65% needs about 168.12 cp. An `[%eval]` has whole centipawns, so no hand-set eval gives
     exactly 65 or 35.
   - F-5 met the same kind of item by setting its threshold parameter to `win_percent(cp)` of a
     fixture eval (`tests/test_presumed_results.py:156`).
   - **Suggestion:** say that the edges are tested that way, or on the band function directly, so
     the item can't be met by a test that never lands on the edge.

5. **non-blocking** — The parameter's validation and the floor are underspecified.
   - "an invalid pair (e.g. lower ≥ upper)" leaves out values outside 0–100 and NaN. It also
     doesn't say whether the check runs up front in `build_site`, as F-5's check does.
   - "at least 10 points, i.e. it is graded at least an inaccuracy" (`ROADMAP.md:216-217`) doesn't
     say whether the floor is a fixed 10 or follows `Thresholds.inaccuracy`. They differ once the
     thresholds are passed in.
   - **Suggestion:** name the valid range, and name which of the two the floor is.

6. **non-blocking** — The note for a moment that is both kinds is unspecified.
   - A swing's note "says that the move changed the expected result" (`ROADMAP.md:220`). The block
     doesn't say whether a 20-point moment that is also a swing gets that wording. There are 362
     such moves in the owner's book.
   - **Suggestion:** one clause in the scope, or leave it to artistic license explicitly.

7. **non-blocking** — The block and the row give different dates for the decisions.
   - The block says the decisions were made "on 2026-09-25" (`ROADMAP.md:251`), and the PR body
     says the same.
   - F-6's row records the kind of moment and the timing as "The owner's choices on 2026-09-24"
     (`ROADMAP.md:18`).
   - **Suggestion:** date each decision.

The owner's merge confirms that the owner made the recorded decisions and chose the mode in
`PLAN.md` row 4; I can't check either from the repository, so neither is a finding. The rule
proposed with this shaping, the 10-point floor, is clearly marked "Proposed with this shaping,
confirmed by the owner's merge".

— Claude Opus 5.5 (claude-opus-5-5), reviewer
Blocking findings remain: 1, 2 and 3.
