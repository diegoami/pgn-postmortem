# Review 025: the first release's records, F-11 parked, the owner's checks (round 01)

- **Revision covered:** `46db7038a28b58618b5adfe7697f7fd8b708b8d0` (branch
  `release-0.1.0-records`, pull request #25, one commit `46db703`).
- **Target proof:**
  - After `git fetch origin`, `git rev-parse origin/release-0.1.0-records` gives `46db703…`. This
    equals `headRefOid` from `gh pr view 25 --json headRefOid,files`.
  - `git merge-base origin/main origin/release-0.1.0-records` is
    `ea4a27bfe18b7800bae546d649a0adf9f299b71d`, which is also `origin/main`.
- **Files checked** (5). I got the list two ways and they are the same: `gh pr view 25 --json files`
  and `git diff --name-only ea4a27b..origin/release-0.1.0-records`.
  - `CLAUDE.md`
  - `PLAN.md`
  - `ROADMAP.md`
  - `reviews/018-f8-reading-history-impl-02.md`
  - `reviews/024-fix-board-squares-impl-01.md`
- **How I read them:** `git show origin/release-0.1.0-records:<path>` and `git show 46db703`. I did
  not check out the branch.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. I have
  not seen how the change was made. I treated the PR body and the commit message as claims to check.
- **Mode:** Claude Code.
- **Out of my reach:** the repository cannot show that the owner said or decided what is recorded.
  The owner's merge is that check, so it is not a finding.

## What I checked and found correct

- **Statuses.**
  - F-10 is `landed`, "Landed in #23 (`f3b4dea`), 2026-09-25". `f3b4dea` is "Merge pull request #23
    from diegoami/iteration-7-lichess-links" on `main`.
  - F-11 is `parked`, with the owner named, dated and quoted ("let us postpone F-11"), and a reason.
  - Both words are in the roadmap's vocabulary (`ROADMAP.md`, *Statuses*: "`parked` and `refused`.
    … **Only the owner parks or refuses**, and the reason is recorded").
- **F-10's block against review 023's completion note.**
  - Finding 1: the note says "set-up games are decided by the starting board, which is accepted.
    F-10's plan text gets aligned in a later record change". The edited scope bullet says exactly
    that, and cites the owner, the date and the finding.
  - Finding 2: the note says the variant gap "goes into the roadmap as a note for later". A "Note for
    later" is added under *Out of scope*. See finding 5 for one sentence beyond this.
  - Finding 3 ("stays as it is"): nothing is edited, which is right.
  - Done-when 2 keeps "(a `FEN` header)". That is right: it describes the fixture's game, which has
    a real set-up `FEN`, and a release's claims must not move after the work.
  - Nothing else in the block changed: the diff has two hunks in the block.
- **The model that implemented none of the range.**
  - Every one of the 144 non-merge commits in `7476e54..origin/main` carries
    `Co-Authored-By: Claude Opus 5.5`. The 21 commits without a trailer are GitHub merge commits.
  - Every signed review verdict on `main` is "— Claude Opus 5.5 (claude-opus-5-5), reviewer" (46).
  - No record names another family as a builder. DeepSeek, through OpenCode, is another family. I
    cannot check that the id `opencode/deepseek-v4-pro` exists; the owner's run will show it.
- **r5 and the prompt.** `harness_template` has tagged `r5` (`f22685d`). Its `PRINCIPLES.md`
  names `reviews/milestone-prompt.md` and ends a milestone verdict with `AGREE` or `BLOCK`. So "the
  tag waits for that review's AGREE" matches the rule being borrowed. Claude mode's "no AGREE/BLOCK
  marker" applies to change reviews, not to this milestone review.
- **The addenda.**
  - Both come after the completion note's signature, and are labelled "addendum", dated, quoted
    verbatim ("everythink ok") and marked "Transcribed by the orchestrator".
  - They change no done-when, assertion, owner decision or process rule.
  - Each closes a check the note itself left open ("The owner's phone check is deferred to the live
    book"). They are non-material transcriptions.
- **PLAN's sentence** agrees with the earlier decision in the same paragraph (F-8 to F-11 before
  F-1.3). With F-11 parked, F-10 is the last of them.
- **Nothing else changed:** five files, all Markdown. There is no absolute local path, and no secret
  or `.env` content in the diff.

## Findings

1. **blocking**: the release's scope in `CLAUDE.md` leaves out one landed code change in its range.
   - `CLAUDE.md:63-64` says v0.1.0 "lands F-1.1, F-1.2, F-5, F-6, F-8, F-9, F-10 and the
     board-squares defect fix (#24)".
   - `git log --merges 7476e54..origin/main` also has `d90a102`, "Merge pull request #7 from
     diegoami/fix-filename-date-padding". It changes `pgn_postmortem/analysis.py`,
     `pgn_postmortem/collection.py` and two test files.
   - It is a defect-path fix (review 006 round 03, finding 14; `reviews/007-…`), the same kind of
     change as #24, which the list names.
   - The other merges in the range only record things (shapings, queueing, decisions).
   - A release review over the range will meet #7's code with no claim listed for it.
   - Fix: add "the file-name date padding fix (#7)" to the list.
2. **blocking**: "each fixed when its shaping landed and before its work" (`CLAUDE.md:64-65`) is not
   true of every item.
   - **F-6:** its done-when changed during its iteration. Commit `dbb228b`, "Record the owner's
     change of F-6's level band to 40-60%", is on PR #15's branch. It changes the done-when's
     thresholds ("White winning at 65%" → "60%", "can't hit 65.000%" → "60.000%") and the owner's
     check (15. Nxc5 added).
     - F-6's block says so itself: the owner's choice was "changed the same day after checking the
       preview of the book built from this iteration's branch (pull request #15)".
     - It is a recorded owner decision and legitimate. But F-6's claims were not fixed before its
       work.
   - **#7 and #24:** neither has a done-when in `ROADMAP.md` (review 024's note: "no roadmap line
     for the defect, which this record covers"). The sentence "those requests' done-when items"
     gives them no claims.
   - The other in-branch roadmap edits leave done-when items alone:
     - `8814cbd` on #21 touches F-9's scope text only;
     - `e320079` on #8 adds to F-1's licence question.
   - The claims statement is what the release reviewer checks against, so it has to be accurate.
   - Fix: say that F-6's band was changed by the owner during its iteration (`dbb228b`, recorded in
     F-6's block). Also say where the two fixes' claims are: their review records, 007 and 024,
     each with the defect and the assertion that would have caught it.
3. **non-blocking**: the new text sits next to earlier sentences in the same bullet that it now
   partly overrides.
   - `CLAUDE.md:55-57` still says the milestone rules are "adopted as its own reviewed change before
     F-1's first release at the end of F-1.4".
   - `CLAUDE.md:61` still says "F-1's first milestone review covers the range from that commit".
   - The new lines 62-69 make v0.1.0, before F-1.4 and before r5, the review over that same range.
   - A careful reader can reconcile them: "F-1's first release" would be the one that completes
     F-1, and the review from `7476e54` becomes v0.1.0's. A later session may not.
   - The line "(expected to be `r5`)" is also now past: `r5` is tagged (`f22685d`).
   - Suggestion: reword lines 57 and 61 to "the release that completes F-1 (after F-1.4)" and "the
     first milestone review (v0.1.0's)".
4. **non-blocking**: the prompt is not pinned. "`harness_template` main's milestone prompt as the
   fixed prompt" (`CLAUDE.md:68`) points at a moving branch.
   - `main` is 44 commits past `r5` (`gh api …/compare/r5...main`).
   - `reviews/milestone-prompt.md` is not among the changed files, so today the prompt is the same
     at `r5` and on `main`.
   - Suggestion: name `r5` (`f22685d`) or a commit, so the prompt stays fixed if `main` changes
     before the review runs.
5. **non-blocking**: `ROADMAP.md:635` adds a claim that is not in the recorded decision.
   - The sentence is "None of the owner's games is a variant."
   - Review 023's completion note records only that the variant gap "goes into the roadmap as a note
     for later".
   - The owner's archive is not in this repository, so I cannot check the claim.
   - Suggestion: attribute it (the owner's words, dated) or drop it.
6. **non-blocking**: nearby text now reads stale. Optional to align here.
   - `ROADMAP.md:13`, F-1's row: "F-1.3 and F-1.4 come after F-8 to F-11".
   - `PLAN.md:45`, the row label "after F-8 to F-11". The new sentence at `PLAN.md:49` explains the
     change.
   - `ROADMAP.md:20`, F-8's row: "the owner's phone check was deferred to the live book". The
     addendum in review 018 now records that check as done.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
Blocking findings remain: 1 and 2.
