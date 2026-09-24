# Review 005 — F-1.1 in Claude Code mode, and the milestone-review plan (round 01)

- **Revision covered:** `89ef79369e78345c53dae80d0f291a9e11af0dcf` (branch `f1-1-claude-mode`,
  pull request #5). It is one commit on top of `main` at `e57a8e1133a63b66229c89e8feee2857d41f5fca`,
  "Run F-1.1 in Claude Code mode; plan the milestone reviews".
- **Target proof:** `git rev-parse f1-1-claude-mode` gives `89ef793…`, and so does
  `gh pr view 5 --json headRefOid`. The working tree's `HEAD` is the same commit, and the only
  untracked path is the ignored `pgn_postmortem.egg-info/`.
- **Files checked:** `CLAUDE.md` and `PLAN.md`. I got this list two ways, and they agree:
  `gh pr view 5 --json files`, and
  `git diff --name-only $(git merge-base main f1-1-claude-mode)..f1-1-claude-mode`, where the merge
  base is `main` itself (`e57a8e1`).
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. It has
  not seen how the change was made.
- **Mode:** Claude Code.

## What I checked

**The target.** The diff has 7 lines added and 2 removed. One is the iteration-1 row of `PLAN.md`
(`PLAN.md:38`). The others are the `harness:` line of the `CLAUDE.md` slot (`CLAUDE.md:48-55`).
Nothing else changed.

**`PLAN.md:38`, iteration 1**

- **Mode:** "Claude Code (owner, 2026-09-24; it replaces the OpenCode choice made earlier the same
  day)". The change is recorded as the owner's decision, it is dated, and it names the earlier
  choice it replaces. On `main`, that earlier choice was "OpenCode (owner, 2026-09-24)", recorded
  by #4. It fits the slot: "the owner picks the mode of each change when it starts"
  (`CLAUDE.md:49-50`).
- **Design record:** "none: Claude mode has no design stage (`CLAUDE.md`); the plan is F-1.1 in
  F-1's block in `ROADMAP.md`". This agrees with four rules:
  - `CLAUDE.md:19`: "There is **no design stage**".
  - `PRINCIPLES.md:73-75`: a design record "exists only in OpenCode mode … Claude mode has none".
  - `design/README.md:4-5`.
  - `ROADMAP.md:143-145`: the shaping becomes "in Claude mode the brief".
  
  `PLAN.md:22-23` asks for a design record only "for OpenCode", so "none" is a valid cell.
- **`design: required`:** the slot keeps it (`CLAUDE.md:79`), and it does not conflict with this
  row:
  - `PRINCIPLES.md` defines only `design: none`.
  - `AGENTS.md:43-46` makes the design stage an OpenCode-mode process.
  - r4's `ADOPT.md:55-56` lists "`design: required` or `design: none` (OpenCode mode)".
  - r4's scaffold describes `required` as "OpenCode mode writes a design record before
    implementation" (`tools/scaffold.mjs:293`).
  
  So `required` governs OpenCode-mode changes only, and it does not create a design stage in
  Claude mode.
- **Reviewer:** "a fresh-context session (`CLAUDE.md`)" matches `CLAUDE.md:13-18`.
- **The other columns are unchanged.** Rows 2–5+ still leave the mode to the owner, and they say a
  design record is written "(OpenCode mode)", so they stay correct whichever mode the owner picks.
- **No stale pointer to the dropped design record remains.** `git grep` for
  `001-f1-1` / `design/001` finds it only in the round-01 and round-02 records and the completion
  note of review 004. Those are history.

**`CLAUDE.md:48-55`, the harness line.** I checked it against the harness clone:

- **The recorded adoption is accurate.** `r4` is an annotated tag (`4cd8a74`) that points at commit
  `39c29e3`, which is the commit the slot names.
- **"Those milestone reviews are not in `r4`" is true.** `git grep -i milestone r4` finds only
  `docs/archive/04-toy-app.md:14`, where "milestones" means iterations. `r4:PRINCIPLES.md` has no
  *Milestones* section.
- **The milestone reviews are on harness `origin/main` and untagged.** `origin/main` is
  `5cfec3c`, and `git describe` gives `r4-104-g5cfec3c`, with no `r5` tag. There,
  `PRINCIPLES.md:189` has a *Milestones* section. Its reviewer "is of a family that implemented
  none of the range — in a Claude-mode range, any model that is not Claude". That matches the
  slot's "reviewed by a model that is not Claude". `BACKLOG.md` on `origin/main` lists "milestone
  reviews" under "**In r5:**". So "the next tagged release of the harness (`r5`)" matches the
  harness's own plan.
- **The line imports no rule.** It records the owner's usual way of working and an intention: r5,
  adopted as its own reviewed change, before F-1's first release. None of the untagged *Milestones*
  mechanics (issues, claims, `AGREE`/`BLOCK`, when to tag) is copied into this project.
- **The line is attributed and dated:** "(owner, 2026-09-24)".
- **The line contradicts nothing.** The per-change process is unchanged: the reviewer is the same
  family by default (`CLAUDE.md:14-15`). A review of a release is a different, later layer, and r4
  does not have one. "Modes: both" still holds, and `merge: owner`, `design: required` and the
  decided list are untouched.

**The owner's decisions.** From the repository I can't tell whether the owner made these
decisions. The owner's merge is that check, so it is not a finding.

**The gates, run on `89ef793`:**

```
$ .venv/bin/python -m ruff check .
All checks passed!
$ .venv/bin/python -m pytest -q
30 passed in 0.59s
```

No tests were skipped, so the Stockfish test ran. The change touches no code, so the gates can only
confirm that nothing else moved.

## Findings

1. **non-blocking**. The timing in the plan may be too late for the rule it plans for. The quote
   is at `CLAUDE.md:53-55`: "adopted as its own reviewed change before F-1's first release at the
   end of F-1.4".
   - **What harness `main` requires.** It says (`origin/main:PRINCIPLES.md`, *Milestones*) that
     "**Claims come before the work.** When a release is scoped, before its work starts, the
     project's plan records … numbered claims (C1…Cn)". The claims are fixed when that change
     lands, and the milestone reviewer checks the plan's history from that commit.
   - **The problem.** As written, r5 could be adopted after F-1.1–F-1.4 are built, just before the
     tag. The first release's work would then have been done before any claims were fixed. That
     release would either fail the rule it is adopting or need an owner override.
   - **Why it does not block.** The line only records an intention. `r5` is untagged and may still
     change. F-1's block already has per-slice done-when checks (`ROADMAP.md:57-60`) that could
     serve as claims.
   - **Suggestion.** When r5 is adopted, the owner decides one of two things: F-1's claims are fixed
     from the existing done-when items, or adoption moves earlier. Alternatively, reword the line
     now to "before F-1's release is reviewed", so the timing does not promise more than the rule
     allows. The project also has no tags yet (`git tag -l` is empty), so the r5 adoption must also
     decide what "the previous tag" is for the first milestone's range.

2. **non-blocking**. "they come with the next tagged release of the harness (`r5`)"
   (`CLAUDE.md:52-53`) states a fact about an untagged release of another repository. It is right
   today (`BACKLOG.md` on harness `main`, "**In r5:** … milestone reviews"). It stops being right if
   r5 ships without them or under another name. A wording such as "the owner plans to take them
   from the next tagged release (`r5`)" would record only what is known. This is wording. It does
   not change the decision.

No other finding. The diff changes only the two stated places. The mode change is marked as the
owner's, dated, and linked to the choice it replaces. No design stage is introduced in Claude mode.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
