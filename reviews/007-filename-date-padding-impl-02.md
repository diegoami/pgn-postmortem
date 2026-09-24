# Review 007: zero-padded dates in file names (round 02)

- **Revision covered:** `263d4c431e412a82a934b350647dbc4b6b064c51` (branch
  `fix-filename-date-padding`, pull request #7). Round 01 covered `f9c0346…`.
- **Target proof:**
  - After `git fetch origin` and `git checkout --detach origin/fix-filename-date-padding`,
    `git rev-parse HEAD` gives `263d4c4…`. This equals `headRefOid` from
    `gh pr view 7 --json headRefOid,files`.
  - `git merge-base origin/main HEAD` is `1c51ac42fa478268a3c297722e5f2bccd94e6ac5`, which is still
    `origin/main`.
- **Files checked** (7). I got the list two ways and they are the same:
  `gh pr view 7 --json files` and `git diff --name-only 1c51ac4..263d4c4`.
  - The six files of round 01.
  - `reviews/007-filename-date-padding-impl-01.md`.
- **Commits since round 01** (`git log f9c0346..263d4c4`):
  - `b0f0546` records the round-01 review. The committed file is byte-identical to the file I wrote
    (checked with `cmp` against my scratchpad copy).
  - `6e6a9a5` adds the date-identity test (finding 1). It touches `tests/test_collection.py` only,
    13 lines added.
  - `263d4c4` adds the ignore-list line (finding 3). It touches `CLAUDE.md` only, 2 lines added and
    1 deleted.
  - `git diff f9c0346..263d4c4 -- . ':!reviews'` shows those two hunks and nothing else. The code
    (`pgn_postmortem/`) is the same as in round 01.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. This
  round continues the round-01 reviewer session (`PRINCIPLES.md`, *Reviewer sessions*). I re-read
  the current diff, and did not rely on the PR's "Answer to review round 01".
- **Mode:** Claude Code.

## Gates, run by the reviewer

I used the same fresh venv as in round 01, with the package installed editable from this worktree.
Stockfish is at `/usr/games/stockfish`, so no test was skipped.

```
$ .venv/bin/python -m ruff check .
All checks passed!
$ .venv/bin/python -m pytest -q -rs
57 passed in 4.60s
```

CI (`gh pr checks 7`, run 36009406145, `headSha` `263d4c4…`, conclusion `success`):
`test (3.11)` and `test (3.13)` pass with 57 passed each. The log shows
`test_dates_written_differently_are_two_games_with_the_same_padded_file_date PASSED`.
GitGuardian passes.

## Round-01 findings

| # | status | evidence |
|---|---|---|
| 1 | **resolved** | `tests/test_collection.py:103-113`, details below. |
| 2 | **left as is**, on the owner's call | Still declared under the PR's "Left out" ("Old stripped copies are left behind"). The code is unchanged, so my round-01 reproduction (scenario B) stands. |
| 3 | **resolved** | `CLAUDE.md:78-79` adds `.claude/worktrees/` to the slot's "paths to normally ignore", with a reason. |

**Finding 1, reproduced.** The new test reads the same moves and result dated `2019.3.14` and
`2019.03.14`. It asserts three things:

- kept 2, 0 duplicates
- two different ids
- both file names are `2019-03-14-<id>.pgn`

I applied each break with my one-off script, ran the full suite, and restored the file.
`git status` was clean afterwards.

| break | result |
|---|---|
| `game_id` hashes the padded date through `file_stem` (my round-01 break 7) | `1 failed, 56 passed`: only the new test |
| `game_id` hashes the `zfill`-padded header (the PR's fail-first item 5) | `1 failed, 56 passed`: only the new test. The failing line is `assert (collection.report.kept, collection.report.duplicates) == (2, 0)`, with `E assert (1, 1) == (2, 0)`, as the PR shows. |
| `game_id` strips leading zeros from each date part (the opposite normalization) | `1 failed, 56 passed`: only the new test |
| `file_stem` unpadded again | red: the new test (its file-name assertion), and the two round-01 tests |

The test pins the rule as the owner stated it and as `collection.py:36-37` documents it. It goes
red on its intended assertion under normalization in either direction. It adds no fixture file and
changes no existing assertion.

**Finding 3, checked.** The edit adds one phrase at the end of the ignore list:
"`.claude/worktrees/` (agent worktrees: full copies of the repository, git-ignored)". Each part is
accurate:

- `.gitignore:9` ignores it.
- My own worktree sits there, and it is a full checkout.

It follows the list's existing "path (reason)" pattern. Nothing else in `CLAUDE.md` changed in this
round. Ignoring the path when reading does not conflict with the `PRINCIPLES.md` habit ("ignoring
a path never means deleting or gitignoring it"). The gitignore is a separate, stated part of the
change, and it has its own reason.

## Anything new

- The PR body now matches the head:
  - It says 57 tests, 54 plus 3 new.
  - It adds a done-when item for the new test, and extends the `.gitignore` item to the `CLAUDE.md`
    line.
  - Its fail-first item 5 matches what I reproduced.
  - The "Answer to review round 01" list matches the commits.
- The gates-table "covers" cell (`CLAUDE.md:91`) does not name the new test. It already covers it
  under "duplicates kept once by the owner's identity rule", as it does the older
  `…_on_different_dates_are_kept_twice`, so I raise no finding.
- No other change to code, tests or harness text since round 01.

## Findings

None.

Round-01 finding 1 is resolved, finding 3 is resolved, and finding 2 stays declared under "Left
out" on the owner's call. The defect path for review 006, finding 14 is met, as established in
round 01, and the code has not changed since. The gates are green locally and in CI at `263d4c4`.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
