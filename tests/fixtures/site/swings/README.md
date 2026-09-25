# Synthetic fixtures: moves that changed the expected result

**Hand-written, not generated.** These PGNs were written by hand for the tests
of ROADMAP F-6 (`tests/test_outcome_swings.py`). No engine produced them: the
`PostmortemAnalysis` header that marks a game as analyzed says so
(`hand-written for the tests, not by an engine`), and every `[%eval]` comment
and every engine line (a variation) was set by hand to put a move exactly
where a test needs it. The evaluations are not what Stockfish would say about
these positions. They are not under `tests/fixtures/site/analyzed/`, which
`pgn-postmortem analyze` writes, nor under `tests/fixtures/site/synthetic/`,
whose tests expect only F-5's games there; edit these files by hand, and keep
this table in step.

Every game opens 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6 5. d3 d6 6. O-O,
each move at `[%eval 0.20]` (White 51.8%), and has a recorded result. No file
carries a `PostmortemId`: the reader adds it. Winning chances are White's, from
the analysis step's win-percentage model
(`pgn_postmortem.analysis.win_percent`); a move's cost is its side's loss. The
bands are the default 40/60 (the owner's change of 2026-09-25 to the shaping's
35/65): **White winning** at 60% or more, **Black winning** at 40% or less,
**level** in between.

The engine lines are stored as the analysis step stores them: a move's own
better line is a variation that replaces it (off the position before it), and
a move's refutation is a variation that replaces the next move (off the
position after it, so also before the next move). The engine's first choice
before a move is the first move of any line stored there.

| file | move | White's chances | cost | lines stored before the move | what it tests |
|---|---|---|---|---|---|
| `two-swings.pgn` | 7. Re1 | 51.8% → 33.2% (level → Black winning) | 18.7 | its own, 7. Bb3 | a White swing (item 1); its refutation 7... Ng4 is stored |
| | 8... Nh5 | 33.2% → 46.3% (Black winning → level) | 13.1 | its own, 8... Ba7 | a Black swing (item 1); its refutation 9. Nxe5 is stored. The game has no move costing 20 points, so its only critical moments are these two swings (item 8). Read without its analysis, it has none (item 9) |
| `not-swings.pgn` | 7. h3 | 51.8% → 63.5% (level → White winning) | −11.6 (a gain) | 7. b4 | a band change in favour of the side that moved (item 2) |
| | 8. Nbd2 | 63.5% → 57.3% (White winning → level) | 6.2 | 8. a4 (as an analysis with a lower inaccuracy threshold would store it) | a band change costing less than 10 points (item 3) |
| | 8... Ba7 | 57.3% → 36.5% (level → Black winning) | −20.8 (a gain) | none | puts the game in Black's band for the next move |
| | 9. Re1 | 36.5% → 24.9% (Black winning → Black winning) | 11.6 | its own, 9. Bb3 | a 10–20-point loss inside one band (item 4). The level band is 20 points wide, so this loss is inside Black winning |
| `first-choice.pgn` | 7. Re1 | 51.8% → 33.2% (level → Black winning) | 18.7 | none: the engine's first choice was the move played | excluded, no line stored (item 5) |
| | 7... Ng4 | 33.2% → 46.3% (Black winning → level) | 13.1 | only 7. Re1's refutation, which starts with 7... Ng4 | excluded, the refutation-only shape of the owner's 3 exclusions (item 5) |
| `critical-swing.pgn` | 7. Re1 | 51.8% → 28.5% (level → Black winning) | 23.4 | its own, 7. Bb3 | a 20-point critical moment that is also a swing: shown once (item 6) |
| `edges.pgn` | 7. Re1 | 51.8% → 40.01% (level → level) | 11.8 | its own, 7. Bb3 | just inside the default lower edge; Black winning, and a swing, with the lower edge set to exactly `win_percent(-110)` (item 7) |
| | 8... Nh5 | 49.1% → 59.99% (level → level) | 10.9 | its own, 8... Ba7 | just inside the default upper edge; White winning, and a swing, with the upper edge set to exactly `win_percent(110)` (item 7) |
| `default-band.pgn` | 7. Re1 | 51.8% → 39.92% (level → Black winning) | 11.9 | its own, 7. Bb3 | the same moves as `edges.pgn` just past the default edges: swings at 40/60, not at 35/65 (item 7) |
| | 8... Nh5 | 49.1% → 60.08% (level → White winning) | 11.0 | its own, 8... Ba7 | |

In `edges.pgn` and `default-band.pgn`, 8. h3 (to `[%eval -0.10]`, 49.1%) is a
gain for White. Every other move costs nothing (its eval equals the previous
one, or it gains). The item numbers are F-6's done-when items in `ROADMAP.md`.
