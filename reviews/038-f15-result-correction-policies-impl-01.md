# Review 038: F-15, customizable, optional and documented result correction (round 1)

- **Revision covered:** `f2dd2e2cb0b38e8fccb07daf62385e03df173a0d` (branch `f15-result-correction-policies`)
- **Merge base:** `7f0fad99ea3d24e0c5c21e9cbd22d70207553234`
- **Files checked** (`git diff --name-only main...f15-result-correction-policies`, local; no remote
  pull request): `CLAUDE.md`, `PLAN.md`, `README.md`, `ROADMAP.md`,
  `design/004-result-correction-policies.md`, `docs/result-correction.md`, `pgn_postmortem/analysis.py`,
  `pgn_postmortem/cli.py`, `pgn_postmortem/collection.py`, `pgn_postmortem/results.py`,
  `pgn_postmortem/workspace.py`, `tests/fixtures/site/corrections/README.md`,
  `tests/test_result_correction.py`, `tests/test_result_docs.py`, `tests/test_result_policies.py`.
  The working tree held equal the named revision (clean).
- **Reviewer:** Claude Code fresh-context session (Claude Sonnet 5.5, `claude-sonnet-5-5`), same model
  family as the builder; no external process. Mode: Claude Code.
- **Claims reviewed:** ROADMAP F-15 block, PLAN iteration 12, `design/004-...`, the owner's decisions of
  2026-10-04.

## What was run

- Gates: `ruff check .` clean; `pytest -q` 421 passed; `node --test 'tests/js/*.test.mjs'` 32 pass, 0 fail.
- An independent script (not the implementation's tests): every original result (`1-0`, `0-1`,
  `1/2-1/2`, `*`, missing, `weird`) x every verdict kind (win, loss, level, forced mate, checkmate,
  stalemate, bare kings, no eval) x the four policies, through `decide_game` against a literal
  re-derivation of the design table: 0 mismatches; `OriginalResult` present exactly when `Result` differs
  from the source and equal to it; a second pass changes nothing; `all` then each policy gives the
  policy's own target (restore).
- Threshold edges per policy at exactly `win_percent(200)`, +1e-9 and -1e-9, both colours: win at and
  below, draw above; 54.9, 95.1, NaN, inf rejected.
- Identity: `PostmortemId`, file names and `game_id` unchanged by `Collection.correct_results` under every
  policy; on disk, `all`, `board`, `contradictions`, `unrecorded`, `all` in sequence: the restored/corrected
  counts are as the design says, and each repeat changes nothing.
- Skip: `header_skip` semantics (search not match, case sensitive, `(?i)`, missing header never matches,
  empty pattern matches any present header, `=` inside the regex kept, `=x`, `  =x`, `a`, `a=(` rejected);
  skip rule `Event=(` rejected by argparse (exit 2) with the directory byte-identical; a skip callable that
  raises on the third game propagates.
- CLI: bad policy (exit 2), bad rule (2), threshold 99 (1) with nothing written (directory hash equal);
  `--dry-run --explain` with two skip rules writes nothing and prints policy, rules, per-game reasons;
  `analyze --result-policy`/`--result-skip-header` without `--correct-results` exits 1 and creates no
  output directory; `--help` text matches behaviour.
- Workspace: a manifest without the keys builds a site byte-identical to `main`'s (`diff -r`); with
  `correct_results` the input directory hash is the same before and after the build; `result_threshold =
  nan` and a threshold without a policy are rejected before the output directory exists.
- F-13 and F-14: `git diff --stat` shows no change in `tests/golden/**` or `tests/test_workspace.py`, and
  the only change in an existing test is one added line in `tests/test_result_correction.py`.
- Mutations on a `git archive` copy, each making the relevant tests fail: skip call removed, restore's
  `OriginalResult` removal removed, `>=` to `>` at the threshold, source taken from the current `Result`,
  manifest skip dropped, manifest validation removed, analyze flag check removed, policy not passed at
  analysis time. One survivor (`and decided != original` in `contradictions`) is an equivalent mutant: the
  result is the same with it removed (a verdict equal to the source's gives `kept: agrees` or `restored`
  either way).
- Docs mechanism (scratch copy): changing a console example's output line, a `python tested` assert (twice)
  makes `tests/test_result_docs.py` fail. Changing a fence info string from `console tested` to
  `console  tested` (two spaces) makes seven examples silently stop running with the file still green (see
  finding 1).

## Findings

1. **non-blocking** `tests/test_result_docs.py:27` (`FENCE`) and `:56`
   (`test_the_docs_have_tested_examples_of_every_kind`): the mechanism can pass with examples not run. A fence
   typo (`console  tested`, `` ``` console tested ``, `Tested`) is not matched, so the block drops out of the
   parametrization, and the only guard is that each *kind* still appears once somewhere. Reproduced: with
   `^```console tested` replaced by two spaces in `docs/result-correction.md`, 13 tests became 6 and all
   passed. Failure scenario: a later edit mistypes a fence and the example rots unseen, the case the owner
   named a defect. Suggested fix: also fail when any fence line of the two documents contains the word
   `tested` and is not matched by `FENCE`, or assert the count of blocks per document. The same test also
   passes a console block with no `$` line or no expected output (vacuous by design: only the exit code is
   checked); an assertion that every console block has at least one expected line would close it. Not
   blocking because every current example is matched and mutations of the content fail.
2. **non-blocking** `docs/result-correction.md` (section "What is written, and how to undo it"): the
   undo text says `--policy board` after `all` "leaves only the board's corrections" and that the source's
   result "is in every game's `OriginalResult` header". The first is honest but the page does not say the
   corollary: no command undoes the board's own corrections or the `*` fills of a collection, so a full undo
   is not possible without copying `OriginalResult` back by hand or re-reading the source; the design records
   `--policy none` as out of scope but the page does not. The second is overstated: `OriginalResult` exists
   only on games whose result differs from the source (the same page says so two paragraphs earlier). Please
   say both plainly where a reader looks for how to undo.
3. **non-blocking** `pgn_postmortem/workspace.py:92-103` (`from_toml`): unknown keys in a `[[collection]]`
   table are silently ignored (pre-existing behaviour, now with consequences). A misspelled
   `result_skip_header = [...]` next to `correct_results = "all"` builds the site with the correction applied
   and without the skip the owner asked for; a misspelled `correct_result` silently means no correction (safe).
   Reproduced: `correct_result = "all"` builds without complaint. The design lists "unknown keys" in none of
   its checks, so this is not a claim failure; consider rejecting unknown keys in the correction family (keys
   starting with `result_` or `correct`) or all of them. Reproduced via the `workspace` command.
4. **non-blocking** `pgn_postmortem/results.py:358-364` (`correct_results`): a `skip` callable that raises
   propagates after the files before it have been rewritten (reproduced: raise on the third file, one file
   already changed on disk). The docstring and `design/004` say it propagates "before the file is written",
   which is per file. A rerun is idempotent, so no harm beyond a partial pass, but the docs could say that
   a failing skip leaves earlier files corrected.
5. **non-blocking** `design/004-result-correction-policies.md` ("Report", `GameDecision`): stale against the
   code. It lists `old` and `new` fields (the code has `result` and `verdict`) and says the idempotent
   second-run test "now compares its last line" while the test compares the whole output with the policy line
   first (`tests/test_result_correction.py:385`). The one-line edit of that F-14 test is justified (the
   deliberately changed report format is recorded in the design and in ROADMAP F-15's done-when) and the
   command's default output for a run now begins with a `Policy:` line, a visible change to F-14 users
   scripting against the output; the design states it, but the README does not.
6. **non-blocking** `pgn_postmortem/workspace.py:41,70` (`CollectionProfile`, `Workspace`) and the nearby
   methods have no docstring (pre-existing; the new fields have a comment, `WorkspaceReport` gained one).
   `docs/result-correction.md` first Python example names its skip function `level_and_recorded_decisive`
   but it skips by `Event`; rename it. `header_skip`, `POLICIES` and `check_policy` are importable from
   `pgn_postmortem.results` only, not from the package root; the docs use the right paths.

No blocking finding: every claim in ROADMAP F-15's done-when and in the CLAUDE.md gates-table edit (the
tests row; the claims checked against real tests: the literal-table matrix, exit codes 2 and 1, rejection
before writing, in-memory manifest, docs examples run with output asserted in order) held when run, and the
policy table matches the code for every combination I tried.

— Claude Code (Claude Sonnet 5.5, `claude-sonnet-5-5`), reviewer
No blocking finding remains.
