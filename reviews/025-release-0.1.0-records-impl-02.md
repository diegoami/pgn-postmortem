# Review 025: the first release's records, F-11 parked, the owner's checks (round 02)

- **Revision covered:** `8460d044cdbc48f61d5540afb96e81f7bf286add` (branch
  `release-0.1.0-records`, pull request #25).
  - After round 01's `46db703`, the branch has two commits:
    - `23005ee`: round 01's record;
    - `8460d04`: "Answer the release-records review, round 01".
- **Target proof:**
  - After `git fetch origin`, `git rev-parse origin/release-0.1.0-records` gives `8460d04…`. This
    equals `headRefOid` from `gh pr view 25 --json headRefOid,files`.
  - `git merge-base origin/main origin/release-0.1.0-records` is `ea4a27b…`, which is still
    `origin/main`.
  - The committed `reviews/025-release-0.1.0-records-impl-01.md` is byte-identical to the file I
    wrote in round 01 (`cmp` reports no difference).
- **Files checked** (6). I got the list two ways and they are the same: `gh pr view 25 --json files`
  and `git diff --name-only ea4a27b..origin/release-0.1.0-records`.
  - `CLAUDE.md`
  - `PLAN.md`
  - `ROADMAP.md`
  - `reviews/018-f8-reading-history-impl-02.md`
  - `reviews/024-fix-board-squares-impl-01.md`
  - `reviews/025-release-0.1.0-records-impl-01.md`
- **How I read them:** `git show origin/release-0.1.0-records:<path>` and `git show 8460d04`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. This is
  the same reviewer session as round 01, continued for the re-review. I have not seen how the change
  was made.
- **Mode:** Claude Code.
- **What `8460d04` touches:** `CLAUDE.md` (the harness bullet), `PLAN.md` (one row label) and
  `ROADMAP.md` (F-1's and F-8's rows, and F-10's variant note). The two review addenda from round
  01 are unchanged.

## The round-01 findings

1. **Scope list (blocking): resolved.**
   - `CLAUDE.md:63-66` now lists F-1.1, F-1.2, F-5, F-6, F-8, F-9 and F-10, and "two defect fixes:
     the file-name date padding (#7, `d90a102`) and the board squares (#24, `3adc85a`)".
   - I checked this against `git log --oneline --merges 7476e54..origin/main` (21 merges).
     - Seven are the listed requests' implementations: #6, #8, #13, #15, #18, #21, #23.
     - Two are the listed fixes: #7 and #24.
     - The other twelve change only records (shapings, queueing, decisions, the mode change). None
       of them touches `pgn_postmortem/` or `scripts/`.
   - Both shas are the merge commits of those PRs.
2. **Claims statement (blocking): resolved.**
   - **Requests:** `CLAUDE.md:66-68` says each request's done-when was fixed when its shaping landed
     and before its work, "except F-6's level band, which the owner changed during F-6's iteration
     (35–65% to 40–60%, recorded in F-6's block)".
     - I listed the roadmap commits between each shaping merge and its implementation merge
       (`git log <shaping>..<impl> -- ROADMAP.md`). There are three:
       - F-6: `dbb228b`, the band change, now named;
       - F-9: `8814cbd`, scope text only, before the done-when heading;
       - F-1.2: `e320079` (licence question 2) and `ebea87c` (the owner's F-1.1 decisions and
         mode).
     - `930dd2e` (#4) only adds "Decided by the owner" lines to F-1's open questions.
     - So F-6 is the only item whose done-when moved during its work, and the exception is stated
       correctly. The band values match F-6's block (recommended default 35–65%, changed to 40–60%).
   - **Defect fixes:** `CLAUDE.md:69-70` says their claims are "the assertion its change landed,
     recorded in `reviews/007-…` and `reviews/024-…`".
     - Review 007's completion names that assertion: output file names zero-pad month and day, with
       new tests red on the unfixed code.
     - Review 024's names `tests/test_boards.py`, failing on the pre-fix code.
     - The text does not claim these were written before the work, which the defect path could not
       give. So the statement is true as written.
3. **Earlier slot sentences (non-blocking): resolved.**
   - "(expected to be `r5`)" and "F-1's first milestone review covers the range" are gone.
   - The bullet now says:
     - the owner's 2026-09-24 plan;
     - that `r5` is tagged (`f22685d`) and not yet adopted;
     - that v0.1.0 "comes earlier than that plan … so it is the first milestone and its review
       covers the range from `7476e54`".
   - Read top to bottom, the bullet no longer contradicts itself. See new finding 1 for one pronoun.
4. **Prompt not pinned (non-blocking): resolved.** The bullet now names "r5's milestone prompt
   (`reviews/milestone-prompt.md` at `r5`)". The orchestrator's check, blob `d260683` at both `r5`
   and `main`, matches the one I made in round 01.
5. **Unrecorded variant claim (non-blocking): resolved.**
   - `ROADMAP.md:635-636` now reads "None of the 148 analyzed games of the owner's book has a
     `Variant` header (checked by the orchestrator on 2026-09-25); the rest of the archive is not
     checked yet."
   - It is attributed and scoped. The owner's book is outside this repository, so I cannot re-run
     that check.
6. **Stale nearby text (non-blocking): resolved.**
   - F-1's row (`ROADMAP.md:13`): "F-1.3 and F-1.4 come after F-8 to F-10 (F-11 is parked) and the
     first release".
   - PLAN's row label (`PLAN.md:45`): "after F-10 and the first release (F-11 is parked)".
   - F-8's row (`ROADMAP.md:20`): "the owner's phone check, deferred to the live book, was done:
     "everythink ok" (2026-09-25)".
   - All three agree with the PLAN sentence at `PLAN.md:49` and with the review 018 addendum.

## Nothing else changed

- `8460d04`'s diff has three hunks in `CLAUDE.md`, `PLAN.md` and `ROADMAP.md`, all described
  above.
- `23005ee` adds only the round-01 record.
- F-10's and F-11's statuses and F-10's block edits are unchanged since round 01.
- The diff has no absolute local path, and no secret or `.env` content.

## Findings

1. **non-blocking**: an unclear pronoun at `CLAUDE.md:57`.
   - The text reads "before F-1's release at the end of F-1.4; that release is now tagged, `r5`".
   - The nearest release is F-1's. The one meant is "the next tagged release of the harness" two
     lines earlier.
   - Suggestion: "that harness release is now tagged". Optional; `r5` and `f22685d` make the meaning
     recoverable.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
