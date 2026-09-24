# Review 005 — F-1.1 in Claude Code mode, and the milestone-review plan (round 02)

- **Revision covered:** `f33872972e6ebaf33e58d7dd0346487c44108305` (branch `f1-1-claude-mode`,
  pull request #5). Since round 01 (`89ef793`), two commits have been added:
  - `500a6d8` "Record the F-1.1 mode review, round 01";
  - `f338729` "Answer the F-1.1 mode review, round 01".
- **Target proof:**
  - `git rev-parse f1-1-claude-mode` gives `f338729…`, and so do `HEAD` and
    `gh pr view 5 --json headRefOid`.
  - The only untracked path is the ignored `pgn_postmortem.egg-info/`.
- **Files checked:** `CLAUDE.md`, `PLAN.md` and `reviews/005-f1-1-claude-mode-impl-01.md`. I got this
  list two ways, and they agree:
  - `gh pr view 5 --json files`;
  - `git diff --name-only $(git merge-base main f1-1-claude-mode)..f1-1-claude-mode`, where the merge
    base is still `main` (`e57a8e1`).
- **What changed since round 01** (`git diff 89ef793 f338729 --stat`):
  - the round-01 file was added;
  - `CLAUDE.md` changed, with 7 lines added and 3 removed, all in the `harness:` line;
  - `PLAN.md` did not change.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. This
  round continues the round-01 reviewer session (`PRINCIPLES.md`, *Reviewer sessions*), and it
  re-reads the current revision.
- **Mode:** Claude Code.

## Round-01 findings

| # | finding | status | evidence |
|---|---|---|---|
| 1 | r5 adoption "before F-1's first release" could come after F-1's work, while harness `main` wants a release's claims written before its work | **resolved** | `CLAUDE.md:56-59` now names F-1's claims: the done-when items in `ROADMAP.md`, fixed when #3 landed (`7476e54`). It also sets the first milestone range from that commit, which also answers the "no previous tag" point. I checked this against the repository (below). |
| 2 | "they come with the next tagged release (`r5`)" stated a fact about an untagged release | **resolved** | `CLAUDE.md:52-54`: "they are on `harness_template`'s untagged `main`, and the owner plans to take them from its next tagged release (expected to be `r5`)". This is accurate: harness `origin/main` is `r4-104-g5cfec3c`, with no `r5` tag, and it has a *Milestones* section in `PRINCIPLES.md`. The sentence now records a plan, not a fact. |

**Checking the new text on F-1's claims against the repository:**

- **`7476e54` is what the text says.** It is "Merge pull request #3 from diegoami/shape-f1", dated
  2026-09-24 12:05, a first-parent commit on `main`. It added the F-1 block to `ROADMAP.md`
  (94 lines).
- **The done-when items have not changed since `7476e54`.**
  - `git log 7476e54..f1-1-claude-mode -- ROADMAP.md` lists one commit, `ebea87c` (#4).
  - Its diff only appends "**Decided by the owner on 2026-09-24: …**" to open questions 1, 3, 5
    and 6.
  - The slice table at `ROADMAP.md:57-60`, the "**Done when:**" line (`:62`) and the
    "**Out of scope**" list read the same at `7476e54` and at the head.
- **No F-1 work has landed on `main` since `7476e54`.** `git log --first-parent 7476e54..main` lists
  only #4's merge and two completion notes, and they touch no code.
- **The text stays an intention.** It explains itself by the untagged rule ("Since those rules want
  a release's claims written before its work"). It copies no mechanics into this project: no
  milestone issue, no `C1…Cn` format, no `AGREE`/`BLOCK` on a tag. Under r4, nothing a builder does
  today changes.
- **It contradicts nothing.**
  - `PRINCIPLES.md` has no concept of claims.
  - `ROADMAP.md` is unchanged.
  - The rest of the slot (`merge: owner`, `design: required`, the decided list) is untouched.

**`PLAN.md:38`** has not changed since round 01, so what round 01 found for it still holds.

**The round-01 record** in the change (`500a6d8`) is byte-identical to the file I wrote
(`git diff --quiet f1-1-claude-mode -- reviews/005-f1-1-claude-mode-impl-01.md` exits 0).

**The gates, run on `f338729`:**

```
$ .venv/bin/python -m ruff check .
All checks passed!
$ .venv/bin/python -m pytest -q
30 passed in 0.59s
```

No tests were skipped. This round changes only records, so the gates only confirm that nothing else
moved.

## Findings

1. **non-blocking** — `CLAUDE.md:58`, "fixed when #3 landed (`7476e54`) before any F-1 work began".
   - **What is imprecise.** The spike toward F-1 on `book-poc` is older than `7476e54`
     (`e90ef99`, 2026-09-24 02:28, "WIP: package layout, config, pluggable sources and ingest
     (book spike)"). F-1.1 will reuse it (`ROADMAP.md`, question 5, decided). So F-1 work did begin
     before the claims were fixed. It had not landed on `main`.
   - **Why it does not block.** A milestone reviews `main`, and any reused spike code enters `main`
     through F-1.1's pull request, after `7476e54`. So the range the sentence names still covers
     all of it.
   - **Suggestion:** "before any F-1 work landed on `main`".

2. **non-blocking** — `CLAUDE.md:57-59`, "F-1's claims are its done-when items … F-1's first
   milestone review covers the range from that commit".
   - **These are choices.** The r5 adoption would otherwise make them: which items count as claims,
     and where the first range starts, since the project has no tags yet. The text states them as
     settled.
   - **They sit after the owner's mark.** The mark "(owner, 2026-09-24)" closes the sentence before
     them. They come from the implementer's answer to round 01 (`f338729`'s message).
   - **The done-when items don't all fit harness `main`'s claim shape.** That shape is numbered
     claims, each naming its check, checked before the tag. The last F-1.4 item (`ROADMAP.md:60`,
     "complete only when `pip install <name>==<version>` from PyPI … builds the demo book") can only
     run after the tag and the upload. A reviewer before the tag could only grade it COULD NOT TEST.
   - **Why it does not block.** Neither point binds anything under r4, and the r5 adoption is
     planned as its own reviewed change, where they can be settled. The owner's merge also covers
     whether the owner accepts these two choices.
   - **Suggestion.** If the owner wants them marked now, one of two changes:
     - extend the mark to cover them;
     - or phrase them as "the owner intends … ; the r5 adoption settles the numbering and the
       post-tag PyPI item".

No other finding. The change still touches only the stated places. Both round-01 findings are
addressed, and the fix brings no rule from the untagged harness into this project.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
