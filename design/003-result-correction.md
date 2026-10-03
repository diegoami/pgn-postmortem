# F-14: correct the recorded result from the final position

Status: proposed

Owner decisions (2026-10-03): see `ROADMAP.md`, F-14. They are restated where
they decide something below and marked as such.

## Problem

Many games carry a `Result` that the final position contradicts: a side with
a won position recorded as the loser, a draw recorded as a defeat. The owner
calls it a residue of computer analysis and wants the result corrected from
the evaluation of the final position, in the core of the library. The owner's
survey (final `[%eval]` against the recorded result at 70%) found 9 of 148 OTB
games, 114 of 1,068 correspondence games and 13 of 264 standard games in
disagreement; about 140 games have no final eval because the board ended them
(checkmate or resignation on the board).

Caveat, recorded rather than hidden: a decisive result in a level position can
be genuine (a time forfeit, a resignation, an adjudication). The library
cannot know. So the correction is explicit (never a side effect of reading),
always reports each change, and always keeps the source's value.

## Findings

- F-5 already holds the rule for unrecorded results, but only at display time
  and only for `*`: `shown_result`, `final_white_chances` and
  `check_presume_threshold` in `pgn_postmortem/site.py` (around lines 372-418).
  A recorded result is returned as recorded.
- `game_id` (`pgn_postmortem/collection.py`) hashes the `Result` header as
  written. Writing a corrected result into the header would change the id of
  the analyzed copy, its file name (`<date>-<id>.pgn`) and its match with its
  source (`analyzed_ids`, `Collection.read(keep_analysis=True)`'s duplicate
  rule), so analysis would be redone for every corrected game. Verified by
  reading `Collection.write` and `analyze_games`, which compare ids.
- `strip_game` keeps every header except `DROPPED_HEADERS`, so a corrected
  `Result` and an `OriginalResult` would otherwise travel into a stripped copy
  made from an analyzed file.
- The final `[%eval]` is in each analyzed file, so no engine is needed to
  correct existing analyzed directories.

## Design

### The rule (one place)

A new module `pgn_postmortem/results.py` owns the rule and the validation
(moved from `site.py`, which imports them; `site.shown_result`,
`site.final_white_chances`, `site.check_presume_threshold`,
`site.PRESUME_THRESHOLD` keep working under the same names).

`decided_result(game, presume_threshold=70.0) -> str | None`: the board first
(checkmate: the mating side wins; stalemate or insufficient material: draw);
otherwise, if the game carries the analysis marker and its last move has an
`[%eval]`, a win for a side with at least `presume_threshold` winning chances
(`analysis.win_percent`, a mate score counts as 100) and a draw otherwise;
otherwise None (no verdict). The threshold is validated 55-95 exactly as F-5's.

### Headers

- `Result` is the corrected result; `OriginalResult` is the source's value as
  written (`*` for a missing one), written **only when they differ**.
- Only games carrying `PostmortemAnalysis` (the library's own output) are
  corrected, and only such a game's `OriginalResult` is trusted. A source game
  with an `OriginalResult` of its own is not touched or believed. Reason: the
  id rule below depends on the marker, and a stripped source copy must keep
  hashing its `Result`.
- **Idempotence and reversal.** Correcting again compares the rule's verdict
  with the current `Result`: equal, nothing changes. If the verdict differs,
  `Result` becomes the verdict and `OriginalResult` keeps the first original,
  never the previous corrected value. If the verdict equals the
  `OriginalResult` (a rerun at another threshold), `Result` goes back to it
  and `OriginalResult` is removed (reported as restored). So
  `OriginalResult` is present exactly when the result differs from the source.
- A game with no verdict (no mate, stalemate or insufficient material, and no
  final eval) is left as it is and counted.
- A game recorded `*` that gets a verdict is corrected like any other
  (`OriginalResult "*"`): the header becomes definitive and agrees with what
  the site showed before.

### The id rule (owner decision)

`game_id` hashes the **original** result: `OriginalResult` when the game
carries the marker and the header, else `Result`. A corrected analyzed copy
therefore keeps its `PostmortemId`, its file name and its match with its
source. `strip_game`, when the game carries the marker, restores `Result` from
`OriginalResult` and drops `OriginalResult`: the correction comes from the
analysis, and the stripped game is a stripped game again.

### API

- `correct_game(game, presume_threshold=70.0) -> ResultChange | None`:
  changes one game's headers in place; None when nothing changed.
- `correct_results(path, *, presume_threshold=70.0, dry_run=False) ->
  CorrectionReport`: for each PGN file under `path` (a directory, recursively,
  or one file) whose single game carries the marker, correct and rewrite it
  atomically (only if changed; the file name is not changed because the id is
  not). A file that is not analyzed, has several games or does not parse is
  skipped and counted, with a warning. No engine, no network.
- `Collection.correct_results(presume_threshold=70.0) -> CorrectionReport`:
  the same for the games of a collection read with `keep_analysis=True`, in
  memory (so a site can be built from corrected games without writing them).
  Not-analyzed games are skipped.
- `analyze_games(..., correct_results=False, presume_threshold=70.0)` and
  `Collection.analyze(...)`: when true, each newly analyzed game is corrected
  before it is written. The threshold is validated up front, before the
  engine starts. Games already analyzed are not touched by this option; the
  `correct-results` command is for them.
- `ResultChange(path, game_id, white, black, old, new, kind)`, `kind` one of
  `corrected`, `restored`; `CorrectionReport(changes, unchanged, no_verdict,
  skipped, warnings)` with `summary()` and one line per change
  (`2019-03-14-bf58e2afa0.pgn: 0-1 -> 1/2-1/2`). Exported from
  `pgn_postmortem`.

### CLI

- `pgn-postmortem correct-results DIR [--threshold N] [--dry-run]`: prints one
  line per changed game (file, players, old -> new) and the counts; with
  `--dry-run`, writes nothing. Threshold outside 55-95: exit 1 with an error
  before any file is touched.
- `pgn-postmortem analyze ... --correct-results [--result-threshold N]`.

### The site

The site needs no change to work: it reads the corrected `Result` and shows it
(`shown_result` returns the recorded value). Two small additions, neither
changing any existing golden page (no existing fixture has an
`OriginalResult`):

- an article of a game with an `OriginalResult` has a "Source result" row in
  its infobox, and a sentence in its conclusion saying the source recorded it
  differently and the library corrected it from the final position;
- `Article.presumed` is true for such a game, so the conclusion never says a
  corrected result "came from outside the position".

### Interaction with `keep_analysis` and duplicates

Reading the analyzed directory with `keep_analysis=True` computes the id from
the original result, so the analyzed copy and its source still collide as
duplicates exactly as before, and the analyzed copy is kept. Reading with
`keep_analysis=False` strips the copy (original result restored).

## Tests (no Stockfish)

On hand-written fixtures in `tests/fixtures/site/corrections/` (README says
what each is): recorded loss with 73% for the player; recorded win in a 50%
position; recorded draw at 27%; a recorded game already agreeing; a mate and a
stalemate with a wrong recorded result; `*`; exactly at the threshold; a game
without a final eval and not ended on the board. Checks: results and headers;
the second run changes nothing and `OriginalResult` is the first value; a
rerun at another threshold restores; id before equals id after, same file
name, still matching its unanalyzed source (read both, one game); stripped
read restores the original; threshold validation (library and CLI, before any
write); `dry_run` writes nothing; `Collection.correct_results`; the option on
`analyze_games` through a stubbed `analyze_game`-free path (the correction
function on an analyzed game, since the engine must not run), and validation
before the engine starts; the CLI as a subprocess; the site showing the
corrected result, the source-result row and sentence, and the existing
goldens unchanged.

## Out of scope

Running it on the owner's archives; the Markdown pipeline; any signal other
than the board and the final eval (`Termination`, clock, move text); a
per-game override list.

## Open questions

None for the owner: the four decisions of 2026-10-03 settle the semantics.
Recommended defaults taken, for the owner's veto: a `*` result is corrected
too; a rerun at another threshold may restore the original.
