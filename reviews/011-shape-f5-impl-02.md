# Review 011 — shape F-5, round 02

- **Revision covered:** `4c4193640dc167b09cb971f068a2f3c59cc4a54d` (branch `shape-f5`, pull
  request #11). After `git fetch origin`, `git rev-parse origin/shape-f5` equals the pull request's
  `headRefOid`. The merge base with `origin/main` is still `0fd6b4cf7dfb5a544b05b36e7790719e39d29696`.
  The branch has three commits since then: `30b3833` (the shaping, reviewed in round 01), `40bb259`
  (records the round-01 review) and `4c41936` ("Answer the F-5 shaping review, round 01").
- **Files checked:** `PLAN.md`, `ROADMAP.md`, `docs/book-plan.md`,
  `reviews/011-shape-f5-impl-01.md`. The list comes from `gh pr view 11 --json files`. It is
  identical to
  `git diff --name-only $(git merge-base origin/main origin/shape-f5)..origin/shape-f5`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`). This is the same fresh-context Claude Code
  subagent as round 01, continued for the re-review, as `PRINCIPLES.md` allows.
- **Mode:** Claude Code.

What was read:

- **The committed round-01 review.** `reviews/011-shape-f5-impl-01.md` at this revision is
  byte-identical to the reviewer's file (`cmp` reports no difference).
- **The answer commit.** `4c41936` changes only `ROADMAP.md` (F-5's block) and
  `docs/book-plan.md:10-12`. `PLAN.md` is unchanged since round 01.
- **The code.** The new block was read against `pgn_postmortem/site.py` and
  `pgn_postmortem/collection.py`, both unchanged on this branch.
- **The owner's data.** The count over the owner's analyzed book was re-checked read-only. The
  draws are the games whose final White win percentage is 50.0 and 54.9. The weakest win is 88.0,
  and the weakest Black win is 6.7, which is 93.3 for Black. Any threshold above 54.9 and up to
  88.0 therefore gives the same 8 × 1–0, 2 × 0–1 and 2 × ½–½. The new claim "any value from 55% to
  85%" (`ROADMAP.md:183-184`) is accurate. None of the 12 games ends in checkmate or stalemate.
- **The pawn equivalents.** Under `win_percent` (lichess's constant 0.00368208), 70% is about
  +230 cp and 80% about +376 cp, which matches the block's "+2.3" and "+3.8 pawns".

## Round-01 findings

1. **Resolved (blocking 1).** The scope now lists "the end of the moves" among the places a result
   shows. Done-when 1 checks it there too.
2. **Resolved (blocking 2).** The board decides first: checkmate means the mating side wins,
   stalemate means a draw, whether the game is analyzed or not. The presumption follows, and the
   "not recorded" wording comes last. The old out-of-scope item is gone, so scope and out-of-scope
   no longer contradict each other. The order is consistent with the code: for an analyzed
   checkmate, `white_cp` would give the same win anyway (`site.py:128-129`). Done-when 6 tests the
   unanalyzed checkmate and stalemate cases.
3. **Resolved (blocking 3).** The field is now "**Open questions:** none remain". Each of the three
   owner decisions carries its recommended default, its reason and an "Owner decision:" mark.
4. **Resolved (blocking 4).** The tests now bracket the threshold. Done-when 1 has about 72–75%
   giving a win, which fails an implementation at 80%. Done-when 3 has about 65–68% giving a draw,
   which fails one at 60%. Done-when 4 sets the parameter to 80 and expects a draw, which fails an
   implementation that ignores the parameter. Done-when 5 rejects a threshold of 50 or below.
5. **Resolved.** "No bare \*" now applies outside the PGN section.
6. **Mostly resolved.** The fixtures are now synthetic, documented PGNs. Where they live is taken up
   as new finding 3 below.
7. **Partly resolved.**
   - An analyzed game whose final position has no eval now falls to the "not recorded" wording
     (scope step 3).
   - A threshold of 50% or below is rejected. Values from 51 to 59 remain possible; see new
     finding 4.
   - Whether the threshold is also a command-line option is still open. That falls within the
     implementer's latitude.
8. **Resolved.** The fields now follow the block format.
9. **Resolved.** `docs/book-plan.md:10-12` now reads: "The 'Existing spike' section describes the
   `book-poc` branch; F-1.1 reused parts of it." That is accurate. The note about the stale
   eval-trusting text elsewhere in the file was optional and was not taken up, which is fine.

## New findings

1. **blocking** — The out-of-scope list refers to a request that does not exist:
   "- F-6's diagrams." (`ROADMAP.md:170`). There is no F-6 in the queue on this branch or on `main`,
   in any remote branch, or in any pull request (checked with `git grep -n "F-6"` over every remote
   branch, and `gh pr list --state all`). *Out of scope* exists so that deferred work is "recorded
   not lost" (`ROADMAP.md`, *The block*). A reference to an unrecorded request loses it, and an
   implementer cannot tell what is excluded. Fix this in the same change, in one of two ways:
   - add the F-6 row to the queue with the owner's wording verbatim, as F-4 was queued;
   - or replace the reference with a description of the deferred work (for example "diagrams of
     …, not yet requested").

2. **non-blocking** — Two cases the scope states have no check.
   - **A mate eval in the final position.** The scope says "a forced mate counts as 100%"
     (`ROADMAP.md:136`), but the round-01 done-when on a forced mate was dropped, and no remaining
     item has a final `[%eval #N]`. Two of the owner's 12 games end that way (`#-9` and `#-3` from
     the side to move's view). An implementation that read only centipawn evals would treat them as
     having no eval and print "not recorded", and every listed test would still pass. Suggest adding
     "one ending at a final `[%eval #N]` (not on the board) shows the mating side's win".
   - **Black's side of the draw band.** Done-when 2 (about 25–28% for White gives 0–1) and
     done-when 3 (about 65–68% gives a draw) do not include a case at about 32–35% for White, which
     should be a draw. An asymmetric rule, such as "White below 40% means Black wins", would pass.
     Suggest one mirrored draw case.

3. **non-blocking** — The block does not say where the synthetic fixtures go. They are to be "small
   synthetic PGNs that carry the library's analysis marker header and hand-set `[%eval]` comments"
   and are "documented as synthetic" (`ROADMAP.md:147-149`). The slot lists
   `tests/fixtures/site/analyzed/**` as generated output, "written once by
   `pgn-postmortem analyze`", never edited by hand (`CLAUDE.md:73-74`). That directory is also the
   golden test's input. Suggest either:
   - saying the synthetic fixtures live elsewhere (a separate directory, or built in the tests);
   - or updating the slot's list of generated paths in the same implementation change, if they are
     to join the golden site.

4. **non-blocking** — Two edge cases remain.
   - **Thresholds from 51% to 59%.** These are accepted. Under such a threshold, a presumed winner
     with less than 60% makes the conclusion say "the result came from outside the position on the
     board: a resignation, the clock or an adjudication" (`site.py:664-671`), which is false for a
     result presumed from that very position. Either raise the lower bound to 60 or have the
     implementation word presumed results differently. The owner's default of 70 is not affected.
   - **Insufficient material.** The board rule covers checkmate and stalemate only. An unanalyzed
     "\*" game that ends with bare kings would say "not recorded", while the conclusion already
     calls that position one with "too little material left on the board for a mate"
     (`site.py:649-650`). Suggest adding insufficient material as a draw decided by the board, or
     leaving it out of scope explicitly.

Nothing else changed beyond what the answer commit states. The PLAN.md renumbering and the queue row
are as reviewed in round 01 and remain consistent.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
A blocking finding remains: new finding 1 (the dangling "F-6's diagrams" reference).
