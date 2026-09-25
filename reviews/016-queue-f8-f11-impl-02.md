# Review 016 — queue F-8 to F-11, implementation, round 02

- **Revision covered:** `dedbcad7ea860e93dcd9911ce1344b6d829eb6cb` (branch `queue-f8-f11`, pull
  request #16). After `git fetch origin`, `git rev-parse origin/queue-f8-f11` equals the pull
  request's `headRefOid`. The commits since round 01 are `cc6e392` (the round-01 record) and
  `dedbcad` (the answer to it, and the owner's order).
- **Files checked:** `PLAN.md`, `ROADMAP.md`, `reviews/016-queue-f8-f11-impl-01.md`. Obtained from
  the pull request's files (`gh pr view 16 --json files`) and checked against the local diff from
  the merge base (`git diff --name-only $(git merge-base origin/main origin/queue-f8-f11)..origin/queue-f8-f11`,
  merge base `aa054d7`). The two lists match. Changes since round 01 were read with
  `git diff ec8f14d dedbcad`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that
  did not see the change being written. It is the same reviewer as round 01.
- **Mode:** Claude Code.

## What was checked

- **The round-01 record is committed unchanged.** `reviews/016-queue-f8-f11-impl-01.md` at
  `cc6e392` is byte-identical to the file the reviewer wrote (checked with `cmp`).
- **The owner's wording is untouched.** The id and request cells of every row are identical at
  `ec8f14d` and `dedbcad`, compared cell by cell. Only the status and notes cells changed: F-6's,
  and F-8's to F-11's.
- **Row form.** Every row still has five cells, counted by splitting on `|`. There is no `|` inside
  any cell. F-8 to F-11 are still `requested`, with an empty iteration cell, and each still says
  "Not shaped yet". None of them has a block, a scope or done-when items.
- **The owner's decisions are recorded, not invented.** Each of F-8 to F-11 records the order ("the
  owner decided on 2026-09-25 that F-8 to F-11 come before F-1.3"). F-10 records the choice of a
  link to lichess's analysis board, by FEN. The record gives the reason it was recommended as the
  default (no JavaScript, no bundled engine, no licence question), what it costs (the network and a
  third-party site), and the alternative not chosen, with that alternative's costs. The
  repository cannot show that the owner decided these; the owner's merge is that check. The F-10
  decision fixes the owner-level choice only. How the link looks and whether it opens a new tab
  are still left for shaping, which fits *Artistic license*.
- **F-6's status.** It now reads `landed`, with "Landed in #15 (`378dd9c`), 2026-09-25".
  `378dd9c` is "Merge pull request #15 from diegoami/iteration-4-outcome-swings", so the row
  names the merge commit, as F-5's row does (`88ebc62`, the merge of #13). The addition "with the
  owner's band change to 40–60%" matches `dbb228b`.
- **PLAN.md.** The added paragraph records the order and says that F-8 to F-11 get their
  iteration numbers when they are shaped, with F-1.3 and F-1.4 moving after them. That fits
  iteration 7+ ("the first unblocked roadmap request, in the owner's order") and the table's
  "a plan, not a contract". See finding 2.

## The round-01 findings

1. **JavaScript and the EPUB: resolved.** F-8 and F-11 now say that each would bring JavaScript
   into the site and that the EPUB would not carry it. F-10's decided option needs no script, and
   its rejected option is listed with "JavaScript" among its costs.
2. **`file://` and rebuilds: resolved.** F-8 now says that browser storage for `file://` pages
   differs between browsers. F-11 now says that storage survives a rebuild and that the risk is a
   renamed page when a game's id changes (a corrected `Date` or `Result`, see F-7). That agrees
   with F-7's own note.
3. **The "no hosting" citation: resolved.** It is gone. What replaced it has a small citation
   problem of its own (finding 1 below).
4. **F-6's status: resolved.** See above.

## Findings

1. **non-blocking — F-8 credits "no JavaScript by design" to "F-1's scope, `docs/book-plan.md`",
   but neither says anything about JavaScript.** Both say the site needs no server and works
   offline and from `file://` (ROADMAP F-1 *Scope*; `docs/book-plan.md` *Output*: "no server
   needed"). A search for `javascript`, ignoring case, over `ROADMAP.md`, `PLAN.md`, `docs/` and
   `README.md` at this revision finds only `README.md:194` ("there is no JavaScript") and the new
   notes themselves. The code says the same at `pgn_postmortem/site.py:13`. So the fact is true,
   but the source given for it is wrong. Suggested: "no server (F-1's scope, `docs/book-plan.md`)
   and no JavaScript (`README.md`, *The site*)". Or leave it: the statement is correct.
2. **non-blocking — the iteration table and F-1's row still show F-1.3 and F-1.4 as iterations 5
   and 6.** PLAN.md's table still has rows 5 and 6 for F-1.3 and F-1.4, whose out-of-scope cells
   do not list F-8 to F-11. F-1's row in `ROADMAP.md` still reads "1, 2, 5, 6 (F-1.1 to
   F-1.4 …)". The new paragraph under the table explains that these numbers will move, so the
   records do not contradict each other. But someone who reads only the table, or only F-1's row,
   sees F-1.3 as next. Suggested: a short pointer in rows 5 and 6, or in F-1's iteration cell
   (for example "moves after F-8 to F-11, owner 2026-09-25"). Renumbering can also wait until
   F-8 is shaped, as the paragraph says.

Nothing else changed beyond what the commit message lists.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged by the owner on 2026-09-25 as `db15a62` (pull request #16); the clean round, 02, covers `dedbcad`. CI on the merge commit passed: https://github.com/diegoami/pgn-postmortem/actions/runs/36133368719.

- **F-8 to F-11 are queued** with the owner's verbatim wording and status `requested`, and are not shaped. The notes carry the constraints for shaping.
- **The owner's decisions are recorded:**
  - F-8 to F-11 come before F-1.3, in the rows and in `PLAN.md`.
  - F-10 is a link to lichess's analysis board, with its default, reason and the alternative not chosen.
- **F-6 is marked `landed`** (#15, `378dd9c`).
- **Only `ROADMAP.md` and `PLAN.md` changed,** plus the review records.

Left for F-8's shaping: round-02 findings 1 (the source of "no JavaScript by design" is `README.md` and `site.py`, not F-1's scope) and 2 (pointers in the iteration table and F-1's row to the new order).

— Implementer, Claude Opus 5.5 (claude-opus-5-5)
