# Review 014 — shape F-6, round 02

- **Revision covered:** `e77932b09069983e2b7d09eafe6c550e286b69f1` (branch `shape-f6`, pull request #14).
- **Target proof:** after `git fetch origin`, `git rev-parse origin/shape-f6` gives
  `e77932b09069983e2b7d09eafe6c550e286b69f1`, which equals `headRefOid` from
  `gh pr view 14 --json headRefOid,files`. The merge base with `origin/main` is `2330744`, which is
  `origin/main` itself. There are three commits on top of it: `a30d861` (round 01's target), `b26dc86`
  (records round 01) and `e77932b` ("Answer the F-6 shaping review, round 01").
- **Files checked:** `PLAN.md`, `ROADMAP.md` and `reviews/014-shape-f6-impl-01.md`. The PR's `files`
  list and `git diff --name-only $(git merge-base origin/main origin/shape-f6)..origin/shape-f6`
  agree. The committed round-01 review is byte-identical to the file I wrote (`cmp` gives no
  difference). Everything was read at `origin/shape-f6`, and the round's change with
  `git diff a30d861 origin/shape-f6`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent.
- **Mode:** Claude Code.

## What I checked

- **The recount.** `pgn_postmortem/` is the same on the branch as in the working tree. I used the
  library's own `review_moves` and `engine_line`, read-only and without Stockfish, on the 148
  analyzed files in the workspace `chessgamescollection`, `book/analyzed/`. I applied all three
  conditions, reading condition 3 as the site already does: the first stored line off the position
  before differs from the move played.
  - **The counts hold:** 390 critical moments, 239 candidate swings that are not already critical
    moments, **236 new questions in 96 games**, and 362 swings that are already critical moments.
  - **Three candidates are excluded**, all exactly as the block names them:
    - 45… Qa6 and 47… Qa6 in `2005-09-24-3bd9df323c`;
    - 18. Qxd4 in `2008-01-05-ec4df50311`. **The implementer is right that this is White's 18th
      move.** It is ply 35, so my round-01 citation "18… Qxd4" was wrong.
  - No position had its band edge hit exactly (0 of 239 candidates).
- **Condition 3 can be read from the stored analysis for every flagged move.** Here is why, from
  `pgn_postmortem/analysis.py` (`analyze_game`, lines 164-201):
  - The refutation of move N is the principal variation (PV) of the search after move N. That same
    search also gives `pv_before` for move N+1.
  - Both lines hang off node N.
  - So every alternative line stored off a position starts with the engine's first choice there,
    whichever of the two it is. On the owner's data, no node has alternative lines that disagree on
    their first move (0).
  - A graded move with no alternative line stored off the position before is one whose first choice
    was the move played. Every one of the 239 candidates has at least one line stored there.

  This matters because all three excluded moves have exactly one alternative line, and it is **the
  previous move's refutation, starting with the move played**. That is the case this round's note
  asked about. See finding 1.
- **The lead.** `site.py:575` on `main` says "…where a single move cost at least {mistake} points of
  winning chances". The block quotes "cost at least 20 points" from it accurately. The required new
  wording, "cost at least 20 points or changed the expected result", is true for both kinds of
  moment. The "no critical moment" branch (`site.py:580`) stays true under F-6.
- **The owner decisions and the PR body.**
  - Every owner decision now has its recommended default, a reason and the owner's choice, each
    dated.
  - F-6's row (2026-09-24: which moments, and when) agrees with the block (the band on 2026-09-25).
  - The PR body gives 236 in 96 games, names the three exclusions and withdraws the "engine line"
    claim. It uses no gendered pronouns for the owner.
  - `PLAN.md` rows 4–7+ haven't changed since round 01.

## Round-01 findings

1. **Resolved.** The false claim is gone. Condition 3 excludes the three cases and gives its reason,
   and the refutation is stated as present only "when the analysis has one".
2. **Resolved.**
   - The scope now requires the infobox and lead counts, and fixes the lead's wording.
   - The conclusion is dropped from the "counts in" sentence.
   - Item 8 tests the counts and the wording.
3. **Resolved.** The first decision now says why its default was recommended.
4. **Resolved.** Item 7 tests the edges by setting the parameter to a fixture's exact value.
5. **Resolved.**
   - The valid range is stated: finite; lower in (0, 50); upper in (50, 100).
   - The check runs up front, even for an empty collection.
   - The floor is a fixed 10.
6. **Resolved.** A 20-point moment that is also a swing gets the changed-result note (scope; item 6).
7. **Resolved.** Each decision is dated, and the row agrees.

## Findings

1. **blocking** — Item 5 can be met by an implementation that gets all three of the owner's real
   exclusions wrong.
   - **What the block says:** condition 3 states the rule ("the engine's first choice in the
     position before differs from the move played"). It doesn't say how the first choice is read
     from the stored analysis.
   - **The wrong implementation:** an obvious reading is "a better line is stored off the position
     before". That rule includes all 239 candidates, because each of the three excluded moves has a
     line stored there: the previous move's refutation, which starts with the move played.
   - **Why item 5 doesn't catch it:** item 5 ("a 10–20-point band change whose move was the engine's
     first choice is not a moment") can be met with a fixture that has no line at all off that
     position, and that fixture passes under the wrong rule.
   - **Why it matters:** the result would be the three "What would you play?" questions with no
     better move that round 01 found. The owner's verdict check covers only the Verona game.
   - **Fix:** add one sentence to condition 3. The first choice is the first move of any engine line
     stored off the position before, since the previous move's refutation and this move's better
     line come from the same search. When no line is stored, the move played was the first choice.
     Also make item 5 cover the shape found in the owner's book: a fixture whose only line off that
     position is the previous (graded) move's refutation, starting with the move played. A second
     fixture with no line there is optional.

2. **non-blocking** — The fixed 10-point floor and `build_site`'s `thresholds` parameter can
   disagree.
   - **The code:** `build_site` and `review_moves` take `thresholds` (`site.py:150, 969`), and a
     move's grade comes from `classify(loss, thresholds)`.
   - **The problem:** a caller could pass an inaccuracy threshold above 10. A swing costing between
     10 and that threshold would then be a moment with `grade` None. Today's `moment_html` and
     `note_text` index `GRADES[review.grade]`, which has no None entry. The block doesn't say what
     such a moment's note or answer says.
   - **Suggestion:** either take the floor as `thresholds.inaccuracy`, which is 10 under the decided
     grading and adds no new parameter, or state that a swing's note doesn't depend on its grade.
     Under the defaults nothing changes.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
Blocking findings remain: 1.
