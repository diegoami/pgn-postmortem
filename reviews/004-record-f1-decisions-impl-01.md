# Review 004 — Record the F-1 decisions, implementation round 01

- **Revision covered:** `ebea87c4e94555a69946db0e7f9e200c5f764421` (branch `record-f1-decisions`,
  pull request #4). One commit on top of `main`: `ebea87c` "Record the owner's F-1.1 decisions and
  mode".
- **Target proof:** `git rev-parse record-f1-decisions` and `git rev-parse HEAD` both give
  `ebea87c…`, which equals `gh pr view 4 --json headRefOid`.
- **Files checked:** `PLAN.md`, `ROADMAP.md`.
  - Obtained from `gh pr view 4 --json files` and from
    `git diff --name-only $(git merge-base main record-f1-decisions)..record-f1-decisions`; the two
    lists are equal.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. I have not
  seen how the change was made; I judged it from the repository and the pull request.
- **Mode:** Claude Code.

## What I checked, and how

- **Gates, on `ebea87c`** (working tree clean apart from ignored and untracked tool output):
  - `.venv/bin/python -m ruff check .` → `All checks passed!`
  - `.venv/bin/python -m pytest -q` → `30 passed` (a `stockfish` binary is on `PATH`, so the
    Stockfish smoke test ran rather than being skipped).
- **The diff, read in full** (`git diff main...record-f1-decisions`): `ROADMAP.md` gains four lines
  and nothing else; `PLAN.md` changes one row.
- **The decisions (`ROADMAP.md:84`, `:91`, `:98`, `:102`):** each is added as a new line under its
  question. None of the existing lines change, so the question text, the default, the reason and
  the alternatives are the same as on `main`. Each line is marked "Decided by the owner on
  2026-09-24" and names the value it chose. In every case the value is the question's default
  ("(the default)"), and it matches that question: `pgn-postmortem` for 1, "3.11 or newer" for 3,
  "reuse those parts" for 5, which points back to the default's list of reading, duplicate
  removal and parallel analysis code, and standard `[%eval]` for 6. These are the four questions
  marked "before F-1.1". Questions 2, 4, 7, 8 and 9 stay open, and each of those gates a later
  slice. This satisfies *Owner decisions* in `PRINCIPLES.md`: a recommended default, a reason and
  an owner-decision mark were already there, and the decision is now recorded beside them. As the
  brief says, I cannot check from the repository that the owner really gave these answers. The
  owner's merge is that check.
- **Against the slot's *decided* list:** no decision re-opens anything on it. Decision 6 is about
  the library's own output format. It does not trust source evals: F-1's scope still strips a
  source `[%eval]` and re-analyzes every game (`ROADMAP.md:44-49`). The name `pgn-postmortem` is
  already the name in `pyproject.toml`.
- **The `PLAN.md` row for iteration 1 (`PLAN.md:38`):**
  - Mode is "OpenCode (owner, 2026-09-24)". That fits the slot ("the owner picks the mode of each
    change") and `design: required`.
  - The design record is `design/001-f1-1-read-and-analyze.md`. This follows `design/README.md`'s
    `NNN-<slug>.md`, and `001` is the next free number (`design/` holds only `README.md`).
  - "written by the implementer when the iteration starts and agreed before any code" matches
    `design/README.md` (the implementer owns the record, in OpenCode mode) and `AGENTS.md`, *The two
    stages* ("Do not implement before that").
  - The request, done-when, out-of-scope and effort cells are unchanged.
- **Nothing else changed:** the diff touches only those five places.

## Findings

1. **blocking** — `PLAN.md:39-41`, the *design record* column of iterations 2–4 reads "as above".
   On `main`, "above" was "written when the iteration starts (OpenCode mode)", which applies to any
   iteration. After this change, "above" is
   "`design/001-f1-1-read-and-analyze.md`, written by the implementer when the iteration starts…".
   So read as written, F-1.2 to F-1.4 now start from F-1.1's design record. The change did not
   touch those rows, but it changed what they say. Their modes are not chosen yet ("chosen by the
   owner"), so no specific record can be named for them. **Fix:** give rows 2–4 their own text
   again. For example: "written when the iteration starts, if the owner chooses OpenCode mode; none
   in Claude mode". Or say "as row 5+".

2. **blocking** — `ROADMAP.md:84` now records the package name as decided. But the `CLAUDE.md` slot
   still says: "**open work:** … the direction and its open decisions (package name, licence) in
   `docs/book-plan.md`" (`CLAUDE.md:121-122`). `docs/book-plan.md:174-177` also still lists
   "**Package name.**" under *Open decisions*, with nine candidates and the question "Should the
   library keep this repo's name or get its own?". Neither file is in this change. The
   contradiction exists only because of `ROADMAP.md:84`: on `main`, both sources agreed that the
   name was open. `PRINCIPLES.md`, *The ownership map*: "A contradiction found between files is
   recorded as a defect and fixed in the change that found it." A builder who starts F-1.1 from the
   slot's *open work* pointer is told that the name is undecided.
   - **Fix, in this change:**
     - drop "package name" from the slot's parenthesis, or point it at F-1's open questions in
       `ROADMAP.md`;
     - mark the entry in `docs/book-plan.md` as decided, with a link to `ROADMAP.md`.
   - The Python-version, spike-reuse and `[%eval]` decisions do not conflict with
     `docs/book-plan.md`. It already proposes `[%eval]` (line 56) and reusing the spike's analysis
     code (line 152).
   - This adds `CLAUDE.md` and `docs/book-plan.md` to the file list and extends the done-when
     "only `ROADMAP.md` and `PLAN.md` change". If the builder would rather not widen the change,
     *The builder fixes findings…* in `CLAUDE.md` sends that disagreement to the owner.

3. **non-blocking** — `PLAN.md:38`, the *reviewer* cell of iteration 1 still reads "the assignment
   table (OpenCode) or a fresh-context session (Claude)". The mode is now fixed to OpenCode, so the
   Claude alternative no longer applies to this row. Narrowing the cell to "the assignment table in
   `AGENTS.md` (OpenCode)" would make the row say exactly what F-1.1 does. If rows 2–4 keep "as
   above" in this column, change it with finding 1 so that they keep both options.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
Two blocking findings remain (1 and 2).
