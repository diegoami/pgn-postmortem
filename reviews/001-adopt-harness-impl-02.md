# Review — adopt harness r4, implementation round 02

**Revision reviewed:** 2584897c9dd3e3c17cd70cc18de04ec6b97c0706
**Files reviewed:** `AGENTS.md`, `CLAUDE.md`, `PLAN.md`, `PRINCIPLES.md`, `ROADMAP.md`, `design/README.md`, `docs/book-plan.md`, `reviews/001-adopt-harness-impl-01.md`, `reviews/README.md`, `verification/README.md`. I got the list from `gh pr view 1 --json headRefOid,files`, which gave head `2584897c9dd3e3c17cd70cc18de04ec6b97c0706` and those ten files. I checked it against the local diff: `git merge-base main 2584897` = `c50bddece22b9f02ac8cc16ae9e26c034555667e`, then `git diff --name-only c50bdde..2584897`. The two lists are identical. `adopt-harness`, `origin/adopt-harness` and `HEAD` all resolve to `2584897`. Two commits were added since round 01: `4ccf3ed` (adds the round-01 file, identical to the one I wrote) and `2584897` (changes `CLAUDE.md`, `ROADMAP.md` and `docs/book-plan.md`). The only untracked path was `pgn_postmortem.egg-info/`, which is not part of the change.
**Harness reference:** `harness_template` tag `r4` (commit `39c29e3b40534bdcfa379e4f426cd3dc3dc88440`), read with `git show r4:<path>`.
**Reviewer:** Claude Opus 5.5 (claude-opus-5-5), a fresh-context Claude Code subagent continuing the round-01 reviewer session (`PRINCIPLES.md:90-93`). Claude Code mode.

### Round-01 findings

- **1 (no design record, not explained): resolved.** The PR body now has a "**No design record.**" paragraph. It quotes `PRINCIPLES.md` ("Claude mode has none, so it has no design records"), says that rule takes precedence over `ADOPT.md` §5 and §6, and marks the contradiction inside r4 as a harness defect to report upstream. It is not fixed here, which is correct.
- **2 (`pages` listed as a merge gate): resolved.** The gates table at `CLAUDE.md:77-80` now has only `lint` and `tests`. `CLAUDE.md:83-88` says "Only the two gates above decide a merge", describes `pages.yml` as a "**post-merge check** … that cannot block it", and replaces the old repeats mismatch with "a red run is re-run once". The trigger description matches `.github/workflows/pages.yml` (`push: branches: [main]`, `paths: ["examples/docs/**", ".github/workflows/pages.yml"]`).
- **3 (settled choices vs. "nothing agreed"): resolved.** `docs/book-plan.md:3-9` now says "The owner's settled choices are the ones listed under *decided, and not to be re-opened* in the `CLAUDE.md` project slot … everything else here is direction". I checked each example it gives against the slot: DeepSeek with bring-your-own-key (`CLAUDE.md:109-111`), the chapters and English (`CLAUDE.md:112-113`), and library before pipeline (`CLAUDE.md:117-118`). All are there.
- **4 (owner decisions missing default and reason): resolved.** The PR's decision table now has a "recommended default and reason" column for all six decisions and a separate "owner's decision" column. It also states "the owner chose the default every time". That matches `PRINCIPLES.md:109-111`.
- **5 (roadmap quotes unverifiable): resolved by the owner.** `ROADMAP.md:9` records "The owner confirmed on 2026-09-24 that the quoted wording of F-1 to F-3 is the owner's own." I can't check that confirmation from the repository. It is recorded in the file that owns requests, which is what the finding asked for.

### New findings

1. **The PR body's slot summary still lists Pages as a gate.** Non-blocking. Under "The filled slot, in short", the PR body still has "**gates:** … the Pages workflow". That contradicts the fix for finding 2 (`CLAUDE.md:83`, "Only the two gates above decide a merge"). The file is correct and the body is stale. The same summary still says "no long runs on his data unless he asks", while `2584897` switched the slot to neutral wording (`CLAUDE.md:98-99`). Update both lines in the PR body.

2. **Calling a second failed Pages run a "defect" overstates what the defect path can do.** Non-blocking. `CLAUDE.md:87-88` says "a second red run is a defect, handled by the defect path in `PRINCIPLES.md`". But the defect path (`PRINCIPLES.md:115-119`) is "fixed by a change that lands the assertion that would have caught it". The failure model in `CLAUDE.md:86-87` is network and GitHub availability, and an outage has no assertion to land. That clause is a small invented rule. Suggestion: say a second red run is investigated, and only a failure caused by the repository goes through the defect path. Nothing in r4 is contradicted outright, so this doesn't block.

### Verified

- **Gates.** At `2584897`, `.venv/bin/python -m ruff check .` printed "All checks passed!" and `.venv/bin/python -m pytest -q` printed "30 passed in 0.69s". CI run `35971565602` for head `2584897c9dd3e3c17cd70cc18de04ec6b97c0706` concluded `success` on 3.10 and 3.12.
- **No drift in the r4 files.** The verbatim files (`AGENTS.md`, `design/README.md`, `reviews/README.md`, `verification/README.md`) still show no diff against `r4:<path>`. `PRINCIPLES.md` still differs from r4 only in the conservative floor (lines 43-45). `PLAN.md` is unchanged since `8bba768`.
- **The new commit is scoped to the answers.** `2584897` touches only the lines needed for findings 2, 3 and 5, plus the neutral-pronoun edits in `CLAUDE.md:45,72,98-99`. None of it touches the process text outside the slot, so the adapters still carry only mode-specific text. The added `ROADMAP.md:9` line is a record, not a rule.
- **The round-01 file is unchanged.** `reviews/001-adopt-harness-impl-01.md` at `4ccf3ed` is byte-identical to the file written in round 01. Nothing else in the repository changed.

### Not verified

- I cannot check the owner's confirmation of the roadmap wording (`ROADMAP.md:9`) or the owner decisions in the PR body from the repository. I take them as recorded.
- I did not read `.env` or any credentials.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged by the owner on 2026-09-24 as `7f54e2f` (pull request #1); the last clean round, 02, covers `2584897`. The done-when items of r4 `ADOPT.md` §6:

- **Every chosen harness file exists:** `PRINCIPLES.md`, `AGENTS.md`, `CLAUDE.md`, `PLAN.md`, `ROADMAP.md`, `design/README.md`, `reviews/README.md` and `verification/README.md` are on `main` at `7f54e2f`.
- **The slot is filled from this repository:** the product, paths, never-echo list, `merge: owner`, `design: required` and the gates table are in `CLAUDE.md`. Both review rounds checked them against the repository.
- **The gates table names commands that run here:** `ruff check .` passed and `pytest -q` gave 30 passed, locally and in the reviews. CI on the merge commit passed: https://github.com/diegoami/pgn-postmortem/actions/runs/35972646748.
- **The adapters carry only mode-specific text:** `AGENTS.md` is verbatim r4, and `CLAUDE.md` changes only inside the slot. Checked in rounds 01 and 02.
- **Every collision is reported:** `PLAN.md` from `book-poc` was split into `ROADMAP.md` F-1 to F-3 and `docs/book-plan.md`, as the pull request body records.
- **The review records and provenance exist:** `reviews/001-adopt-harness-impl-01.md` and `-02.md` are both posted on #1. The provenance (r4, `39c29e3`, 2026-09-24) is in the slot. There's no design record in Claude mode (r4 `PRINCIPLES.md`), as the pull request body explains.
- **Nothing else changed:** the diff from the merge base contains only the harness files, `docs/book-plan.md` and the review records.

Left open: the round-02 wording point about the post-merge Pages check goes into a separate change, as the owner decided.

— Implementer, Claude Opus 5.5 (claude-opus-5-5)
