# Review 003 — Shape F-1, implementation round 02

- **Revision covered:** `8118f1b12a362387152c7689e55280eaafb712b4` (branch `shape-f1`, pull
  request #3).
  - Round 01 covered `103a165`. Since then, two commits: `9fd480c` records the round-01 review, and
    `8118f1b` is "Answer the F-1 shaping review, round 01".
- **Target proof:** `git rev-parse shape-f1`, `origin/shape-f1` and `HEAD` all give `8118f1b…`, which
  equals `gh pr view 3 --json headRefOid`.
- **Files checked:** `PLAN.md`, `ROADMAP.md`, `reviews/003-shape-f1-impl-01.md`.
  - Obtained from `gh pr view 3 --json files` and from
    `git diff --name-only $(git merge-base main origin/shape-f1)..origin/shape-f1`; the two lists
    are equal.
  - The round-01 file is unchanged by `8118f1b` (`git diff 9fd480c 8118f1b -- reviews/` is empty).
    It still ends with my signature and "Two blocking findings remain (1 and 2)."
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. This is a
  re-review that continues the round-01 reviewer session, which `PRINCIPLES.md` (*Reviewer sessions*)
  allows. I re-read the current revision rather than the implementer's summary.
- **Mode:** Claude Code.

## What I checked, and how

- **Gates, on `8118f1b`:** `.venv/bin/python -m ruff check .` → `All checks passed!`, and
  `.venv/bin/python -m pytest -q` → `30 passed`.
- **The round-01 answer, read in full:** `git diff 9fd480c 8118f1b`. It was checked against
  `ROADMAP.md`, `PLAN.md`, `PRINCIPLES.md` and the `CLAUDE.md` slot on `main`.
- **Original wording:** the *Original request* line (`ROADMAP.md:21`) is still byte-identical to
  `main`'s F-1 row.
- **`PLAN.md`:** every column of rows 1–5+ is filled.
- **The Ubuntu package claim:** `apt-cache policy epubcheck` on Ubuntu 24.04 (what `ubuntu-latest`
  runs) shows candidate `4.2.6-2`, so "the Ubuntu package" exists.

## Round-01 findings

| # | round 01 | status at `8118f1b` | evidence |
|---|---|---|---|
| 1 | blocking: skipping source `[%eval]` re-opened "every game is re-analyzed" | **resolved** | `ROADMAP.md:43-50`: source `[%eval]` is stripped with the other comments; every game is re-analyzed by the library, which only skips games it has already analyzed itself. Trusting source evals is now listed out of scope, naming the decision (`ROADMAP.md:69-70`). F-1.1 tests "strip comments (a source `[%eval]` included)" and "analyze nothing on a second run" (`ROADMAP.md:57`). |
| 2 | blocking: F-1.3 needed a demo collection picked only in F-1.4 | **resolved** | F-1.3 now lands "the demo collection of open question 7, committed with its source named" (`ROADMAP.md:59`). Question 7 is marked "(before F-1.3)" (`ROADMAP.md:99`). |
| 3 | `epubcheck` undeclared | resolved, with a remainder in new finding 2 | `ROADMAP.md:60` says: a new `epub` gate, the Ubuntu package installed in CI, skipped locally when the tool is missing, and added to the gates table in the same change. |
| 4 | PyPI release needs credentials | resolved, with a remainder in new finding 3 | `ROADMAP.md:60`: "The owner publishes the release … the builder never handles PyPI credentials". |
| 5 | owner checks could not fail, and had no record | resolved | `ROADMAP.md:58-60`: each owner verdict is recorded in the completion note, and "a 'no' sends the slice back". |
| 6 | question 3's reason, and the CI conflict | resolved | `ROADMAP.md:87-89`: the reason is now 3.10's end of life only. F-1.1 moves the CI matrix and the gates table (`ROADMAP.md:57`). |
| 7 | added quotes not traceable to the owner | resolved as recorded | `ROADMAP.md:22` says "confirmed by the owner that day". The "from 2005" claim is replaced by the spike's count, which `docs/book-plan.md` gives as 1,791. See new finding 4 on how the confirmation is recorded. |
| 8 | untested scope | mostly resolved | New tests cover globs across directories, the second run, revision-mode questions, and building without analysis (`ROADMAP.md:57-58`). The remainder is new finding 5. |
| 9 | which decision gates which slice | resolved | Each question now names its slice (`ROADMAP.md:80-105`). |
| 10 | Google Play Books dropped | resolved | Question 8 now offers it as the alternative (`ROADMAP.md:102-104`). |
| 11 | `PLAN.md` rows without the owner's wording | resolved | Rows 2–4 now carry the quote (`PLAN.md:39-41`). |

## New findings

1. **non-blocking.** An owner's "no" is final only if the verdict comes before the merge, and the
   block does not say so.
   - **What the block says:** F-1.2, F-1.3 and F-1.4 record the owner's verdict "in the slice's
     completion note" (`ROADMAP.md:58-60`).
   - **The timing problem:** `PRINCIPLES.md` (*Completion*) has the note appended "when a change
     lands". A "no" that "sends the slice back" only works if the owner gives the verdict before
     merging. After the merge, a "no" is the defect path, not a send-back.
   - **Suggested fix:** "before the owner merges".

2. **non-blocking.** The new `epub` gate (`ROADMAP.md:60`) has no command yet.
   - **What is unclear:** the gates table needs a command for every gate. The block says both "a
     new `epub` gate" and "the test is skipped locally". That reads as a pytest test, which would
     belong to the existing `tests` gate, not to a new gate.
   - **A second edit needed:** a third gate also means changing the slot's sentence "Only the two
     gates above decide a merge" (`CLAUDE.md:83` on `main`). This is a harness change under the
     bootstrap.
   - **Why it is non-blocking:** F-1.4 must write the table row anyway, and its own review will see
     it.
   - **Suggested fix:** name the intended command, or fold the check into `tests` with the tool
     added to that row's *covers* and *failure model*.

3. **non-blocking.** The PyPI release no longer has a done-when item.
   - **The change:** round 01 had "the release is on PyPI". Now "The owner publishes the release"
     (`ROADMAP.md:60`) states who does it, not a check that it happened.
   - **Why it matters:** the owner may push the tag after the slice merges. If so, F-1's
     "Done when: all four slices have landed" (`ROADMAP.md:62`) can be true while scope line 51
     ("It is released on PyPI") is not.
   - **Suggested fix:** say whether the upload closes F-1.4 or is a separate step after it, and how
     it is checked (`https://pypi.org/pypi/<name>/json` → 200, then `pip install <name>` from PyPI
     in a clean environment).

4. **non-blocking.** The owner's confirmation of the added quotes is recorded, but nothing in the
   repository traces it to the owner.
   - **What I can and cannot confirm:** the coordinator's message said the owner confirmed them on
     2026-09-24, and `ROADMAP.md:22` records "confirmed by the owner that day". A reviewer cannot
     check that from the repository, and an agent's message is not the owner's confirmation.
   - **Why it is non-blocking:** the owner merges, and merging this line is the owner's own check of
     it.
   - **Suggested fix:** if a durable trace is wanted, the owner's confirming words can go in the pull
     request, as the row confirmation at `ROADMAP.md:8` did.

5. **non-blocking** (remainder of round-01 finding 8). F-1.1 lands "the library package with its API
   and command line" and parallel analysis (`ROADMAP.md:57`), but no done-when item checks them.
   - **Missing:** a check that the command-line entry point runs (for example
     `<name> --help` after `pip install -e .`), and one that analysis runs with more than one
     worker.
   - **Why it is non-blocking:** both are cheap to add when F-1.1 starts, and nothing here makes the
     slice unverifiable.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
