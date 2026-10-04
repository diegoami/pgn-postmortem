# Correcting recorded results

Reference for ROADMAP F-14 and F-15. The README has the short version.

Every command and snippet here marked `tested` is run by
`tests/test_result_docs.py` against the hand-written games in
`tests/fixtures/site/corrections/` (copied to `analyzed/`), so the examples and
the output shown cannot drift from the code.

## Optional, always

**Nothing is corrected unless you ask.** Reading, `analyze` without
`--correct-results`, `site`, `workspace` with a manifest that has no
`correct_results` key, and the library calls that do not name the correction,
never touch a result. There is no default that corrects.

## What it does, and the caveat

A source's `Result` is sometimes wrong, a residue of computer analysis: the
side with the won position recorded as the loser, a draw recorded as a defeat.
The library can read the final position, and write the result that position
gives into the `Result` header of a game it analyzed.

**The honest caveat:** a decisive result in a level position can be genuine, a
time forfeit, a resignation, an adjudication, and the library cannot tell. A
correction can therefore make a true result false. That is why it is opt-in,
why it keeps the source's value (`OriginalResult`), why every change is
reported, and why the policies below let you choose how far it may go and
which games it must leave alone.

## The verdict of the final position

1. **The board decides first**: checkmate gives the mating side the win;
   stalemate and insufficient material a draw.
2. Otherwise the **final `[%eval]`** (a forced mate counts as 100%): a win for
   a side with at least the **threshold** winning chances (70% by default, 55
   to 95, one value, set with `--threshold`, `presume_threshold=` or
   `result_threshold`), a draw otherwise.
3. A game with neither (no board result, no final eval) has **no verdict** and
   is never changed.

Only games the library analyzed (carrying the `PostmortemAnalysis` marker) are
touched; the final eval is already in the file, so **no engine runs**.

## The policies

The policy says which verdicts may overrule which recorded results. In the
table, `o` is the source's result, `v` the verdict, `->X` writes X, `-` keeps
the result.

| policy | rule |
|---|---|
| `all` (the default) | the verdict, whenever there is one: a recorded decisive result in a level position becomes a draw |
| `contradictions` | the verdict only when `o` is recorded (`1-0`, `0-1`, `1/2-1/2`), the verdict is decisive and differs from it: a recorded win or loss reversed, or a recorded draw made decisive; never a decisive result made a draw because the position is level, and `*` is not filled in |
| `unrecorded` | the verdict only when `o` is `*`, missing or not a result (F-5's rule, written to the file) |
| `board` | the verdict only when the board decided it (checkmate, stalemate, insufficient material) |

| `o` \ `v` | `1-0` | `0-1` | `1/2-1/2` |
|---|---|---|---|
| `all`, `1-0` | - | ->0-1 | ->1/2-1/2 |
| `all`, `0-1` | ->1-0 | - | ->1/2-1/2 |
| `all`, `1/2-1/2` | ->1-0 | ->0-1 | - |
| `all`, `*` | ->1-0 | ->0-1 | ->1/2-1/2 |
| `contradictions`, `1-0` | - | ->0-1 | - |
| `contradictions`, `0-1` | ->1-0 | - | - |
| `contradictions`, `1/2-1/2` | ->1-0 | ->0-1 | - |
| `contradictions`, `*` | - | - | - |
| `unrecorded`, `1-0` / `0-1` / `1/2-1/2` | - | - | - |
| `unrecorded`, `*` | ->1-0 | ->0-1 | ->1/2-1/2 |
| `board` | as `all`, only when the board decided `v` | | |

### A worked example of each

The fixture games: `2013-01-01` was recorded `0-1` and its final eval is +2.75
(73% for White); `2013-01-02` was recorded `1-0` and its final eval is 0.00;
`2013-01-05` was recorded `*` and ends at +2.75; `2013-01-10` was recorded
`1-0` and ends in stalemate.

`all` corrects all four, including the recorded win in the level position:

```console tested
$ pgn-postmortem correct-results analyzed --dry-run
Policy: all, threshold 70.
2013-01-01-30390dba02.pgn: 0-1 -> 1-0 (Ada Example vs. Bert Sample, corrected)
2013-01-02-545b079385.pgn: 1-0 -> 1/2-1/2 (Ada Example vs. Bert Sample, corrected)
2013-01-05-4181e790f7.pgn: * -> 1-0 (Ada Example vs. Bert Sample, corrected)
2013-01-10-c95ddbcd6f.pgn: 1-0 -> 1/2-1/2 (Ada Example vs. Bert Sample, corrected)
Would change 7 game(s); 1 already agree, 1 without a verdict from the final position, 1 skipped.
```

`contradictions` reverses the recorded loss, and keeps the recorded win in the
level position, the `*` and the stalemate (`--explain` says why for each game
kept):

```console tested
$ pgn-postmortem correct-results analyzed --policy contradictions --dry-run --explain
Policy: contradictions, threshold 70.
2013-01-01-30390dba02.pgn: 0-1 -> 1-0 (Ada Example vs. Bert Sample, corrected)
2013-01-02-545b079385.pgn: kept: policy (1-0, the final position says 1/2-1/2)
2013-01-05-4181e790f7.pgn: kept: policy (*, the final position says 1-0)
2013-01-10-c95ddbcd6f.pgn: kept: policy (1-0, the final position says 1/2-1/2)
Would change 4 game(s); 1 already agree, 1 without a verdict from the final position, 3 kept by the policy, 1 skipped.
```

`unrecorded` only fills in the `*`:

```console tested
$ pgn-postmortem correct-results analyzed --policy unrecorded --dry-run
Policy: unrecorded, threshold 70.
2013-01-05-4181e790f7.pgn: * -> 1-0 (Ada Example vs. Bert Sample, corrected)
Would change 1 game(s); 1 already agree, 1 without a verdict from the final position, 6 kept by the policy, 1 skipped.
```

`board` only writes what the board proves, here the stalemate and a checkmate:

```console tested
$ pgn-postmortem correct-results analyzed --policy board --dry-run
Policy: board, threshold 70.
2013-01-09-eb43f2e558.pgn: 1/2-1/2 -> 0-1 (Bert Sample vs. Ada Example, corrected)
2013-01-10-c95ddbcd6f.pgn: 1-0 -> 1/2-1/2 (Ada Example vs. Bert Sample, corrected)
Would change 2 game(s); 1 already agree, 1 without a verdict from the final position, 5 kept by the policy, 1 skipped.
```

## The threshold

One value, 55 to 95, default 70 (about +2.3 pawns). A side with exactly the
threshold counts as winning. Anything outside 55 to 95 is rejected before
anything is read or written. With `--threshold 80` the +2.75 position (73%) is
a draw:

```console tested
$ pgn-postmortem correct-results analyzed --policy contradictions --threshold 80 --dry-run
Policy: contradictions, threshold 80.
2013-01-06-6d18beffac.pgn: 1/2-1/2 -> 0-1 (Ada Example vs. Bert Sample, corrected)
2013-01-09-eb43f2e558.pgn: 1/2-1/2 -> 0-1 (Bert Sample vs. Ada Example, corrected)
Would change 2 game(s); 1 already agree, 1 without a verdict from the final position, 5 kept by the policy, 1 skipped.
```

(The recorded loss, at 73%, is no longer a win at 80%, so `contradictions`
leaves it; what is still corrected is the forced mate and the checkmate.)

## Leaving games alone

A skipped game is left exactly as it is, even if an earlier run corrected it,
and is reported `kept: skipped`. This is where you tell the library what only
you know: that a game ended on time, by resignation, by adjudication.

**On the command line** and **in the manifest**, one small form: `NAME=REGEX`,
repeatable. A game is skipped when its header `NAME` exists and the regular
expression is found in its value (`re.search`, case sensitive; `(?i)` for
insensitive; any rule skips). It covers a reason the result may be genuine
(`Termination=(?i)forfeit|time`), a kind of game (`Event=Blitz`) and a single
game by its id (the last part of its file name: `PostmortemId=^30390dba02$`). A rule without `=` or with an
invalid regular expression is rejected before anything is read.

```console tested
$ pgn-postmortem correct-results analyzed --skip-header PostmortemId=^30390dba02$ --dry-run --explain
Policy: all, threshold 70.
Skip rules: PostmortemId=^30390dba02$
2013-01-01-30390dba02.pgn: kept: skipped (0-1)
Would change 6 game(s); 1 already agree, 1 without a verdict from the final position, 1 excluded by the skip rule, 1 skipped.
```

**In the library**, `skip` is a callable `skip(game) -> bool`. It receives the
`chess.pgn.Game` of each analyzed game as read (its headers as in the file,
`Result`, `OriginalResult`, `PostmortemId`, `Termination`, and its moves with
their comments), once, before the policy; it must not change the game.
`header_skip(["NAME=REGEX", ...])` builds one from the same rules.

```python tested
from pgn_postmortem import correct_results

def club_championship_games(game):
    return game.headers["Event"] == "Club championship"

report = correct_results("analyzed", policy="contradictions", skip=club_championship_games)
assert report.excluded == 9 and report.changes == []
```

## What is written, and how to undo it

`Result` becomes the result the policy gives, and `OriginalResult` holds the
source's value, written **only when the two differ**. A run never overwrites
`OriginalResult` with a corrected value. Running again changes nothing.
Files are written only after every game has been decided, so an error (for
example a `skip` callable that raises) leaves every file as it was.

**Undo.** Correct again with a policy that would not make the correction: a
narrower policy **restores** each game it would not have corrected (the
original comes back and `OriginalResult` is removed; reported `restored`).
`--policy board` after `all` restores everything except the board's own
corrections.

**There is no command that undoes the board's own corrections or the `*`
fills** (no `--policy none`): a game the policy still corrects stays corrected.
To undo those, re-read the source (reading without the analysis always gives
the source's result back, and analyzing again from it is a new, uncorrected
copy), or copy the `OriginalResult` value back into `Result` by hand and delete
the header. `OriginalResult` exists only on a game whose `Result` differs from
the source's, so it is also the list of what was changed.

```console tested
$ pgn-postmortem correct-results analyzed
$ pgn-postmortem correct-results analyzed --policy board
Policy: board, threshold 70.
2013-01-01-30390dba02.pgn: 1-0 -> 0-1 (Ada Example vs. Bert Sample, restored)
```

## Identity stays stable

A game's id (`PostmortemId`, and so its file name and its match with its
unanalyzed source) is computed from the **source's** result: `OriginalResult`
when the game has it. A correction therefore changes no id and no file name,
analysis is not redone, and the analyzed copy and its source are still one
game. Reading a corrected game without its analysis gives the source's result
back.

## The interfaces

### Command line

```bash
pgn-postmortem correct-results DIR [--policy all|contradictions|unrecorded|board]
                               [--threshold PERCENT] [--skip-header NAME=REGEX]...
                               [--dry-run] [--explain]
pgn-postmortem analyze INPUT... --out DIR --correct-results
                               [--result-policy NAME] [--result-threshold PERCENT]
                               [--result-skip-header NAME=REGEX]...
```

The reports say the policy used (`Policy: contradictions, threshold 70.`), list
each change with its reason (`corrected`, `restored`), and with `--explain`
every game kept (`kept: agrees`, `kept: policy`, `kept: skipped`,
`kept: no verdict`); `--dry-run` prints the same and writes nothing. Giving a
policy, threshold or skip rule to `analyze` without `--correct-results` is an
error.

### Library

```python tested
from pgn_postmortem import Collection, correct_results

# files: a directory of analyzed games, rewritten in place
report = correct_results("analyzed", policy="contradictions", presume_threshold=70, dry_run=True)
print(report.header())
for decision in report.decisions:
    print(decision.line())

# memory: nothing written, e.g. before building a site
games = Collection.read("analyzed", keep_analysis=True)
report = games.correct_results(policy="board")
assert len(report.changes) == 2  # the stalemate and the checkmate
games.build_site("site", title="Games")
```

`Collection.analyze(..., correct_results=True, result_policy=..., presume_threshold=...,
result_skip=...)` corrects each game as it is analyzed. A policy or skip rule
without `correct_results=True` raises `ValueError`.

### Workspace manifest

Per `[[collection]]`, all optional; absent keys mean no correction. The
correction is applied **in memory** when the site is built: no input or
analysis file is ever rewritten (F-13's read-only promise holds), and the
build reports it.

```toml tested
[[collection]]
slug = "otb"
title = "Over-the-board games"
inputs = ["analyzed"]
correct_results = "contradictions"            # a policy name
result_threshold = 70                         # optional, 55 to 95
result_skip_headers = ["Termination=(?i)forfeit|time"]   # optional, NAME=REGEX
```

An unknown policy, a threshold outside 55 to 95, a bad rule, or a threshold or
rules without `correct_results` are rejected before anything is written.
