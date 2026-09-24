# Review 003 — Shape F-1, implementation round 03

- **Revision covered:** `f6e41b46d63fcace71bf63375db49bc158c7e856` (branch `shape-f1`, pull
  request #3). Round 02 covered `8118f1b`. Two commits since then:
  - `9de7b48` records the round-02 review;
  - `f6e41b4` is "Answer the F-1 shaping review, round 02".
- **Target proof:** `git rev-parse shape-f1`, `origin/shape-f1` and `HEAD` all give `f6e41b4…`,
  which equals `gh pr view 3 --json headRefOid`.
- **Files checked:** `PLAN.md`, `ROADMAP.md`, `reviews/003-shape-f1-impl-01.md`,
  `reviews/003-shape-f1-impl-02.md`.
  - Obtained from `gh pr view 3 --json files` and from
    `git diff --name-only $(git merge-base main origin/shape-f1)..origin/shape-f1`; the two lists
    are equal.
  - `f6e41b4` does not touch either review file (`git diff 9de7b48 f6e41b4 -- reviews` is empty).
    The round-02 file still ends with my signature and "No blocking finding remains."
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. This
  re-review continues the round-01 and round-02 reviewer session (`PRINCIPLES.md`, *Reviewer
  sessions*). I re-read the current revision; I did not rely on the coordinator's summary.
- **Mode:** Claude Code.

## What I checked, and how

- **Gates, on `f6e41b4`:**
  - `.venv/bin/python -m ruff check .` → `All checks passed!`
  - `.venv/bin/python -m pytest -q` → `30 passed`
- **The answer to round 02, read in full:** `git diff 9de7b48 f6e41b4`. It changes only the four
  slice rows (`ROADMAP.md:57-60`). I checked it against `ROADMAP.md`, `PLAN.md`, `PRINCIPLES.md` and
  the `CLAUDE.md` slot on `main`.
- **Unchanged parts:**
  - the *Original request* line, still byte-identical to `main`'s F-1 row;
  - `PLAN.md`, unchanged since round 02.

## Round-02 findings

| # | round 02 | status at `f6e41b4` | evidence |
|---|---|---|---|
| 1 | an owner's "no" only works before the merge | **resolved** | F-1.2, F-1.3 and F-1.4 now say "before merging": the owner records the verdict on the slice's pull request, a "no … does not merge", and the completion note only transcribes the verdict (`ROADMAP.md:58-60`). This matches `PRINCIPLES.md` (*Completion*: the note may only transcribe). |
| 2 | the `epub` gate had no command | **resolved** | The check is now "a test in the tests gate … with the tests row of the gates table updated in the same change" (`ROADMAP.md:60`). No third gate, so the slot's "Only the two gates above decide a merge" stays true. |
| 3 | the PyPI release had no done-when item | **resolved** | "F-1.4, and with it F-1, is complete only when `pip install <name>==<version>` from PyPI in a clean environment builds the demo book; the completion note records the PyPI URL and that run" (`ROADMAP.md:60`). |
| 4 | the owner's confirmation of the quotes is not traceable | unchanged, by agreement | As noted in round 02, the owner's merge is its check. `ROADMAP.md:22` is unchanged. |
| 5 | F-1.1 had no check of the command line or of parallel analysis | **resolved** | New tests: "give the same output with two workers as with one; and run the command line end to end on a fixture collection (read, then analyze) as a subprocess" (`ROADMAP.md:57`). |

## New findings

1. **non-blocking.** F-1.4 now merges before its last done-when item can close, and the block does
   not say what happens if that item fails.
   - **The sequence** (`ROADMAP.md:60`), which is the only workable one: the owner publishes "after
     the merge", and F-1.4 is "complete only when" the PyPI install works.
   - **What this departs from:** the usual reading of `PRINCIPLES.md` (*Completion*: "when a change
     lands", the note records the evidence that closed each item). Here the note is appended after
     the release, not at the merge.
   - **Suggested fix:** one clause that a failing PyPI install or release run is handled by the
     defect path, not by re-opening the merged slice.
   - **Also suggested:** declare the release workflow in the slot next to `pages.yml` as a second
     **post-merge check**, since it runs after merges and cannot block them.

2. **non-blocking.** The clean-environment check does not say what it builds from, or whether it
   needs Stockfish.
   - **The check:** "`pip install <name>==<version>` from PyPI in a clean environment builds the demo
     book" (`ROADMAP.md:60`). This wording was already there in round 02 (as `pip install <name>`);
     I missed it then.
   - **The input question:** the demo collection is committed to the repository in F-1.3, not
     necessarily in the wheel.
   - **The analysis question:** source `[%eval]` comments are now stripped (`ROADMAP.md:43-48`).
     Unless the demo ships with the library's own analysis output, which counts as "already analyzed
     (in its own output)", the check re-analyzes the whole demo collection with Stockfish.
   - **Suggested fix:** state the input and whether analysis is expected, for example "from the
     committed demo collection and its committed analysis, without Stockfish".

3. **non-blocking.** Verdict comments are not attributable.
   - **The problem:** under the single GitHub account (`PRINCIPLES.md`, *Comment, not approval*),
     the owner's verdict comments on a slice's pull request (`ROADMAP.md:58-60`) come from the same
     account the agents post from.
   - **Suggested fix:** the owner signs the verdict comment, so the completion note can quote an
     owner's verdict and not an agent's.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged by the owner on 2026-09-24 as `7476e54` (pull request #3); the last clean round, 03, covers `f6e41b4`. CI on the merge commit passed: https://github.com/diegoami/pgn-postmortem/actions/runs/35985173971.

- **F-1's block has every field of the block format:** `ROADMAP.md`, *Accepted requests*, on `main`. Checked in rounds 01–03.
- **Every slice fits one iteration and has runnable done-when checks:** F-1.1 to F-1.4, with the owner-verdict and PyPI items tightened in rounds 01–02.
- **The original wording is quoted unchanged:** confirmed byte for byte in round 01. The owner confirmed the added quotes on 2026-09-24, and the merge is its check.
- **Only `ROADMAP.md` and `PLAN.md` change,** plus the review records: the pull request's file list.
- **The gates:** `ruff check .` passed and `pytest -q` gave 30 passed at every round.

Left open by the owner's decision, to settle when F-1.4 is shaped for its session: round-03 findings 1 (a failed PyPI release after the merge goes through the defect path, and the release workflow is declared as a post-merge check) and 2 (what the clean-install demo build is built from, and whether it needs Stockfish). Finding 3 (sign owner verdict comments) is a habit for the owner, not a change.

— Implementer, Claude Opus 5.5 (claude-opus-5-5)
