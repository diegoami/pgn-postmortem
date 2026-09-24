# Review 006: F-1.1, read and analyze (round 02)

- **Revision covered:** `cbe3b31b530ce9d8810bf33d80700194e41838b0` (branch
  `iteration-1-read-and-analyze`, pull request #6). Round 01 covered `e2735891…`.
- **Target proof:**
  - After `git fetch origin` and `git checkout --detach origin/iteration-1-read-and-analyze`,
    `git rev-parse HEAD` gives `cbe3b31…`. This matches `gh pr view 6 --json headRefOid`.
  - `git merge-base origin/main HEAD` is `3850530508de72da436b4de69ce143cc1c65e8a0`, which is
    also `origin/main`.
- **Files checked** (16). I got the list two ways and compared them with `diff`; they are the
  same: `gh pr view 6 --json files` and `git diff --name-only 3850530..cbe3b31`.
  - The 15 files of round 01, plus `reviews/006-f1-1-read-and-analyze-impl-01.md`.
- **Commits since round 01:**
  - `edd55e5` records the round-01 review. `git show HEAD:reviews/006-f1-1-read-and-analyze-impl-01.md`
    is byte-identical to the file I wrote (checked with `cmp`).
  - The fixes: `7a9b343` (finding 1), `49f13bf` (3), `8d6455d` (4), `99abad7` (5),
    `ec452d6` (6 and 8), and `cbe3b31` (2 and 7).
  - `git diff --stat e273589..cbe3b31` touches `CLAUDE.md`, `README.md`, `pgn_postmortem/`
    (`__init__`, `analysis`, `cli`, `collection`), the three test files, and the review file.
    `pyproject.toml`, `scripts/`, `examples/` and `data/` are unchanged.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. This
  round continues the round-01 reviewer session (`PRINCIPLES.md`, *Reviewer sessions*). I
  re-read the current code and did not rely on the PR's "Answer to review round 01".
- **Mode:** Claude Code.

## Gates, run by the reviewer

I reinstalled the package with `pip install -e .` in the worktree's venv (Python 3.12.3,
Stockfish 16) and cleared `__pycache__`.

```
$ .venv/bin/python -m ruff check .
All checks passed!
$ .venv/bin/python -m pytest -q -rs
50 passed in 3.10s        (nothing skipped)
```

CI (`gh pr checks 6`, run 36001350089, `headSha` `cbe3b31…`) passed on `test (3.11)` and
`test (3.13)`: 50 passed on each. The CI log shows all six new tests as `PASSED`, including the
console-script test and the Stockfish tests.

## Round-01 findings

Each break below is mine. I applied it with a one-off script, ran only the target test (with
`__pycache__` cleared and `PYTHONDONTWRITEBYTECODE=1`), and restored the file with
`git checkout`. At the end, `git status` was clean.

| # | round-01 finding | status | my reproduction |
|---|---|---|---|
| 1 | incremental skip took stripped files as analyzed | **resolved** | `analyzed_ids` (`analysis.py:207-217`) now needs both `PostmortemId` and the new `PostmortemAnalysis` header, which only `analyze_game` writes and reading strips (`DROPPED_HEADERS`). Break: accept `PostmortemId` alone, and the test goes red at `test_library_analysis.py:81`. Break: stop dropping the marker, and it goes red at `:88`. Break: stop writing the marker, and the second-run tripwire goes red at `:65`. See new finding 9 for a gap that remains in the in-place workflow. |
| 2 | duplicate rule | **documented**, as the coordinator instructed; now an owner decision | The docstring (`collection.py:17-32`) and the README (`README.md:171-175`) match `game_id`, with one inaccuracy: new finding 10. |
| 3 | literal path with glob characters | **resolved** | An existing path is now taken literally (`collection.py`, `if GLOB_CHARS & set(text) and not path.exists()`). Break: restore the glob-first check, and it goes red at `test_collection.py:43`. |
| 4 | Latin-1 fallback | **resolved** (Windows-1252, then Latin-1). Decoding stays per file, and the docstring now says so. | Break: drop `cp1252`, and it goes red at `test_collection.py:97`. Break: drop the Latin-1 last resort (`cp1252` with `errors="replace"`), and it goes red at `:101`. Python's `cp1252` codec does reject 0x81, 0x8D, 0x8F, 0x90 and 0x9D, so the "five bytes" claim is right. |
| 5 | engine failures: traceback, and slow failure | **resolved** | `EngineFailure` wraps start-up errors (`analysis.py:274`) and errors during a game (`:257`), and the CLI prints them as one `error:` line. Queued games are cancelled (`:289`). Break: `shutdown(wait=True)` without `cancel_futures`, and it goes red at `test_library_analysis.py:129` (about 9.6 s: all 20 stand-in games ran). Break: remove the per-game wrap, and it goes red at `:127`. Break: remove the start-up wrap, and it goes red at `test_cli.py:65`. |
| 6 | mating move's missing eval not asserted | **resolved** | Break: write `[%eval #0]` on the mating move, and it goes red at `test_library_analysis.py:54`. |
| 7 | additions, README, harness text | **resolved** | The README names both headers. The `CLAUDE.md` gates-table row now also lists the new tests. It is accurate, and consistent with `ci.yml`. |
| 8 | console script not tested | **resolved** | Break: `main` returns 0 on error, and it goes red at `test_cli.py:81`. The test is skipped only when the script is not installed next to the interpreter. The gates install it, and CI ran it. |

**Fail-fast test (finding 5).** It uses a stand-in engine and `time.sleep(0.5)`, and asserts only
an upper bound (`len(started) <= 2`). Timing can only make it pass more easily, so it will not
flake red. With the fix removed it goes red, as shown above.

## New findings

9. **blocking.** In the in-place workflow the README now describes, a second `read --out` throws
   away the analysis already done.
   - **Evidence:**
     - `README.md:168-169`: "`analyze` skips a game when a file in its output directory carries
       that game's id and this header, so games that `read --out` only stripped are still
       analyzed, even in the same directory."
     - `collection.py:277-284`: `Collection.write` overwrites any existing
       `out_dir/<date>-<id>.pgn` with the stripped game (`path.write_text(...)`). That includes a
       file the analysis step wrote there.
   - **Reproduction** (`Collection.read(fixtures).write(games)`, then
     `Collection.read(games).analyze(games, depth=6)`, then the same two steps again):
     - Run 1: 4 analyzed, 0 skipped.
     - After the second read: 0 files with `[%eval`, so every analyzed game was replaced by its
       stripped copy.
     - Run 2: 4 analyzed, 0 skipped.
     - With separate directories (the README's own example), the second pass analyzes nothing
       (`(0, 4)`), as intended.
   - **Why it matters:** "read, then analyze in place" is a normal way to add new games to an
     archive, and the round-01 answer makes it a supported use. On the owner's roughly 1,800 games,
     it silently discards hours of Stockfish work on every refresh. That contradicts F-1's "a game
     the library has already analyzed (in its own output) is not analyzed again". The finding-1
     fix made in-place analysis work, and this is the half it left open.
   - **Suggested fix:** `Collection.write` should not overwrite a file that carries the analysis
     marker for the same `PostmortemId`. It could leave it, or it could skip every existing file
     and report the count. Add the assertion that would have caught this: read into a directory,
     analyze in place, read into it again, and expect the second `analyze` to report
     `(0, n)` with the `[%eval` files intact.
   - Documenting that `read --out` must never target an analysis directory would also close the
     contract gap, but it keeps a silent data-loss trap. The fix above is one condition and one
     test.

10. **non-blocking.** The duplicate-rule documentation says "start position", but the id uses the
    `FEN` header text.
    - **Evidence:**
      - `collection.py:18-19`: "the SHA-1 of the ``FEN`` header (empty for the standard start)".
      - `README.md:171`: "Two copies of a game count as one when they have the same start
        position, result and moves."
    - The code (`headers.get("FEN", "")`) hashes the header *as written*: it is empty only when
      there is no `FEN` header.
    - Reproduction: the same 20-ply game, once without a `FEN` header and once with
      `[SetUp "1"]` and `[FEN "<standard start>"]`, gets two ids (`b58d2b39d9` and
      `d2976456a0`), although `a.board() == b.board()`. The two copies are kept twice.
    - This is only an accuracy fix, not a rule change (the rule is the owner's decision). Say
      "the `FEN` header as written (empty when there is none)", and add this case to the list of
      what follows from the rule. Neither text mentions that the lower-cased names are not
      whitespace-trimmed either, but that is minor.

11. **non-blocking.** An observation on the marker header: `PostmortemAnalysis` records the engine
    and the limit, for example `Stockfish 16, depth 18`, but the skip ignores it.
    - A rerun with a deeper search, or a newer engine, skips every game.
    - That matches F-1's contract ("incremental only in that a game the library has already
      analyzed … is not analyzed again"), so there is nothing to fix. It may be worth one README
      sentence: delete a file to redo it. The PR body already says there is no `--force`.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
One blocking finding remains (finding 9: a repeated `read --out` into an analysis directory overwrites analyzed games, so the in-place workflow is not incremental).
