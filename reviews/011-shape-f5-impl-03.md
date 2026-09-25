# Review 011 — shape F-5, round 03

- **Revision covered:** `26a8831fbc05a42c4cbbb8818a94e41a3cccd8f3` (branch `shape-f5`, pull
  request #11).
  - After `git fetch origin`, `git rev-parse origin/shape-f5` equals the pull request's
    `headRefOid`.
  - The merge base with `origin/main` is still `0fd6b4cf7dfb5a544b05b36e7790719e39d29696`.
  - Since round 02 (`4c41936`) there are three commits:
    - `13bc98f` records the round-02 review;
    - `13b0eb5` is "Answer the F-5 shaping review, round 02";
    - `26a8831` is "Renumber F-5's done-when list".
- **Files checked:** `PLAN.md`, `ROADMAP.md`, `docs/book-plan.md`,
  `reviews/011-shape-f5-impl-01.md`, `reviews/011-shape-f5-impl-02.md`. The list comes from
  `gh pr view 11 --json files`. It is identical to
  `git diff --name-only $(git merge-base origin/main origin/shape-f5)..origin/shape-f5`.
  - Since round 02, only `ROADMAP.md` and `reviews/011-shape-f5-impl-02.md` changed
    (`git diff 4c41936 26a8831 --stat`).
  - `PLAN.md` and `docs/book-plan.md` are as reviewed before.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`). This is the same fresh-context Claude Code
  subagent as rounds 01 and 02, continued for the re-review.
- **Mode:** Claude Code.

What was checked:

- **The committed review files.** Both are byte-identical to the reviewer's files (`cmp`, no
  difference): `reviews/011-shape-f5-impl-01.md` and `reviews/011-shape-f5-impl-02.md`.
- **F-5's block.** It was read at this revision against `pgn_postmortem/site.py`, which is
  unchanged on this branch.
- **F-6's example numbers.** They were checked read-only with python-chess and the library's own
  `site.review_moves`, on the owner's analyzed game `2008-01-04-4e5d4e182f.pgn`.

## Round-02 findings

1. **Resolved (blocking).** F-6 is now a queue row (`ROADMAP.md:18`). F-5's out-of-scope list now
   names what it defers: "diagrams for moves that changed the expected result, which is F-6". The
   row follows *How to request*:
   - its status is `requested` and its iteration cell is empty;
   - its notes say "Not shaped yet; it is shaped after F-5's shaping lands";
   - there is no block for it under *Accepted requests*.

   The quoted wording and the owner's two choices cannot be verified from the repository; the
   owner's merge is that check.

   The example figures in the notes are accurate against the analyzed game:
   - 31... Qa2 is the only move that loses 20 points or more (White 3.4% → 31.5%, a loss of 28.1),
     graded a mistake, "?";
   - 37... Rg2+ takes White from 25.0% to 41.3%, a loss of 16.4 for Black;
   - 40. Ra4 takes White from 48.8% to 31.8%, a loss of 17.0;
   - both are graded inaccuracies, so neither gets a diagram.

   One detail of the label is not from the game's record; see new finding 1.

2. **Resolved (non-blocking).** Both missing checks now exist:
   - done-when 7 covers a final mate-score eval (`[%eval #N]`, not checkmate on the board), and
     scope step 2 now names mate scores;
   - done-when 2 adds the draw case on Black's side (about 32–35% for White gives ½–½).
3. **Resolved (non-blocking).** The synthetic fixtures get their own directory,
   `tests/fixtures/site/synthetic/`, which is documented as hand-written and stated not to be under
   the generated `tests/fixtures/site/analyzed/`. The slot's rule about generated output is kept.
4. **Resolved (non-blocking).**
   - Insufficient material is now decided by the board as a draw (scope step 1 and done-when 6).
     This is consistent with the conclusion's existing wording (`site.py:649-650`).
   - The threshold is bounded to 55–95%, with anything else rejected (done-when 5).
   - The scope requires that the conclusion never describe a presumed win as having "come from
     outside the position". See new finding 2 for the one part without a check.

The done-when list is numbered 1–10 with no gaps. Each item can be run on the synthetic fixtures,
and together they would catch:
- a threshold other than 70 (items 1 and 3);
- a parameter that is not used (item 4);
- an asymmetric draw band (item 2);
- mate scores that are not read (item 7);
- a place that is missing a result (item 1 names all five);
- a game whose board decides the result being presumed from its analysis instead (item 6);
- a stray "\*" (item 8);
- a changed identity (item 9);
- the plural defect (item 10).

The "55% to 85%" claim in the owner decisions (`ROADMAP.md`, F-5, *Open questions*) still holds.
The round-02 count found that any threshold above 54.9% and up to 88.0% gives the same results for
the owner's 12 games. It also agrees with the new lower bound of 55%.

## New findings

1. **non-blocking** — F-6's notes label the example game "(Pedroni vs. Amicabile, Verona 2008)"
   (`ROADMAP.md:18`), but the game's headers say `[Event "Saxonia Systems AG"]` and
   `[Site "Saxonia Systems AG"]`. The analyzed file and the workspace's source copy
   `book/games/2008-01-04-4e5d4e182f.pgn` agree on this. "Verona" appears only in the Event of a
   neighbouring game (`2008-01-06`, "Festival Verona 2008"). The owner's URL and its id
   `4e5d4e182f` identify the game without ambiguity, so nothing is misdirected. Still, the label is
   an inference presented as the game's record. Suggest "(Pedroni vs. Amicabile, 4 January 2008)",
   or keep "Verona" only if the owner confirms it.

2. **non-blocking** — The scope rule "a presumed win is never described as a result that 'came from
   outside the position'" has no done-when item. With the default threshold of 70% it cannot
   trigger, because the conclusion only uses that wording below 60% (`site.py:664-671`). It can
   trigger only with the threshold set between 55 and 59 and a final position in that band. One
   more assertion would pin it: threshold 55, a game ending at about 57% for White, a conclusion
   without "outside the position". It is optional; the gap concerns a setting other than the
   owner's.

3. **non-blocking** — The iteration table in `PLAN.md` and the F-1 row still give F-1.3 iteration 4
   (`PLAN.md:41`; `ROADMAP.md:13`, "1, 2, 4, 5"). F-6's row records the owner's choice to land it
   "Right after F-5, before F-1.3". Nothing goes wrong before F-6 is shaped: the next iteration
   after this merge is 3 (F-5), which is correct, and F-6's own shaping is where the table would
   be renumbered, as this change did for F-5. Suggest a short note in F-6's row that its shaping
   renumbers F-1.3 and F-1.4 in `PLAN.md` and in the F-1 row, so the two files are not read as
   disagreeing meanwhile.

Nothing else changed. There is no code, test or golden-file change. `PLAN.md` and
`docs/book-plan.md` are unchanged since round 02.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged by the owner on 2026-09-25 as `bd31f14` (pull request #11); the clean round, 03, covers `26a8831`. CI on the merge commit passed: https://github.com/diegoami/pgn-postmortem/actions/runs/36109410453.

- **F-5's block has every field of the block format,** with the original request verbatim and the owner decisions each with a recommended default and reason. Checked in rounds 01–03.
- **The iteration table stays consistent:** F-5 is iteration 3, and F-1.3 and F-1.4 move to 4 and 5.
- **Only `ROADMAP.md`, `PLAN.md` and `docs/book-plan.md` changed,** plus the review records. Round 02 also queued **F-6** as a `requested` row, with the owner's wording.

Left for F-6's shaping: round-03 findings 1 (F-6's note calls the example game "Verona 2008" while its source header then said "Saxonia Systems AG"; the source was since corrected in DA_chessgames `9e7c939`, Event "Festival Verona 2008", Site "Verona", so the note is now accurate), 2 (the "outside the position" wording rule has no test; it only triggers with thresholds of 55–59%) and 3 (shaping F-6 renumbers F-1.3 and F-1.4 again).

— Implementer, Claude Opus 5.5 (claude-opus-5-5)
