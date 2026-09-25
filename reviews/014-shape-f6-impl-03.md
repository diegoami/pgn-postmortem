# Review 014 — shape F-6, round 03

- **Revision covered:** `9256c7e2672c38d9232201a70f6a0c4c341ce6d1` (branch `shape-f6`, pull request #14).
- **Target proof:**
  - After `git fetch origin`, `git rev-parse origin/shape-f6` gives
    `9256c7e2672c38d9232201a70f6a0c4c341ce6d1`, which equals `headRefOid` from
    `gh pr view 14 --json headRefOid,files`.
  - The merge base with `origin/main` is `origin/main` itself (`2330744`).
  - Round 02's target `e77932b` is followed by two commits: `be2b6aa` (records round 02) and
    `9256c7e` ("Answer the F-6 shaping review, round 02").
- **Files checked:** `PLAN.md`, `ROADMAP.md`, `reviews/014-shape-f6-impl-01.md` and
  `reviews/014-shape-f6-impl-02.md`.
  - The PR's `files` list and `git diff --name-only origin/main...origin/shape-f6` agree.
  - Both committed review files are byte-identical to the files I wrote (`cmp`).
  - This round's change, `git diff e77932b origin/shape-f6`, touches only condition 2, condition 3
    and item 5 of F-6's block, plus the round-02 record. Everything was read at `origin/shape-f6`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent.
- **Mode:** Claude Code.

## What I checked

- **The new reading rule against `pgn_postmortem/analysis.py`.** The file is the same on `main` and
  on the branch. The relevant code is `analyze_game`, lines 164-201, and `attach_line`, lines
  128-142. I checked each case:
  - **A flagged move with its own better line.** The code attaches `pv_before` off the parent only
    when `pv_before[0] != move`. The line's first move is the engine's first choice and differs from
    the move played, so the move is included. This is correct.
  - **A move after a flagged move whose refutation is stored.** The refutation is the `pv` of the
    search after the previous move, and that same `pv` becomes `pv_before` for this move. It is
    attached off the same node once this move's node exists. Its first move is therefore this
    position's first choice. The move is included when that differs from the move played, and
    excluded when it is the move played. This is correct. When both lines are stored they are the
    same PV, so "the first move of **any** line" is well defined.
  - **No line at all.** A graded move whose parent has no line means either `pv_before[0]` was the
    move played, or the engine returned an empty PV. Either way there is no better move to show, so
    the move is left out. This is correct under the thresholds the analysis used (see finding 1).
  - `attach_line` stops at the first illegal move, but the first move of a PV is always legal. The
    refutation dropped after the game's last move is at the final position, which is never "the
    position before" a move.
- **The rule applied literally.** I applied condition 3 as written, with the floor at
  `LICHESS_THRESHOLDS.inaccuracy` (10) and the bands at 35/65. I used the library's `review_moves`,
  read-only and without Stockfish, on the 148 analyzed files in the workspace
  `chessgamescollection`, `book/analyzed/`. The test is: the first moves of all lines stored off the
  parent; excluded if there are none or if they include the move played.
  - **It gives 236 new questions in 96 games.** The 3 excluded moves are the ones the block names:
    45… Qa6 (ply 90) and 47… Qa6 (ply 94) in `2005-09-24-3bd9df323c`, and 18. Qxd4 (ply 35) in
    `2008-01-05-ec4df50311`. All three have the refutation-only shape.
  - **The shapes of the 239 candidates:** 171 have only their own better line, 65 have their own
    line and the previous move's refutation, 3 have only the refutation, and 0 have no line.
  - The two wordings of item 5 cover the last two shapes, which a wrong implementation could
    mishandle.
- **The floor and `build_site`'s `thresholds`.** `build_site(thresholds=…)` passes the thresholds
  to `review_moves`, which grades with `classify(loss, thresholds)`.
  - `classify` returns a grade whenever `loss >= thresholds.inaccuracy` (`analysis.py:105`).
  - A floor equal to `thresholds.inaccuracy` therefore makes every swing a graded move, so
    `GRADES[review.grade]` in `moment_html` and `note_text` always has an entry.
  - Under the defaults the floor is 10, as before. The rule fits the parameter and adds none.
- **The rest.**
  - Items 1, 3 and 4 still say "10" and "10–20". That is right under the default thresholds, which
    are what the fixtures use.
  - The owner decision "Proposed with this shaping" still reads "at least 10 points (the inaccuracy
    threshold)", which is consistent.
  - The PR body's "at least 10 points" and "236 questions in 96 games" match. It uses no gendered
    pronouns.

## Round-02 findings

1. **Resolved.**
   - Condition 3 says how the first choice is read: the first move of any line stored at the
     position.
   - It says why "a line is stored" is not the test.
   - Item 5 now requires both the no-line fixture and the refutation-only fixture.
2. **Resolved.** The floor follows `thresholds.inaccuracy`, so a swing is never ungraded.

## Findings

1. **non-blocking** — "If no line is stored there, the move played was the first choice" holds only
   when the site's thresholds are the ones the analysis used.
   - `analyze_games` has its own `thresholds` parameter (`analysis.py:218`), and it decides which
     moves get lines.
   - If a caller builds the site with a lower inaccuracy threshold than the analysis used, a swing
     between the two thresholds has no line of its own.
     - When the previous move's refutation is stored, it is still read correctly.
     - When it isn't, the move is left out, and not because the engine chose it.
   - The outcome is safe: no question is ever asked without a better move to show. Only the stated
     reason is overstated, and the default thresholds are unaffected.
   - **Suggestion (optional):** "…the move played was the first choice, or (with thresholds lower
     than the analysis used) nothing is known about it; either way it is not a moment."

No blocking finding remains. The block's scope, conditions and done-when items can be implemented
and tested as written. The counts reproduce on the owner's files, and every round-01 and round-02
finding is resolved.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking findings remain.
