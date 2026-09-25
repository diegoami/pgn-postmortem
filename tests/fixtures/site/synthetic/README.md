# Synthetic fixtures: games whose result was not recorded

**Hand-written, not generated.** These PGNs were written by hand for the tests
of ROADMAP F-5 (`tests/test_presumed_results.py`). No engine produced them:
the `PostmortemAnalysis` header that marks a game as analyzed says so
(`hand-written for the tests, not by an engine`), and every `[%eval]` comment
was set by hand to put the final position at a chosen winning chance. The
evaluations are not what Stockfish would say about these positions. They are
not under `tests/fixtures/site/analyzed/`, which `pgn-postmortem analyze`
writes; edit these files by hand, and keep this table in step.

Every game has `Result "*"`, except `no-result-header.pgn`, which has no
`Result` header at all (python-chess reads it as `*`, and its PGN section
shows `[Result "*"]`). No file carries a `PostmortemId`: the reader adds it.
Winning chances are White's, from the analysis step's win-percentage model
(`pgn_postmortem.analysis.win_percent`). In `white-27.pgn` White made two
inaccuracies; in `white-73.pgn` Black did.

| file | analyzed | how it ends | White's chances | the result the site shows |
|---|---|---|---|---|
| `white-73.pgn` | yes | 3... a6, `[%eval 2.75]`; Black made two inaccuracies | 73.4% | 1–0 (½–½ with the threshold at 80) |
| `white-27.pgn` | yes | 3... a6, `[%eval -2.75]` | 26.6% | 0–1 |
| `white-34.pgn` | yes | 3... a6, `[%eval -1.86]` | 33.5% | ½–½ |
| `white-66.pgn` | yes | 3... a6, `[%eval 1.86]` | 66.5% | ½–½ (1–0 with the threshold at 60) |
| `white-59.pgn` | yes | 3... a6, `[%eval 1.00]` | 59.1% | ½–½ (1–0 with the threshold at 55) |
| `checkmate.pgn` | no | 2... Qh4#, checkmate on the board | | 0–1 |
| `stalemate.pgn` | no | 50. Qf7, stalemate (from a `FEN` start) | | ½–½ |
| `insufficient-material.pgn` | no | 60. Kxd2, king against king (from a `FEN` start) | | ½–½ |
| `stalemate-analyzed.pgn` | yes | 50. Qf7, stalemate, with an impossible `[%eval 5.00]`: the board decides first | (86.3%) | ½–½ |
| `mate-white.pgn` | yes | 60... Kd6, `[%eval #8]`: a mate score, not checkmate | 100% | 1–0 |
| `mate-black.pgn` | yes | 61. Kd5, `[%eval #-8]` | 0% | 0–1 |
| `not-recorded.pgn` | no | 3... Nf6, a position with play left | | not recorded |
| `no-result-header.pgn` | no | 2... Nf6, no `Result` header | | not recorded |
