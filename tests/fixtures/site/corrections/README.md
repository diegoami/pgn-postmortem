# Correction fixtures: results the final position contradicts

**Hand-written, not generated.** Written for the tests of ROADMAP F-14
(`tests/test_result_correction.py`). No engine produced them: the
`PostmortemAnalysis` header says so, and every `[%eval]` was set by hand. They
are 6-ply games (ending 3... a6) unless said otherwise, with different dates
so every game has its own id. Chances are White's, from
`pgn_postmortem.analysis.win_percent`. Edit by hand and keep this table in
step.

| file | recorded | final position | corrected to |
|---|---|---|---|
| `loss-is-win.pgn` | 0-1 | `[%eval 2.75]` (73.4%) | 1-0 |
| `win-is-draw.pgn` | 1-0 | `[%eval 0.00]` (50%) | 1/2-1/2 |
| `draw-is-loss.pgn` | 1/2-1/2 | `[%eval -2.75]` (26.6%) | 0-1 |
| `agrees.pgn` | 1-0 | `[%eval 2.75]` (73.4%) | unchanged |
| `unrecorded-is-win.pgn` | * | `[%eval 2.75]` (73.4%) | 1-0 |
| `mate-score.pgn` | 1/2-1/2 | `[%eval #-8]` (0%) | 0-1 |
| `checkmate-is-draw.pgn` | 1/2-1/2 | the board: Black mates with 2... Qh4# | 0-1 |
| `stalemate-is-win.pgn` | 1-0 | the board: stalemate (from a `FEN`), with an impossible `[%eval 5.00]` | 1/2-1/2 |
| `no-final-eval.pgn` | 1-0 | no eval, and not ended on the board | unchanged (no verdict) |
| `not-analyzed.pgn` | 0-1 | no analysis marker | untouched |

## What each policy makes of them (ROADMAP F-15, `tests/test_result_policies.py`)

No game was added for the policies: these ten cover every case. A game not
listed under a policy is left as recorded.

| policy | corrected |
|---|---|
| `all` | `loss-is-win`, `win-is-draw`, `draw-is-loss`, `unrecorded-is-win`, `mate-score`, `checkmate-is-draw`, `stalemate-is-win` |
| `contradictions` | `loss-is-win` (1-0), `draw-is-loss` (0-1), `mate-score` (0-1), `checkmate-is-draw` (0-1); not `win-is-draw` (a win in a level position), `unrecorded-is-win` (`*`) or `stalemate-is-win` (a draw) |
| `unrecorded` | `unrecorded-is-win` (1-0) |
| `board` | `checkmate-is-draw` (0-1), `stalemate-is-win` (1/2-1/2) |

`tests/test_result_docs.py` copies these games, analyzed, to `analyzed/` and
runs the documentation's examples on them: the output the docs show names these
files and their ids, so a change to a fixture's content changes the docs.
