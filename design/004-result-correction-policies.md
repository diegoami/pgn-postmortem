# F-15: customizable, optional and documented result correction

Status: proposed (implemented; awaiting the fresh-context review)

Owner decisions (2026-10-04): see `ROADMAP.md`, F-15. Every F-14 parameter and
flag keeps working unchanged, and today's behaviour is the default policy.

## Problem

F-14 (`design/003-result-correction.md`) has one behaviour: board first, then
the final eval at the threshold, so a recorded decisive result in a level
position becomes a draw. That is right for the owner's archives but not for
every collection: a time forfeit or a resignation in a level position is a
genuine result the library cannot recognise. The owner wants the behaviour to
be customizable, strictly optional, and well documented.

## Findings

- The rule lives in `pgn_postmortem/results.py` (`decided_result`,
  `correct_game`, `correct_results`, `correct_collection`); it is reached by
  `correct_results(path)`, `Collection.correct_results`,
  `analyze_games(correct_results=True)`, the `correct-results` command and
  `analyze --correct-results`.
- `Workspace.build` (`pgn_postmortem/workspace.py`) reads each profile's
  inputs with `keep_analysis=True` and builds its site from the games in
  memory. F-13's design (`design/002-separate-collections.md`) calls the
  profile's `analyzed_dir` a read-only cache; nothing in it forbids changing
  the games in memory. **There is no conflict**: the manifest keys below
  correct in memory only, so the promise (no input or cache file is ever
  written) holds, and a test asserts it.
- F-14's tests assert the report text in two places (the second-run line of
  the `correct-results` command, and the summary prefix). See "Report".

## Design

### Names (final)

| where | policy | threshold | skip | other |
|---|---|---|---|---|
| Python, directory | `correct_results(path, policy="all")` | `presume_threshold=70` | `skip=None` | `dry_run=False` |
| Python, memory | `Collection.correct_results(presume_threshold=None, *, policy="all", skip=None)` | same | same | |
| Python, analysis | `analyze_games(..., correct_results=False, result_policy="all", presume_threshold=None, result_skip=None)` | | | `Collection.analyze` passes them |
| CLI | `correct-results DIR --policy NAME` | `--threshold PERCENT` | `--skip-header NAME=REGEX` (repeatable) | `--dry-run`, `--explain` |
| CLI | `analyze ... --correct-results --result-policy NAME` | `--result-threshold PERCENT` | `--result-skip-header NAME=REGEX` | |
| manifest, per `[[collection]]` | `correct_results = "NAME"` | `result_threshold = 70` | `result_skip_headers = ["NAME=REGEX"]` | |

`pgn_postmortem.results.POLICIES` is `("all", "contradictions", "unrecorded",
"board")`. `CollectionProfile` gains `correct_results`, `result_threshold`,
`result_skip_headers` (default None, None, empty).

### Opt-in everywhere (owner decision)

Nothing is corrected unless asked: reading, `analyze` without
`--correct-results`, `site` and a manifest without `correct_results` never
touch a result. A policy, threshold or skip rule given without the switch that
turns correction on is an error (the command line exits 1; the manifest is
rejected; the library validates the policy and threshold it is given, and a
`result_policy` or `result_skip` without `correct_results=True` raises
`ValueError`), never silently ignored.

### The policies

Let `o` be the source's result (`source_result`: `OriginalResult` when the
game carries it, else `Result`), and `v` the verdict of the final position
(F-14's rule: the board first, else the eval at the threshold; `None` when
there is none), with a flag for whether the **board** decided it. "Recorded"
means `o` is one of `1-0`, `0-1`, `1/2-1/2`; anything else (`*`, missing,
other text) is "unrecorded". The result the header should hold, the **target**:

- **`all`** (F-14, the default): `v` whenever there is one.
- **`board`**: `v` only when the board decided it (checkmate, stalemate,
  insufficient material); otherwise `o`.
- **`unrecorded`** (F-5's rule written to the file): `v` only when `o` is
  unrecorded; otherwise `o`.
- **`contradictions`**: `v` only when `o` is recorded, `v` is decisive (`1-0`
  or `0-1`) and `v != o`: a recorded win or loss reversed, or a recorded draw
  made decisive. Never a decisive result made a draw because the position is
  level (also not a stalemate or insufficient material on the board: use
  `board` for those), and never a fill-in of `*`.

Outcome, rows the source's result, columns the verdict (`->X` changes to X,
`-` leaves it; a verdict equal to `o`, or none, leaves it in every policy):

| `o` \ `v` | `1-0` | `0-1` | `1/2-1/2` |
|---|---|---|---|
| **all** `1-0` | - | ->0-1 | ->1/2-1/2 |
| **all** `0-1` | ->1-0 | - | ->1/2-1/2 |
| **all** `1/2-1/2` | ->1-0 | ->0-1 | - |
| **all** `*` | ->1-0 | ->0-1 | ->1/2-1/2 |
| **contradictions** `1-0` | - | ->0-1 | - |
| **contradictions** `0-1` | ->1-0 | - | - |
| **contradictions** `1/2-1/2` | ->1-0 | ->0-1 | - |
| **contradictions** `*` | - | - | - |
| **unrecorded** `1-0`, `0-1`, `1/2-1/2` | - | - | - |
| **unrecorded** `*` | ->1-0 | ->0-1 | ->1/2-1/2 |
| **board** (as `all`, only when the board decided `v`) | | | |

`target_result(policy, original, verdict, by_board)` implements it; a test
compares every `o` x `v` x board-or-eval x policy against a literal table.

The write rule is F-14's, generalised with the target: if the target equals
the current `Result`, nothing changes; else if it equals `o`, `Result` is
restored and `OriginalResult` removed (`restored`); else `Result` becomes the
target and `OriginalResult` holds `o` (`corrected`). So running with a
**narrower** policy than before undoes the corrections the narrower policy
would not make, and `OriginalResult` is present exactly when `Result` differs
from the source's. Undo everything: restore is not a command of its own;
`correct-results --policy board` after `all` restores each game the board did
not decide, and a game's original is always in its `OriginalResult` header.
(A full undo, `--policy none`, is out of scope: delete the header's effect by
re-reading the source.)

### One threshold

The threshold stays one value, 55 to 95, as F-14's. No separate draw band.

### Excluding games

Library: `skip` is a callable `skip(game) -> bool`, called once for each
**analyzed** game (one carrying the analysis marker) with the
`chess.pgn.Game` as read: its headers as in the file (`Result`,
`OriginalResult` when present, `PostmortemId`, `Termination`, ...) and its
moves with their comments. It must not change the game. A true result leaves
the game exactly as it is, even if an earlier run corrected it; it is reported
`kept: skipped`. An exception from `skip` propagates, before the file is
written.

Command line and manifest: one small declarative form, `NAME=REGEX`
(`--skip-header`, `--result-skip-header`, `result_skip_headers`), repeatable;
a game is skipped when **any** rule matches: its header `NAME` exists and the
regular expression is found in the value (`re.search`, case sensitive; use
`(?i)` for insensitive). Justification: it is the smallest form that covers
what an owner actually has, a header that says why the result may be genuine
(`Termination=(?i)forfeit|time`, `Event=Blitz`, `TimeControl=`), and a single
game by id (`PostmortemId=^bf58e2afa0$`), so a separate `--keep-result ID`
option would add nothing. A rule without `=` or a bad regular expression is
rejected before anything is read or written. Hand-written logic belongs to the
library's `skip`.

### Report

`CorrectionReport` gains `policy`, `threshold` and `decisions`, a
`GameDecision` for each analyzed game: `path`, `game_id`, `white`, `black`,
`old`, `new` and `status`, one of `corrected`, `restored`, `kept: agrees`
(the result already is the target and the verdict), `kept: policy` (the
policy would not change it: the game's verdict differs from the result), `kept: skipped`,
`kept: no verdict`. `changes` is as before (the corrected and restored ones).
Counts: `unchanged` (kept: agrees), `no_verdict`, `kept_policy`, `excluded`
(kept: skipped) and `skipped` (files that are not analyzed, have several games
or do not parse; unchanged meaning).

`summary()` keeps F-14's text and appends ", N kept by the policy" and ", N
excluded" only when not zero. The commands print first
`Policy: NAME, threshold T.` and a line `Skip rules: ...` when there are any,
then one line per change, then, with `--explain`, one line per kept game
(`<file>: kept: policy (1-0, the final position says 1/2-1/2)`), then the
summary; `--dry-run` prints the same, as "Would change". **Deliberate format
change** (F-14's tests that assert the whole output of `correct-results`
adapt): the policy line comes first, so the test of the idempotent second run,
which compared the whole output to one line, now compares its last line.

### The manifest

Per collection, optional: `correct_results = "<policy>"`, `result_threshold`,
`result_skip_headers`. With the key absent nothing is corrected (today's
behaviour). `Workspace.build` reads the games with their analysis as before,
then `Collection.correct_results(...)` **in memory**, then builds the site;
no file is written, and the games' ids are unchanged. `WorkspaceReport` gains
`corrections`, a `CorrectionReport` for each corrected collection, and the
`workspace` command prints, for each, the policy line and the summary.
Validation, before anything is written (`Workspace.validate`, as the other
manifest checks): `correct_results` must be one of the policies, the threshold
a number from 55 to 95, the skip rules `NAME=REGEX` strings with a valid
regular expression, and `result_threshold` or `result_skip_headers` without
`correct_results` is an error.

### Documentation

A README section "Correcting recorded results" (what and why, the honest
caveat, the policies with a worked example each, the threshold, skipping,
`OriginalResult` and undoing, the three interfaces, identity) linking to
`docs/result-correction.md`, which holds the full reference. Complete
docstrings on every public name of the feature, the module docstring of
`results.py` included, and `--help` text that explains the policies. Examples
in the README and the docs page that are marked `tested` (their fence says
`console tested`, `python tested` or `toml tested`) are run by
`tests/test_result_docs.py` against the fixtures, so they cannot rot.

## Tests

On the hand-written fixtures of F-14 (`tests/fixtures/site/corrections/`,
README updated; no new game is needed): the matrix; each policy on the
directory (the changed set, the headers, a second run changing nothing,
narrowing restoring); the skip callable and the header rules; the reports
(policy line, per-game statuses, dry run, `--explain`); the manifest keys
(applied in memory, no file touched, ids unchanged, absent keys no
correction, every invalid value rejected before anything is written); the
analysis option with a policy; the docs' examples.

## Out of scope

A draw band; `--policy none`; deciding from anything but the board and the
final eval; the owner's archives; the Markdown pipeline.

## Open questions

None for the owner. Recommended defaults taken, for the owner's veto: the
command prints only the changes by default and every game with `--explain`
(a thousand lines of "kept" would hide the changes); `contradictions` does
not fill in `*`.
