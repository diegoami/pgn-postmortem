# Review: Pages check wording, implementation round 01

**Revision reviewed:** f5010f697a0497ba3e2a6a035854ea8d67d27d91
**Files reviewed:** `CLAUDE.md`. I got the list from `gh pr view 2 --json headRefOid,files`, which gave head `f5010f697a0497ba3e2a6a035854ea8d67d27d91` and the one file `CLAUDE.md` (+4 / −2). I checked it against the local diff: `git rev-parse fix-pages-check-wording` = `f5010f697a0497ba3e2a6a035854ea8d67d27d91` (also `HEAD`), and `git diff --name-only $(git merge-base main fix-pages-check-wording)..fix-pages-check-wording` gives only `CLAUDE.md`. The two lists are identical. The branch has one commit on top of `main` (`f5010f6`). The only untracked path is `pgn_postmortem.egg-info/`, which is not part of the change.
**Reviewer:** Claude Opus 5.5 (claude-opus-5-5), a fresh-context Claude Code subagent that did not see the implementation. Claude Code mode.

### What the change claims

It implements non-blocking finding 2 of `reviews/001-adopt-harness-impl-02.md`. That finding said "a second red run is a defect" overstated the defect path, because an outage has no assertion to land. It suggested: "say a second red run is investigated, and only a failure caused by the repository goes through the defect path."

### Findings

1. **A failure that is neither the repository's files nor an outage isn't named, and a non-defect result isn't recorded anywhere.** Non-blocking. `CLAUDE.md:88-90` separates "a failure caused by this repository (the workflow or the content of `examples/docs/`)" from "an outage of GitHub or the network". The deploy job also depends on GitHub-side settings that aren't in the tree: the Pages source set to "GitHub Actions" and the `github-pages` environment (`.github/workflows/pages.yml:49-51`). Because the sentence says "only … is a defect", a broken setting falls on the "not a defect" side. That reading is consistent with the defect path, since no committed assertion could catch it either. But "investigated" doesn't say where the outcome goes. A persistent non-defect failure, for example a disabled Pages setting, could leave the demo site down with nothing in the repository saying so (`PRINCIPLES.md`, "Durable facts belong in the repository"). This is optional. If the owner wants it closed, one clause would do, such as "a failure outside the repository is reported to the owner". It doesn't block, because the finding being implemented only asked for the defect/outage split, and the new text contradicts no rule.

No blocking findings.

### Verified

- **The change does what the finding asked.** The new text at `CLAUDE.md:87-90` ("A second red run is investigated: only a failure caused by this repository … is a defect, handled by the defect path in `PRINCIPLES.md`; an outage of GitHub or the network is not.") follows the round-02 suggestion almost word for word. The overstatement is gone: the defect path (`PRINCIPLES.md`, "fixed by a change that lands the assertion that would have caught it") now applies only to failures where the repository could hold such an assertion, such as a workflow error or bad generated content traced back to `scripts/`.
- **Consistent with the gates disciplines and the gates table.** The table (`CLAUDE.md:77-80`) is unchanged and still lists only `lint` and `tests`. "Only the two gates above decide a merge" (`CLAUDE.md:83`) is unchanged, so the Pages check is still not a gate, and discipline 2 ("A red gate does not merge") isn't touched. The single re-run is still justified by the stated failure model, "network and GitHub availability" (`CLAUDE.md:86-87`), which fits discipline 1's requirement that repeats be justified by a failure model. The trigger description still matches `.github/workflows/pages.yml:7-9`.
- **No new rule the harness doesn't support.** "Investigated" narrows an existing sentence and adds no obligation, role or record type. The edit stays inside the project slot (`<!-- SLOT:BEGIN -->` … `<!-- SLOT:END -->`), which `CLAUDE.md` owns according to the ownership map, and nothing outside the slot is restated.
- **Nothing else changed.** `git diff main..fix-pages-check-wording --word-diff` shows only this paragraph: "once; a" becomes "once. A", plus the added clauses. The PR files list is `CLAUDE.md` alone. The commit message gives an imperative summary and a body with the reason, as the slot's conventions require.
- **Gates.** At `f5010f6`, `.venv/bin/python -m ruff check .` printed "All checks passed!" and `.venv/bin/python -m pytest -q` printed "30 passed in 0.99s". CI run `35972779001` (`headSha` `f5010f697a0497ba3e2a6a035854ea8d67d27d91`), concluded `success` on 3.10 and 3.12.
- **Review is required.** `CLAUDE.md` is a harness file and the edit changes process text, so under the conservative floor and the bootstrap it is non-trivial and takes one Claude-mode review. This file is that review.

### Not verified

- I didn't run the Pages workflow. It runs only after a merge to `main`, and this change doesn't touch `examples/docs/**` or the workflow, so it won't trigger it.
- I did not read `.env` or any credentials.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged by the owner on 2026-09-24 as `2c2eb01` (pull request #2); the clean round, 01, covers `f5010f6`.

- **`CLAUDE.md` separates failures caused by the repository, which are defects, from outages, which aren't:** `CLAUDE.md:87-90` on `main`.
- **Nothing else changed:** the pull request's only code file is `CLAUDE.md` (4 lines added, 2 removed), plus this review record.
- **The gates are green:** `ruff check .` passed and `pytest -q` gave 30 passed. The pull request's checks (test on Python 3.10 and 3.12, GitGuardian) passed before the merge.

The review's non-blocking finding (report a Pages failure caused by GitHub-side settings to the owner) was left as is by the owner's decision.

— Implementer, Claude Opus 5.5 (claude-opus-5-5)
