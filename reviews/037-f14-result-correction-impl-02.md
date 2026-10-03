# Review: F-14, correct the recorded result from the final position (implementation, round 2)

- **Revision covered:** `8fbb53ec2af7af9441435b42ac6386a698dd1a46` (branch `f14-result-correction`, head before this record).
- **Target check:** `git merge-base main HEAD` = `c90d68d04b967c51b87f099798511e5258d4e607`; `git diff --name-only <merge-base>..HEAD` lists 24 files: the 23 of round 1 plus `reviews/037-f14-result-correction-impl-01.md`. The held revision equals the named one; the tree was clean. Local diff, no remote thread. The round-1 fixes are in `49cb940..8fbb53e` (`analysis.py`, `cli.py`, `collection.py`, `results.py`, the tests, the design, README and CLAUDE.md).
- **Reviewer:** Claude Code, Sonnet 5.5 (`claude-sonnet-5-5`), a fresh-context session that did not see the implementation; same model family as the implementer (the default in `CLAUDE.md`). Mode: Claude Code.

## Gates, run on this revision

- `.venv/bin/python -m ruff check .`: all checks passed.
- `.venv/bin/python -m pytest -q`: 278 passed (no golden file changed in the branch's diff; F-5 tests unchanged and green).
- `node --test 'tests/js/*.test.mjs'`: run, no failure.

## Round 1 findings, each re-checked on a scratch copy (nothing on the branch changed)

1. **Source's own `OriginalResult` (blocking): fixed.** `strip_game` (`collection.py:249`) now drops `OriginalResult` from every game, and puts the source's `Result` back only for a game with marker and header. Mutation: restoring the old condition turns `test_a_source_games_own_original_result_never_reaches_its_analyzed_copy` red. That test covers the analyzed copy of such a source (no header, same id and file name as the plain source, one game read together with it, not taken as the original by `correct_results`).
2. **Reporting at analysis time (blocking): fixed.** `AnalysisReport.corrections` is filled from each worker's change (sorted by path) and `cmd_analyze` prints each line and a count. Mutations: not appending to the report turns `test_analysis_corrects_new_games_when_asked` red; removing the print in `cmd_analyze` turns the fake-engine test red. That test is not vacuous: it runs `analyze --correct-results` as a subprocess against a UCI engine written by the test, and flipping the engine's side turns it red (the written `Result` and the listed line depend on the engine's evals).
3. **Not-analyzed warning: fixed** (`results.py:223`); deleting it turns `test_a_file_that_is_not_analyzed_is_skipped_with_a_warning` red.
4. **`--result-threshold` without `--correct-results`: fixed** as an exit-1 usage error before the output directory exists (`cli.py`), and the library validates a given threshold whatever the flag; both mutations turn `test_a_result_threshold_without_correct_results_is_a_usage_error` red.
5. **Gates-table sentence: now true.** The fake-engine subprocess test exists and the sentence says what it asserts.
6. **"Only headers" test:** it does detect re-wrapping of a corrected file. Mutation: writing in `correct_results` with a 30-column exporter turns `test_the_file_changes_only_in_its_headers_and_a_second_run_changes_nothing` red. (Caveat, not a finding: the test's input is itself written by `format_game`, so it guards `correct_results`' writer, not hand-wrapped input; the design says so in "Files and floats".)
7. **Float edge:** recorded in `design/003-result-correction.md` ("Known limitation, inherited from F-5"), not changed. Fine.

## New findings

None blocking. Looked for and not found: an identity change in any read path (stripped read, `keep_analysis=True`, source and analyzed copy read together in either order, `Collection.write` over an analyzed directory, a rerun at another threshold), a partial file left behind, a test that asserts nothing, or a claim in the design or the gates table without a test. The F-14 text in `CLAUDE.md` matches the tests I ran.

1. **non-blocking, legacy input:** an analyzed file written before this fix from a source that carried its own `OriginalResult` still holds the header with the marker and is believed (`source_result`, `collection.py:197`). Only files produced by the unfixed intermediate commits can be like this; no released version wrote them. No action needed beyond knowing it.

## Verdict

No blocking finding remains.

— Claude Code (Sonnet 5.5, `claude-sonnet-5-5`), reviewer
No blocking finding remains.
