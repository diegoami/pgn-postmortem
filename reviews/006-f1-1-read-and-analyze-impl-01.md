# Review 006: F-1.1, read and analyze (round 01)

- **Revision covered:** `e2735891147cd29e3f305f6451246e2abdd23c56` (branch
  `iteration-1-read-and-analyze`, pull request #6). The base is `main` at
  `3850530508de72da436b4de69ce143cc1c65e8a0`.
- **Target proof:**
  - `git remote get-url origin` gives `git@github.com:diegoami/pgn-postmortem.git`.
  - After `git fetch origin` and `git checkout --detach origin/iteration-1-read-and-analyze`,
    `git rev-parse HEAD` gives `e2735891…`. This matches `gh pr view 6 --json headRefOid`.
  - `git merge-base origin/main HEAD` is `3850530…`, which is also `origin/main`.
  - The branch has four commits: `b3bb74a`, `99fb892`, `87c4458` and `e273589`.
- **Files checked** (15). I got the list two ways, and they agree: `gh pr view 6 --json files`
  and `git diff --name-only 3850530..e273589`.
  - `.github/workflows/ci.yml`
  - `.gitignore`
  - `CLAUDE.md`
  - `README.md`
  - `pgn_postmortem/__init__.py`
  - `pgn_postmortem/__main__.py`
  - `pgn_postmortem/analysis.py`
  - `pgn_postmortem/cli.py`
  - `pgn_postmortem/collection.py`
  - `pyproject.toml`
  - `tests/fixtures/collection/club/2019.pgn`
  - `tests/fixtures/collection/online/2020/games.pgn`
  - `tests/test_cli.py`
  - `tests/test_collection.py`
  - `tests/test_library_analysis.py`
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. It has
  not seen how the change was made.
- **Mode:** Claude Code.
- **Rules applied:** from `origin/main`: `PRINCIPLES.md`, the `CLAUDE.md` slot, `ROADMAP.md`
  (F-1, the F-1.1 row, the out-of-scope list, and open questions 1, 3, 5 and 6 as decided),
  `PLAN.md` iteration 1, and `reviews/README.md`.

## Gates, run by the reviewer

I made a fresh `.venv` in the worktree with Python 3.12.3, then ran
`pip install -r requirements-dev.txt` and `pip install -e .`. Stockfish 16 is at
`/usr/games/stockfish`.

```
$ .venv/bin/python -m ruff check .
All checks passed!
$ .venv/bin/python -m pytest -q
44 passed in 2.47s        (-rs: nothing skipped)
```

CI (`gh pr checks 6`, run 35999606119, head `e273589`) passed on `test (3.11)` and
`test (3.13)`. The CI log shows the new Stockfish and CLI tests as `PASSED`, not skipped. Python
3.11 and 3.13 are not installed on this machine, so CI is the only evidence for those versions.

## The contract (the F-1.1 "done when" column)

For each item, I read the test itself, not just its name.

| done-when item | test | does it assert the item? |
|---|---|---|
| read a multi-game file whole | `test_collection.py:24-27` | yes: `report.read == 3`, and the three White names in order |
| collect files through a glob across directories | `test_collection.py:30-33` | yes: `**/*.pgn` gives both files, and the games come from both |
| keep only the player's games under any alias | `test_collection.py:47-55` | yes: all three names, `AdaEx` matched with a different case, and `not_player == 1` |
| keep a game found in two files once | `test_collection.py:58-64` | yes. The two copies differ in `Event` and `Round` and in their annotations, so the check is on content |
| strip comments (a source `[%eval]` included), variations and NAGs | `test_collection.py:67-78` | yes. It first checks that the fixture carries them, then checks every node |
| analyze a forced mate and flag it with `[%eval]` output | `test_library_analysis.py:120-140` | yes: `$4`, the comment exactly `[%eval #1]`, and both engine lines |
| analyze nothing on a second run | `test_library_analysis.py:143-157` | yes. The second run gets a nonexistent engine as a tripwire, and the test checks the counts and that the mtimes did not change |
| the same output with two workers as with one | `test_library_analysis.py:160-167` | yes: the two output directories are equal byte for byte |
| the command line end to end as a subprocess (read, then analyze) | `test_cli.py:193-216` | yes: two `python -m pgn_postmortem` processes, then a third, incremental run |
| Python 3.11+ in `pyproject.toml`, the CI matrix and the gates table | `pyproject.toml` (`requires-python = ">=3.11"`, `py311`), `ci.yml:13` (`["3.11", "3.13"]`), `CLAUDE.md:91` | yes. All three agree, and so do the README badge and Quickstart |

**Scope checks:**

- `git diff --stat 3850530..HEAD -- scripts examples data` is empty, so the scripts, the examples,
  the data and the golden files did not change.
- There is no fetching, no `toml` or config, and no network code in `pgn_postmortem/` (a grep for
  `toml|urllib|http|requests|chess.com|lichess` finds only the lichess threshold names).
- Nothing contradicts the decided list:
  - Every game is re-analyzed. `analyze_game` rebuilds the game from the headers and the mainline
    only.
  - Source annotations are stripped.
  - Moves are graded by win % with 10/20/30.
  - The output is standard `[%eval]` (`node.set_eval`, `analysis.py:167`).
- What the PR reuses from the spike matches `origin/book-poc:pgn_postmortem/ingest.py`:
  `game_id`, `SHORT_GAME_PLIES` and `DROPPED_HEADERS` are the same code. The spike's
  `PostmortemSource` header and its config and sources code were left out, as open question 5
  decided.

## Reproduction: breaks I applied myself

I applied each break to the code with a one-off script and ran only the target test, with
`__pycache__` cleared and `PYTHONDONTWRITEBYTECODE=1`. Then I restored the file with
`git checkout -- <file>`. At the end, `git status` was clean.

| # | break | result |
|---|---|---|
| R1 | `engine.analyse(position, limit)`, without `game=` (no per-game `ucinewgame`) | red at `test_library_analysis.py:76` (`one == two`); the Scholar's-mate game's "better was" line differs. **Red 6 of 6 times.** The unbroken test is green 8 of 8 times |
| R2 | `game_id` also hashes `Event` | red at `test_collection.py:61` (`assert 2 == 1`) |
| R3 | `strip_game` copies each source node's NAGs | red at `test_collection.py:75` (`all(not node.nags …)`) |
| R4 | player names compared without `casefold()` | red at `test_collection.py:50` (only the `AdaEx` game is kept) |
| R5 | incremental skip off (`todo = list(games)`) | red at `test_library_analysis.py:60` (the tripwire: `Stockfish not found at /nonexistent/stockfish`) |
| R6 | the old `{ +0.23 }` comment in place of `set_eval` | red at `test_library_analysis.py:42` (`'+999.99' == '[%eval #1]'`) |
| R7 | `iter_games` stops after the first game | red at `test_collection.py:26` (`1 == 3`) |
| R8 | `glob(..., recursive=False)` | red at `test_collection.py:31` |
| R9 | `cmd_analyze` returns before printing its summary | red at `test_cli.py:39` |

Every break went red on the line written for it. The PR's claim that "the parallel output depends
on `ucinewgame`" is reproduced, and so is the claim that the test catches it.

## Findings

1. **blocking.** The incremental skip treats any file with a library-style name as analyzed,
   including the stripped, unanalyzed files that `read --out` writes.
   - **Evidence:**
     - `analysis.py:185-188`: `return {path.stem.rsplit("-", 1)[-1] for path in out_dir.glob("*.pgn")}`.
     - `analysis.py:215`: `todo = [g for g in games if g.id not in done_ids]`.
     - `read --out` (`collection.py:245-254`) and `analyze --out` write the same
       `<date>-<id>.pgn` names.
   - **Reproduction:**
     - Run `pgn-postmortem read tests/fixtures/collection --out games`.
     - Then run `pgn-postmortem analyze games --out games --depth 6`. It exits 0 and prints
       `Analyzed 0 game(s) into games; 4 already there.`
     - Not one file in `games/` contains `[%eval`.
     - The same happens through the API: `Collection.read(d).write(d)`, then `.analyze(d)`.
   - **Why it matters:** "analyze in place" is a natural way to use the tool, and here it silently
     produces nothing while reporting success. F-1's scope says the step "is incremental only in
     that a game the library has already analyzed (in its own output) is not analyzed again". A
     game that was only stripped has not been analyzed.
   - **Suggested fix:** decide "already analyzed" from something only the analysis step writes.
     That could be an analysis header, or the presence of `[%eval` in the file. Or refuse an
     output directory that is also an input. Either way, add the assertion that would have caught
     this: read into a directory, analyze into the same directory, and expect the games analyzed.

2. **non-blocking.** Duplicate detection can merge two different games, and can keep one game
   twice.
   - `collection.py:34, 143-152`: from 20 plies on, the id is only FEN, result and moves. Two
     different games with the same moves and the same result are therefore one game.
     - Reproduction: two games, 2015 against "Opponent One" and 2021 against "Opponent Two", with
       the same 22-ply Berlin line drawn. `Collection.read` keeps 1 of them and counts the other
       as a duplicate.
     - Repeated theoretical draws and repeated traps do happen in an online archive of about
       1,800 games. F-1 says "all games must be there".
   - The opposite case, for games under 20 plies: the id hashes the player names in lower case,
     so the same short game exported once as "Ada Example" and once as "adaex" is kept twice
     (reproduced).
   - The heuristic is the spike's, reused by owner decision (open question 5), so this is not a
     contract breach. I recommend either:
     - including the date whenever it is complete, and matching the player through the alias set
       rather than the raw name; or
     - recording the limitation, for example in the module docstring or the README, and raising it
       with the owner.

3. **non-blocking.** A literal file name that contains `[`, `*` or `?` is always treated as a glob
   pattern.
   - `collection.py:96`: `if GLOB_CHARS & set(text):`.
   - Reproduction: an existing `lit/games [2019].pgn` gives
     `FileNotFoundError: no file matches lit/games [2019].pgn`.
   - Suggested fix: check `Path(text).exists()` before treating the input as a pattern.

4. **non-blocking.** The encoding fallback decides once per file, and it uses Latin-1 rather than
   cp1252.
   - `collection.py:116-124`.
   - A file that mixes UTF-8 and Latin-1 games (concatenated collections) is decoded wholly as
     Latin-1, so the UTF-8 games come out as mojibake. Reproduced: `['JÃ¼rgen', 'Müller']`.
   - A Windows-era file with curly quotes gives C1 control characters. Reproduced:
     `'Café \x93Open\x94'`.
   - cp1252, with Latin-1 as a last resort, would be closer to the docstring's "old Windows-era
     collections". Decoding per game would handle mixed files.

5. **non-blocking.** Engine failures are not handled the way a missing input is.
   - `cli.py:100` catches only `FileNotFoundError`.
   - Reproduction: an `--engine` that is not a UCI engine ends with exit 1 and a full traceback
     (`chess.engine.EngineTerminatedError`), not a one-line `error:`.
   - `analysis.py:229`: a worker whose engine died is put back in the queue.
   - Leaving the `as_completed` loop inside `with ThreadPoolExecutor` (`analysis.py:245`) waits
     for all the queued games first. So on a long run, the first failure surfaces only after every
     other game has been attempted, and the games that went to the dead engine fail. The
     incremental rerun does recover them.
   - Worth a line in the docs, or a friendlier error.

6. **non-blocking.** The claim that the mating move gets no eval is made but not asserted.
   - `analysis.py:9-11` states it.
   - Both tests allow either outcome:
     - `test_library_analysis.py:139` checks only `nodes[:-1]`;
     - `test_cli.py:212` accepts `eval() is not None or …is_checkmate()`.
   - I checked the actual output by hand: `4. Qxf7# ( 4. Qxf7# $18 ) 1-0` carries no eval on the
     mating move, so the behaviour is as described.
   - Assert it, in one line in the forced-mate test: `nodes[-1].eval() is None`, or no comment.

7. **non-blocking.** Additions beyond the contract, and harness text beyond the gates table.
   - **Additions:** `read --out` / `Collection.write`, the `FileNotFoundError` on a missing path or
     an empty glob, the Latin-1 fallback, the `PostmortemId` header, and the dropped `Annotator`,
     `PlyCount` and `CurrentPosition` headers.
     - Each is small, listed in the PR body and, except the headers, tested.
     - `read --out` is needed for the done-when's "read, then analyze" run.
     - I do not consider any of them scope creep.
   - **Missing from the README:** the `PostmortemId` header the library adds to every game is not
     mentioned in the README's library section (`README.md:141-162`).
   - **Harness text:** `CLAUDE.md:60-66` also changes *paths to inspect* and *the canonical
     source*. That is process text beyond the gates-table row the F-1.1 row names. It is needed so
     the slot does not keep calling `scripts/*.py` the only canonical source, and it is covered by
     this review under the bootstrap rule. It is recorded here so the change is visible.

8. **non-blocking.** The console script entry point is not exercised by any test.
   - `pyproject.toml` `[project.scripts]` defines it. The subprocess test runs
     `python -m pgn_postmortem` with `PYTHONPATH` (`test_cli.py:187-189`).
   - I checked that `.venv/bin/pgn-postmortem` is installed by `pip install -e .`.
   - Acceptable for F-1.1. Worth covering by F-1.4, when the PyPI install is the contract.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
One blocking finding remains (finding 1: the incremental skip counts stripped, unanalyzed files as analyzed).
