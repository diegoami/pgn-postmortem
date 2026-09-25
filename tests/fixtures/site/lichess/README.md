# Lichess-link fixtures: a set-up game, signs in the moves, a standard `FEN`

**Hand-written, not generated.** These PGNs were written by hand for the tests
of ROADMAP F-10 (`tests/test_lichess_links.py`). No engine produced them: the
`PostmortemAnalysis` header of the two analyzed games says so
(`hand-written for the tests, not by an engine`), and every `[%eval]` comment
and engine line was set by hand. They are not under
`tests/fixtures/site/analyzed/`, which `pgn-postmortem analyze` writes; edit
these files by hand, and keep this table in step. No file carries a
`PostmortemId`: the reader adds it.

| file | analyzed | starts from | what it is for |
|---|---|---|---|
| `setup-blunder.pgn` | yes | a set-up position (`FEN` header), Black to move at move 30 | a set-up game with one critical moment: 31. Ra7?? (50% to 0% for White, `[%eval #-1]`) allows the back-rank mate 31... Rd1#; the better line 31. g3 and the refutation are stored. It has no game link, and its question's position link is the position after 30... h6, not the `FEN` header's |
| `promotion.pgn` | no | the standard start | the signs in the game link: a check (4... Qxf2+), captures, and a promotion that mates (6. bxc8=Q#), so the link's moves have no `+` or `#` and the `=` is URL-encoded |
| `standard-fen.pgn` | yes | a `FEN` header that spells out the standard start | kept with its `FEN` header by the analyzed reading; it starts from the standard position, so it has a game link (as for a game's identity, such a header counts the same as none) |

A game with no moves is not here: `Collection.read` skips it, so its test
builds one directly for `build_site`.
