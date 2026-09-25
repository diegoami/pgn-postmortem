# Synthetic fixtures: the quiz list of the player's own mistakes

**Hand-written, not generated.** These PGNs were written by hand for the tests
of ROADMAP F-9 (`tests/test_quiz.py`). No engine produced them: the
`PostmortemAnalysis` header that marks a game as analyzed says so
(`hand-written for the tests, not by an engine`), and every `[%eval]` comment
and every engine line (a variation) was set by hand to put a move exactly
where a test needs it. The evaluations are not what Stockfish would say about
these positions. Edit these files by hand, and keep this table in step.

Every game opens 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6 5. d3 d6 6. O-O O-O,
each move at `[%eval 0.20]` (White 51.8%), as in `../swings/`. No file carries
a `PostmortemId`: the reader adds it. The player is Ada Example, with the
aliases `adaex` and `Example, Ada`, as in the rest of the site's fixtures. A
move's cost is what its side lost in winning chances
(`pgn_postmortem.analysis.win_percent`); the costs below are rounded, the
tests compute them exactly. Three moves cost exactly the same (the same
`[%eval]` before and after, by White), to test the tie rule.

| file | Date | White | Black | critical moments (cost) | what it tests |
|---|---|---|---|---|---|
| `blunder-2015.pgn` | 2015.05.05 | Enzo Opponent | Example, Ada | 7... a6 (45.7, the player's) | the worst of the player's moves comes first, although its game is the latest of the player's |
| `tie-999.pgn` | 999.09.09 | adaex | Gino Newcomer | 7. Re1 (26.95, the player's) | a tie broken by the index, not the file name: the index lists the year 999 first (years are numbers), while its file name `999-09-09-…` sorts after `2012-…` |
| `tie-2012.pgn` | 2012.02.02 | Ada Example | Dora Sample | 7. Re1 (26.95, the player's) | the same tie, second in the index |
| `ties-2014.pgn` | 2014.04.04 | `  ADA EXAMPLE ` (upper case, with spaces around) | Carl `<Foe> & Co` | 7. Re1 and 8. h3 (26.95 each, the player's); 7... a6 (26.95, the opponent's) | a tie inside one game, broken by move order; the name matched regardless of case and spaces; the opponent's moment left out; the opponent's name escaped |
| `both-sides.pgn` | 2013.03.03 | adaex | Example, Ada | 7. Re1 (18.7) and 8... Nh5 (13.1), both outcome swings | both sides are the player, so both moments count; outcome swings (F-6) count. The moves and evaluations are `../swings/two-swings.pgn`'s |
| `opponents-only.pgn` | 2017.07.07 | Hugo Casual | Ada Example | 7. Re1 (49.4, the opponent's) | a game of the player with no own moment |
| `others.pgn` | 2016.06.06 | Otto Other | Pia Other | 7. Re1 (49.4) | a game in which neither side is the player: read without a player, it is in the site but not in the quiz |

The quiz of all seven, for the player, is therefore: 7... a6 (2015), 7. Re1
(999), 7. Re1 (2012), 7. Re1 and 8. h3 (2014), 7. Re1 and 8... Nh5 (2013).
