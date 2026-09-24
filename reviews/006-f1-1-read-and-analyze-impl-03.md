# Review 006: F-1.1, read and analyze (round 03)

- **Revision covered:** `a82bb8213a66698fcbd752f6bf45ef6ae8c6f3bf` (branch
  `iteration-1-read-and-analyze`, pull request #6). Round 02 covered `cbe3b31…`.
- **Target proof:**
  - After `git fetch origin` and `git checkout --detach origin/iteration-1-read-and-analyze`,
    `git rev-parse HEAD` gives `a82bb82…`. This matches `gh pr view 6 --json headRefOid`.
  - `git merge-base origin/main HEAD` is `3850530508de72da436b4de69ce143cc1c65e8a0`, which is
    also `origin/main`.
- **Files checked** (17). I got the list two ways, sorted both, and compared them with `diff`;
  they are the same: `gh pr view 6 --json files` and `git diff --name-only 3850530..a82bb82`.
  - The 16 files of round 02, plus `reviews/006-f1-1-read-and-analyze-impl-02.md`.
- **Commits since round 02:**
  - `aa87d41` records the round-02 review. `git show HEAD:reviews/006-…-impl-02.md` is
    byte-identical to the file I wrote (checked with `cmp`).
  - `78781d1` is the owner's identity rule.
  - `3f3ffc6` fixes finding 9.
  - `a82bb82` answers finding 11.
  - `git diff --stat cbe3b31..a82bb82` touches `CLAUDE.md`, `README.md`,
    `pgn_postmortem/{analysis,cli,collection}.py`, the three test files, and the review file.
    `pyproject.toml`, `scripts/`, `examples/` and `data/` are unchanged.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. This
  round continues the round-01/02 reviewer session (`PRINCIPLES.md`, *Reviewer sessions*). I
  re-read the current code, and did not rely on the PR's "Answer to review round 02".
- **Mode:** Claude Code.
- **Scope of judgment:** the coordinator says the owner decided, on 2026-09-24, that a game's
  identity is its moves, result, date and start position, for every game length and without the
  player names. I judge how that rule is implemented and documented, not the choice itself.

## Gates, run by the reviewer

I reinstalled the package with `pip install -e .` in the worktree's venv (Python 3.12.3,
Stockfish 16) and cleared `__pycache__`.

```
$ .venv/bin/python -m ruff check .
All checks passed!
$ .venv/bin/python -m pytest -q -rs
54 passed in 4.45s        (nothing skipped)
```

CI (`gh pr checks 6`, run 36004567196, `headSha` `a82bb82…`) passed on `test (3.11)` and
`test (3.13)`: 54 passed on each. The CI log shows all four new tests as `PASSED`.

## Round-02 findings, and the owner's rule

Each break below is mine. I applied it with a one-off script, ran only the target test (with
`__pycache__` cleared and `PYTHONDONTWRITEBYTECODE=1`), and restored the file with
`git checkout`. At the end, `git status` was clean.

| # | item | status | my reproduction |
|---|---|---|---|
| 9 | a second `read --out` overwrote analyzed games | **resolved** | `Collection.write` (`collection.py:294-314`) skips a file when `analyzed_id(path) == item.id`. That is the same `analyzed_id` (`collection.py:218`) that the analysis skip uses (`analysis.py`, `analyzed_ids`), so the two cannot disagree. Break: delete the skip, and `test_library_analysis.py:101` goes red (analyses overwritten). The same break makes the CLI test go red at `test_cli.py:57`. |
| 10 | `FEN` header hashed as written | **resolved** (by the owner's rule) | `game_id` hashes `game.board().fen()`, and uses `""` when that is `chess.STARTING_FEN` (`collection.py:179-191`). Break: hash the raw `FEN` header again, and `test_collection.py:108` goes red. |
| 11 | the skip ignores engine and limit | **documented** | The README says to delete a file to redo it with other settings. |
| — | owner's rule: player names not part of the id | **implemented** | Break: add `White` back to the id, and `test_collection.py:93` goes red (aliases kept twice). |
| — | owner's rule: the date is part of the id for every length | **implemented** | Break: drop `Date` from the id, and `test_collection.py:100` goes red (different dates merged). |
| — | CLI read message | **new, tested** | Break: change the "already analyzed there, left as they are" wording, and `test_cli.py:57` goes red. |

**The rule's documentation.** I checked the module docstring (`collection.py:17-42`), the
`game_id` docstring, the README (`README.md:166-185`) and the PR body against the code. All of
them are accurate:

- A missing `Date` or `Result` header really does hash as python-chess's roster default,
  `????.??.??` and `*`. I verified that `read_game` fills the seven tag roster.
- The standard start is normalized, whether written as a `FEN` header or not.
- Dates and results are compared as written, with the stated consequences: partial or
  differently written dates are kept twice, and the same moves on the same day are merged.
- No reference to the old rule is left: a grep for `SHORT_GAME`, `20 half` and `lower case` in
  `pgn_postmortem/`, the README, `CLAUDE.md`, the tests and the PR body finds nothing.

**The read / analyze / read-again sequence**, which the coordinator asked about, run end to end
through the CLI on awkward games (`probe3.py` in my scratchpad). The games were one with no `Date`
or `Result` header, one set up from a non-standard `FEN` with an en-passant square that cannot be
used and a date written `2019.3.14`, and then one new game appended to the source:

```
read 1   : Wrote 2 game(s) to games.
analyze 1: Analyzed 2 game(s) into games; 0 already there.
ids back : True                      (ids re-read from the analyzed files equal the source ids)
read 2   : Wrote 1 game(s) to games; 2 already analyzed there, left as they are.
analyze 2: Analyzed 1 game(s) into games; 2 already there.
read 3   : Wrote 0 game(s) to games; 3 already analyzed there, left as they are.   (inputs: src and games itself)
analyze 3: Analyzed 0 game(s) into games; 3 already there.                         (--engine /nonexistent)
files: 3, all carrying PostmortemAnalysis
```

Ids survive the round trip through stripping and analysis, including the normalized `FEN` and the
placeholder date. The output directory can also be one of the inputs. No duplicate files appear.

## Findings

12. **non-blocking.** The owner's identity decision is recorded only in the PR body and in a
    docstring, and without the parts `PRINCIPLES.md` asks for.
    - **Evidence:**
      - The PR body: "**Owner decision, 2026-09-24 (during review round 02, relayed by the
        coordinator)**…".
      - `collection.py:17-18`: "the owner's decision of 2026-09-24".
    - `PRINCIPLES.md` (*Owner decisions*) asks for "a recommended default, the reason, and an
      owner-decision mark". The record has the mark and the date, but no default and no reason.
      It is also not in `ROADMAP.md` with F-1's other decided questions.
    - I cannot check the decision from the repository. I take it as the coordinator relayed it.
    - It is the owner's own decision, and the owner merges, so this does not hold the change. But
      the owner should confirm it and give it a durable record before or at merge. That record
      could be a decided item in F-1's open questions, or a line in the completion note, which
      may only transcribe it.

13. **non-blocking.** Changing the identity rule orphans analyzed output made under the old rule.
    - `analyzed_id` compares the stored `PostmortemId` with the id recomputed now. An output
      directory analyzed with an earlier revision of this branch (the spike rule) therefore has
      every game analyzed again, under a new file name, next to the old file.
    - Nothing has been released and `main` has no library, so only pre-merge trial runs are
      affected: delete them.
    - The id is now a storage key, though. Any future change to `game_id` will need a note or a
      migration. Worth one sentence in the module docstring for whoever touches it next (F-1.2
      onward).

14. **non-blocking.** This is pre-existing and was missed in round 01: file names are not
    zero-padded, so a directory listing is not always chronological.
    - `collection.py:74` claims "``<date>-<id>.pgn``, so a plain directory listing is
      chronological".
    - But `file_stem` (`collection.py:199`) keeps digit parts as written. A `Date` of `2019.3.14`
      gives `2019-3-14-<id>.pgn`, which sorts after `2019-12-01-…`. I reproduced this in
      `probe3.py`.
    - Padding with `zfill(2)` fixes it, or the docstring could be softened. Cosmetic.

No new defect was found in the fixes. Round-01 findings 1 and 3 to 8, and round-02 findings 9 to
11, stay resolved, and the full suite is green locally and in CI. Every F-1.1 done-when item is
still met by a test that asserts it (the round-01 table stands; the duplicate test,
`test_collection.py:66-72`, still passes under the new rule, because the two copies of the
fixture draw share their date).

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged by the owner on 2026-09-24 as `ccc0f89` (pull request #6); the clean round, 03, covers `a82bb82`. CI on the merge commit passed on Python 3.11 and 3.13: https://github.com/diegoami/pgn-postmortem/actions/runs/36005762329. F-1.1's done-when (`ROADMAP.md`, F-1's block):

- **The gates pass:** `ruff check .` is clean, and `pytest -q` gives 54 passed with none skipped, locally at `a82bb82`, on `main` after the merge, and in CI.
- **The new tests cover every item:**
  - reading a multi-game file whole
  - collecting files through a glob across directories
  - keeping only the player's games under any alias
  - keeping a game found in two files once (under the owner's identity rule of 2026-09-24: moves, result, date and a normalized start position)
  - stripping comments (a source `[%eval]` included), variations and NAGs
  - analyzing a forced mate and flagging it, with `[%eval]` output
  - analyzing nothing on a second run
  - the same output with two workers as with one
  - the command line run end to end as a subprocess

  All were checked in rounds 01–03, the reviewer breaking the code and watching them go red.
- **Every new assertion was shown failing first:** 84 breaks, each red on its intended assertion. The table is in the pull request body.
- **The Python 3.11+ move:** `pyproject.toml`, the CI matrix (3.11/3.13) and the gates table in `CLAUDE.md`.

Beyond the contract, from the reviews:
- two data-loss defects fixed: the skip treating stripped files as analyzed, and a re-read overwriting analyses
- literal paths containing glob characters
- a cp1252 fallback decoding
- a one-line error on engine failure
- a tested console script

Left open, to fix in a follow-up change: round-03 finding 14 (file-name dates aren't zero-padded, so a listing isn't always chronological). Finding 13 (a future change to the id rule orphans analyzed files) is noted for any such change. Finding 12 (the owner's identity decision) is recorded in the pull request body with its default and reason, and the owner's merge confirms it.

— Implementer, Claude Opus 5.5 (claude-opus-5-5)
