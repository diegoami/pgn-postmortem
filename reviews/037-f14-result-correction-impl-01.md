# Review: F-14, correct the recorded result from the final position (implementation, round 1)

- **Revision covered:** `527351331b35cd28d11daab6c17b1d53a5894f26` (branch `f14-result-correction`, head before this record).
- **Target check:** `git merge-base main HEAD` = `c90d68d04b967c51b87f099798511e5258d4e607`; `git diff --name-only <merge-base>..HEAD` lists 23 files: `CLAUDE.md`, `PLAN.md`, `README.md`, `ROADMAP.md`, `design/003-result-correction.md`, `pgn_postmortem/{__init__,analysis,cli,collection,results,site}.py`, `tests/test_result_correction.py` and `tests/fixtures/site/corrections/` (README plus 10 PGNs). The held revision equals the named one; the tree was clean. No local remote review thread was used (local diff).
- **Reviewer:** Claude Code, Sonnet 5.5 (`claude-sonnet-5-5`), a fresh-context session that did not see the implementation; same model family as the implementer (the default in `CLAUDE.md`). Mode: Claude Code.
- **Claims reviewed:** ROADMAP F-14's scope, done-when and the four owner decisions of 2026-10-03; `design/003-result-correction.md`; the F-14 text added to the gates table in `CLAUDE.md`.

## Gates, run on this revision

- `.venv/bin/python -m ruff check .`: all checks passed.
- `.venv/bin/python -m pytest -q`: 274 passed (Stockfish tests skipped or run as the machine allows; none run by me explicitly).
- `node --test 'tests/js/*.test.mjs'`: 32 pass, 0 fail.

## What I tried, and what held

Run against a scratch copy of the fixtures (nothing in the repository changed):

- `correct-results --dry-run`: lists 7 changes, writes nothing (`diff -r` clean). Thresholds 54, 96, `nan`: exit 1 with the message, no file touched; `abc`: argparse exit 2; missing directory: exit 1.
- Real run: 7 files changed, 1 agrees, 1 no verdict, 1 not analyzed. `agrees`, `no-final-eval` and `not-analyzed` are byte-identical afterwards. No `.partial` files remain. A second run changes 0 games and writes nothing.
- Rerun at 80 then at 70: a verdict equal to the source's value gives `restored` and removes `OriginalResult`; otherwise `OriginalResult` keeps the first original, never a corrected value.
- Site built from a corrected directory: "Source result" row and the conclusion sentence appear (also for an unrecorded source: "Not recorded", "no result"); the identity tests (`PostmortemId`, file name, duplicate with the unanalyzed source, stripped read restoring `Result`) pass.
- `analyze --correct-results --result-threshold 40`: exit 1 before the engine and before the output directory is created.
- Mutations on a scratch copy (not the branch): `source_result` believing `OriginalResult` without the marker, `source_result` ignoring it, and `>=` changed to `>` at the threshold each turn `tests/test_result_correction.py` red on an assertion written for it.

## Findings

1. **blocking, identity: a source game's own `OriginalResult` is believed once the game is analyzed.** The design says a source with its own `OriginalResult` "is not touched or believed" so that "a stripped source copy must keep hashing its `Result`", and the test `test_an_original_result_header_of_a_source_game_is_not_believed` asserts only the unanalyzed read. But `strip_game` (`pgn_postmortem/collection.py:245`) drops `OriginalResult` only when the game carries the marker, so a stripped source keeps the header, `analyze_game` copies it (`pgn_postmortem/analysis.py:158`, `out.headers = source.headers.copy()`) and adds the marker, and `source_result` (`collection.py:197`) then believes it. Reproduced: a PGN with `Result "0-1"` and `OriginalResult "1-0"` has id `1a2d3eecb2` read as a source; the same game with the marker added and `PostmortemId` set (what the analysis step writes) recomputes to `5a2319df9b` under `keep_analysis=True`, and reading source and analyzed copy together gives 2 games, not 1 (a duplicate in the site and an analysis redone). `correct_results` would also take the bogus value as the source's. This breaks the owner's "identity must not change" for any input that already carries the header, and the design's stated invariant. Fix: drop `OriginalResult` from a game without the marker when reading it as a source (or in `analyze_game`), and add the assertion for an analyzed copy of such a source (id equal to the source's, one game when read together).
2. **blocking, reporting at analysis time.** The scope says the correction "reports every change (counts, and each game's old and new result)" and the caveat says it "always preserves and reports the original". At analysis time `correct_game`'s result is discarded (`pgn_postmortem/analysis.py:266`), `AnalysisReport` carries nothing, and `cmd_analyze` prints only `Analyzed N game(s)...` (`pgn_postmortem/cli.py:99`). A user of `analyze --correct-results` is never told which results were rewritten (the original is preserved in the file, but nothing lists the changes). Fix: collect the `ResultChange`s into `AnalysisReport` and print them in the command, with a test.
3. **non-blocking: a file that is not analyzed is skipped without the warning the design promises.** `design/003-result-correction.md` and the `correct_results` docstring say a file that is not analyzed, has several games or does not parse is skipped "with a warning"; `pgn_postmortem/results.py:221-223` counts the not-analyzed file as skipped with no warning (only the unparseable and multi-game cases warn, `results.py:219`). The gates-table text says only "several games or none", which is true. Make the prose match the code, or warn.
4. **non-blocking: `analyze --result-threshold` without `--correct-results` is neither validated nor reported** (`pgn_postmortem/analysis.py:241`, validated only when the flag is on): `--result-threshold 40` alone exits through the engine path as if valid. A usage error would be kinder.
5. **non-blocking: the gates-table sentence "the `correct-results` and `analyze` flags as subprocesses"** is true for the rejection of a bad threshold only (`tests/test_result_correction.py`, `test_the_command_line_rejects_a_bad_threshold_before_writing`); no test runs `analyze --correct-results` to success through the command line (the engine is stubbed only in the library tests). Say so, or add it with a stub.
6. **non-blocking: a corrected file is re-exported whole** (`format_game`, `results.py:225`), so a hand-written file's movetext line wrapping can change as well as its headers; `test_the_file_changes_only_in_its_headers...` compares line sets and would not notice. Harmless for the library's own output (already wrapped by `format_game`), but the test name and the design say "only headers".
7. **non-blocking, inherited from F-5 and unchanged:** the black-side edge `100 - white >= threshold` (`results.py:100`) can miss by a floating-point ulp for some centipawn values (about 16 of 430 sampled values where the stated threshold was computed as `100 - win_percent(cp)`); the tests use `win_percent(275)` for both sides and pass. Out of scope for F-14; noted for the owner.

The design record's claims, the README text and the CLAUDE.md gates text were each checked against the code and the tests; apart from items 3 and 5 they are true, and each claimed test exists and asserts what it says (item 1 aside, which is a missing assertion rather than a false one).

## Verdict

Blocking findings remain: 1 and 2. Fix them in the same change and request round 2.

— Claude Code (Sonnet 5.5, `claude-sonnet-5-5`), reviewer
Blocking findings remain (items 1 and 2).
