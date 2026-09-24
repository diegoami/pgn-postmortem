# Review 004 — Record the F-1 decisions, implementation round 02

- **Revision covered:** `dd97d55436f3a735bd6ab0ec871e8c68063e3228` (branch `record-f1-decisions`,
  pull request #4). Round 01 covered `ebea87c`. Two commits since then:
  - `278a019` records the round-01 review;
  - `dd97d55` is "Answer the F-1 decisions review, round 01".
- **Target proof:** `git rev-parse record-f1-decisions`, `HEAD` and `origin/record-f1-decisions`
  all give `dd97d55…`, which equals `gh pr view 4 --json headRefOid`.
- **Files checked:** `CLAUDE.md`, `PLAN.md`, `ROADMAP.md`, `docs/book-plan.md`,
  `reviews/004-record-f1-decisions-impl-01.md`.
  - Obtained from `gh pr view 4 --json files` and from
    `git diff --name-only $(git merge-base main record-f1-decisions)..record-f1-decisions`; the two
    lists are equal.
  - The round-01 file on the branch is the file I wrote: the working tree is clean after `278a019`
    added it, and `dd97d55` does not touch it.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. This
  re-review continues the round-01 reviewer session (`PRINCIPLES.md`, *Reviewer sessions*). I
  re-read the current revision; I did not rely on the coordinator's summary.
- **Mode:** Claude Code.

## What I checked, and how

- **Gates, on `dd97d55`:**
  - `.venv/bin/python -m ruff check .` → `All checks passed!`
  - `.venv/bin/python -m pytest -q` → `30 passed` (Stockfish is on `PATH`, so its test ran).
- **The answer to round 01, read in full:** `git diff 278a019 dd97d55`. It changes one line pair
  in `CLAUDE.md`, rows 1–4 of the `PLAN.md` iteration table, and the *Package name* entry in
  `docs/book-plan.md`. I checked it against `PRINCIPLES.md`, `AGENTS.md`, `design/README.md`,
  `reviews/README.md` and the `CLAUDE.md` slot on `main`.
- **Unchanged since round 01:** `git diff ebea87c dd97d55 -- ROADMAP.md` is empty. The four
  decisions and the untouched questions and defaults are therefore still as I checked them in
  round 01.

## Round-01 findings

| # | finding | status | evidence |
|---|---|---|---|
| 1 | rows 2–4's "as above" design record pointed at F-1.1's record | resolved | `PLAN.md:39-41` now say "written when the iteration starts (OpenCode mode)". That is `main`'s original wording, so no specific record is named for iterations whose mode is not chosen yet. Row 5+'s "as above" in the reviewer column now points at row 4, which keeps both options, as before. |
| 2 | the package name was decided in `ROADMAP.md` but still listed as open in the `CLAUDE.md` slot and `docs/book-plan.md` | resolved | `CLAUDE.md:121-122`: "`ROADMAP.md`, including F-1's open questions (the licence among them); the direction in `docs/book-plan.md`". `docs/book-plan.md:175-177` records the decision with the date and a pointer to question 1 in `ROADMAP.md`. It keeps the part that is still open ("whether the pipeline (F-3) is a separate package or repository"). No other file still lists the name as open: `grep` for the old candidates finds them only as alternatives in question 1 (`ROADMAP.md:82`), which is correct. The PR body's done-when records the wider file list and the reason for it. |
| 3 | iteration 1's reviewer cell still offered the Claude option | resolved | `PLAN.md:38`: "the assignment table (OpenCode)". |

**Did the fixes introduce anything new?**
- **The `CLAUDE.md` edit:** it changes a pointer in the slot and no process rule, so the bootstrap
  needs no more than this review. It contradicts nothing on the slot's *decided* list.
- **`docs/book-plan.md`'s other open decisions** (licence, the Markdown pages, the selection
  weights) are still open, and so are the matching questions in `ROADMAP.md` (2, 4 and 9). The two
  files agree.

## Findings

1. **non-blocking** — `CLAUDE.md:121-122`. On `main`, the *open work* pointer sent a reader to
   `docs/book-plan.md` for open decisions. It now sends them there only for "the direction". Two
   decisions are recorded only in `docs/book-plan.md`, *Open decisions*: "whether the pipeline
   (F-3) is a separate package or repository" and "Where Diego's own book lives". A reader who
   follows the slot now gets no hint that they are there. Suggestion: "the direction, and the
   decisions not yet in `ROADMAP.md`, in `docs/book-plan.md`". Nothing depends on those two
   decisions before F-3, so this does not block.

2. **non-blocking** — the PR body. *What was built* still lists only `ROADMAP.md` and `PLAN.md`,
   while the done-when now includes `CLAUDE.md` and `docs/book-plan.md`. The closing line names
   only the round-01 review file. Adding the two files to *What was built*, and naming the round-02
   file, would make the body match the change. This does not change the diff.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
