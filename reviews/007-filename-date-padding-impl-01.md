# Review 007: zero-padded dates in file names (round 01)

- **Revision covered:** `f9c034626241b1f70fb787f2abcec08091f28721` (branch
  `fix-filename-date-padding`, pull request #7).
- **Target proof:**
  - `git remote get-url origin` is `git@github.com:diegoami/pgn-postmortem.git`.
  - After `git fetch origin` and `git checkout --detach origin/fix-filename-date-padding`,
    `git rev-parse HEAD` gives `f9c0346…`. This equals `headRefOid` from
    `gh pr view 7 --json headRefOid,files`.
  - `git merge-base origin/main HEAD` is `1c51ac42fa478268a3c297722e5f2bccd94e6ac5`, which is also
    `origin/main`.
- **Files checked** (6). I got the list two ways and they are the same:
  `gh pr view 7 --json files` and `git diff --name-only 1c51ac4..f9c0346`.
  - `.gitignore`
  - `CLAUDE.md`
  - `pgn_postmortem/analysis.py`
  - `pgn_postmortem/collection.py`
  - `tests/test_collection.py`
  - `tests/test_library_analysis.py`
- **Commits:** `ba23ad2` (the padding and the `write` change), `f9c0346` (`.gitignore`).
  `git diff --stat` gives 102 insertions and 22 deletions across those six files. `scripts/`,
  `examples/`, `data/`, `README.md` and `pyproject.toml` are unchanged.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. I have
  not seen how the change was made. I treated the PR body and the commit messages as claims to
  check.
- **Mode:** Claude Code.
- **The defect:** finding 14 of `reviews/006-f1-1-read-and-analyze-impl-03.md`. `file_stem` kept
  the digits of the `Date` header as written, so `2019.3.14` gave `2019-3-14-<id>.pgn`. That name
  sorts after `2019-12-01-…`, although `CollectedGame.filename` says a plain listing is
  chronological.

## Gates, run by the reviewer

I used a fresh venv in my worktree (`python3 -m venv .venv`, `pip install -r requirements-dev.txt`,
`pip install -e .`). Stockfish is at `/usr/games/stockfish`, so no test was skipped.

```
$ .venv/bin/python -m ruff check .
All checks passed!
$ .venv/bin/python -m pytest -q -rs
56 passed in 4.27s
```

CI (`gh pr checks 7`, run 36006452981, `headSha` `f9c0346…`, conclusion `success`):
`test (3.11)` and `test (3.13)` pass with 56 passed each. The log shows both new tests as `PASSED`.
GitGuardian passes.

## The defect path

**Shown failing first.** I extracted the base (`git archive 1c51ac4`) into my scratchpad, copied in
the two new test files, and ran them against the unfixed code. I checked that the import resolved
to the scratch copy. Result: `2 failed, 20 passed`. The failures match the PR's fail-first item 1:

- `{'2019.3.14': '2019-3-14'} != {'2019.3.14': '2019-03-14'}`, and so on
- `'2019-3-14-cb596f7592.pgn' == '2019-03-14-cb596f7592.pgn'`

**My own breaks.** I applied each break to the PR head with a one-off script, ran the full suite,
and restored the file. `git status` was clean afterwards.

| # | break | result |
|---|---|---|
| 1 | `file_stem` unpadded again (the pre-fix line) | red: both new tests |
| 2 | pad the month only | red: `test_file_names_are_zero_padded_…` |
| 3 | pad the day only | red: both new tests |
| 4 | `write` goes back to the old own-file-name check, padding kept | red: `test_a_game_analyzed_under_an_unpadded_file_name_is_left_alone` (the gap the padding opens) |
| 5 | `write` never skips | red: the new test, `test_reading_again_into_an_analyzed_directory_keeps_the_analysis`, `test_cli.py::test_read_then_analyze_a_fixture_collection` |
| 6 | the analysis skip goes by file name | red: the new test and two existing analysis tests |
| 7 | `game_id` hashes the padded date instead of the header as written | **green, 56 passed** (finding 1) |
| 8 | undated games named `0000-00-00-<id>` (sort first) | red: `test_file_names_are_zero_padded_…` |

**The identity rule is unchanged.** `game_id` (`collection.py:180-192`) is not in the diff. It
still hashes `game.headers.get("Date", "")`. Only `file_stem` (`collection.py:195-204`) normalizes
the date. File names cannot collide: two copies whose dates differ only in padding have different
ids, so their names differ in the id part.

**The new `write` behaviour.** `write` now builds `done_ids = analyzed_ids(out_dir)` once and skips
any game in it (`collection.py:325-329`). The old check skipped a game when the file at its own
name held its analysis. That is a special case of the new check, so every game skipped before is
still skipped. `analyzed_ids` moved to `collection.py` unchanged, and `analysis.py` imports it, so
the read step and the analysis step share one test. The `write` docstring, the `filename` and
`file_stem` docstrings, and the `analysis` module docstring match the code.

**The old-name and new-name directory, reproduced end to end.** I ran the CLI (`probe_oldnew.sh` in
my scratchpad). "Old" is the package at `1c51ac4` and "new" is the PR head. The games are fixtures
written inline: `2019.3.14`, `2019.12.1`, and then `2019.5.2` appended to the source.

```
A: old read + old analyze (depth 6)
     2019-12-1-361837ba01.pgn  analyzed  be7e7242
     2019-3-14-cb596f7592.pgn  analyzed  932365e0
   new read     : Wrote 1 game(s) to A; 2 already analyzed there, left as they are.
   new analyze  : Analyzed 1 game(s) into A; 2 already there.
   new read (src and A itself) : Wrote 0 game(s) to A; 3 already analyzed there, left as they are.
   new analyze --engine /nonexistent : Analyzed 0 game(s) into A; 3 already there.
   files: 2019-05-02-96cfcf555d.pgn (analyzed), plus the two old files, byte-identical (md5)
   new read A   : kept 3, 0 duplicates
B: old read only (stripped), then new read + new analyze
     2019-03-14-cb596f7592.pgn  analyzed
     2019-3-14-cb596f7592.pgn   stripped, left over   (new read B: 1 duplicate, kept 1)
C: new read + new analyze, then the unfixed old write, side by side
     old read     : Wrote 1 game(s) to C.   (a second, stripped copy appears next to the analysis)
```

A game analyzed under an old name loses no data and gets no duplicate. The old code in C shows the
duplicate that the `write` change prevents. Scenario B is the leftover the PR declares under "Left
out" (finding 2).

**Nothing beyond what the PR states.** The diff has these parts:

- the padding
- the `write` skip, and the move of `analyzed_ids`
- the docstrings
- the two tests
- the `.gitignore` line (`.gitignore:9`)
- the `CLAUDE.md` "covers" cell (`CLAUDE.md:91`)

That cell adds two phrases: "file names with zero-padded dates that list in date order", and
"also under a file name from before the padding". Both describe the new tests accurately. The rest
of the row is unchanged. The PR's "What a passing check would have caught" is present and correct.

## Findings

1. **non-blocking.** No test pins the part of the identity rule that sits next to this change:
   dates compared as written.
   - `collection.py:36-37` says copies with "dates written differently (``2019.03.14`` and
     ``2019.3.14``)" are kept twice.
   - Break 7 made `game_id` hash the padded date. All 56 tests stayed green.
   - At this revision the rule is untouched. The diff shows it, and the PR's claim holds. But this
     change puts a date normalizer one function away from `game_id`, and the suite would not notice
     if a later change used it there. Such a change would also orphan every analyzed file (review
     006, finding 13).
   - This is a pre-existing gap, not a regression. A pair `2019.3.14` / `2019.03.14` asserted kept
     twice in `tests/test_collection.py` would close it. It is not required to fix finding 14.

2. **non-blocking.** A directory that holds only stripped copies under old names ends up with two
   files for one game. It lacks nothing.
   - Reproduced in scenario B: `2019-3-14-<id>.pgn` stripped next to `2019-03-14-<id>.pgn`
     analyzed.
   - The PR declares it under "Left out" ("Old stripped copies are left behind"). It loses no
     data. Reading the directory keeps one copy (1 duplicate, kept 1). It only affects trial
     output from before this change.
   - No action is needed beyond the PR's note. It is recorded here so the completion note can point
     to it.

3. **non-blocking, optional.** `.gitignore:9` ignores `.claude/worktrees/`, but the project slot's
   "paths to normally ignore" (`CLAUDE.md:73`) does not list it.
   - Agent worktrees are full copies of the repository.
   - `.claude/skills/publish-games/SKILL.md` is a path to inspect, so a search scoped to `.claude/`
     would descend into them.
   - This is a one-phrase addition if wanted. The change is fine without it.

The defect path is met. The fix lands the assertions that would have caught finding 14, and I saw
them fail on the unfixed code and under my own breaks. The identity rule is unchanged. The new
`write` behaviour loses no data and creates no duplicate file for analyzed games. The gates are
green locally and in CI.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
