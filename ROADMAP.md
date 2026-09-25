# Roadmap — requests and iterations

> How the project grows. The owner writes requests; the agent shapes them; an
> accepted request is one iteration, one session and one review
> ([`PLAN.md`](PLAN.md), when the overlay is used).

## The queue

The owner confirmed on 2026-09-24 that the quoted wording of F-1 to F-3 is the owner's own.

| id | request | status | iteration | notes |
|---|---|---|---|---|
| F-1 | "first publishing a pip / python library that creates a wikipedia / epub from a pgn collection" | accepted | 1 and 2 (F-1.1, F-1.2); F-1.3 and F-1.4 come after F-8 to F-11 and are numbered when they start (iterations 3 and 4 are F-5 and F-6, 5 is F-8). F-1.1 landed in #6 (`ccc0f89`), F-1.2 in #8 (`05c6270`) | The direction is in [`docs/book-plan.md`](docs/book-plan.md), *Layer 1*. Also in the owner's words: "I would like to read a book about me and my best and worst games like I was Fischer or Capablanca"; ""worst games" is kind of a bad idea, "best games that I lost", not just blunders.  But all games must be there, wikipedia style."; "in English, German comments are from old engines, strip comments and variants from games". Spike code on the branch `book-poc`. |
| F-2 | "Yes, LLM, but of course Claude with API key would be too expensive, Deepseek is the realistic option, BYOK for other users" | requested | | The book's prose. Depends on F-1. `docs/book-plan.md`, *Prose*. |
| F-3 | "then wire that into a pipeline that may fetch games from somewhere on the input or put the published files somewhere on the output" | requested | | Depends on F-1. Also in the owner's words: "as sources it must be able to parse a collection of games"; "if it has to be reusable we have to think about people who do not have a github, so output must be pluggable somehow"; "I am not maintaining their repository or web pages". `docs/book-plan.md`, *Layer 2*; the chess.com, lichess and git sources exist as spike code on `book-poc`. |
| F-4 | "yes, queue the name matching improvement" | requested | | Raised in the owner's own trial run (2026-09-24), in the owner's words: "Why are there games that are not mine, they might be mislabeled". Reading the owner's 149 OTB games kept 140 and left out 8 of the owner's own, spelled `Amicabile Diego` and `Diego , Amicabile`, because player names match exactly except for letter case, so every spelling needs its own alias. The implementer's proposal, to be shaped when picked up: match names ignoring spacing, commas and word order; and have `read` report the names seen most often in the games it left out, so a missed alias is easy to spot. Touches F-1.1's reading; the owner decides at shaping whether it lands before F-1.3 or within it. |
| F-5 | "There are a few where the results is not recorded, default to victory for the one with much higher winning chances, or draw if unclear." | landed | 3 | Raised on the owner's own book (2026-09-24): 12 of the 148 OTB games, all from 2012, have no recorded result. Shaped below. Landed in #13 (`88ebc62`), 2026-09-25. |
| F-6 | "I am looking at the games and I think there should be more diagrams, for instance in this game https://diegoami.github.io/chessgamescollection/games/2008-01-04-4e5d4e182f.html just an error is shown that did not affect the end result. It was move 40 that was deciding, not 31" | landed | 4 | The owner's choices on 2026-09-24, when asked which extra moments should get a diagram: "Swings that changed the outcome" (a move that changes the expected result, e.g. winning → level or level → losing, even below the 20-point critical-moment line), not the other two options offered ("the deciding moment" and "inaccuracies too"); and when: "Right after F-5, before F-1.3". The owner's example game (Pedroni vs. Amicabile, Verona 2008) has only 31... Qa2? as a critical moment; 37... Rg2+ (25% → 41% for White) and 40. Ra4 (49% → 32%) changed the outcome but cost 16 and 17 points. Shaped below. Landed in #15 (`378dd9c`), 2026-09-25, with the owner's band change to 40–60%. |
| F-7 | "queue the library feature" | requested | | The owner's answer on 2026-09-25 to the question "F-7: should I queue the library feature? It would make re-reading a collection refresh the headers of games that are already analyzed, so corrections like this one reach the book without any manual header editing." It comes from correcting the owner's source (DA_chessgames `9e7c939` and `691eba6`: 23 "Saxonia Systems AG" placeholder Sites and 2 Events replaced). Reading again leaves an analyzed game's file alone, headers included, so the corrected headers were carried into `chessgamescollection` by hand (`a4a7d09`, `9be2978`). Header changes don't change a game's identity (moves, result, date, start position), but a corrected `Date` or `Result` would. Not shaped yet. |
| F-8 | "A local history reminding what games have you been watching and ideally the spoilers you have looked" | accepted | 5 | Asked by the owner on 2026-09-25, after F-6 landed, as one of four requested features (F-8 to F-11). The owner decided on 2026-09-25 that F-8 to F-11 come before F-1.3. Notes for shaping: the site has no server (F-1's scope) and no JavaScript (`README.md`, `pgn_postmortem/site.py`), so a history kept in the reader's browser (per device and per browser, never shared) would bring JavaScript into the site, and the EPUB would not carry it. Browser storage for pages opened as local files (`file://`, which F-1 supports) differs between browsers. "Spoilers" would be the answers revealed (the `<details class="answer">` opened) at critical moments. Shaped below. |
| F-9 | "A list of proposed quiz, starting from your worse blunder, assuming the game are yours." | requested | | Asked by the owner on 2026-09-25, after F-6 landed, as one of four requested features (F-8 to F-11). Not shaped yet. The owner decided on 2026-09-25 that F-8 to F-11 come before F-1.3. Notes for shaping: the player's own critical moments across all games, as a list of questions ordered from the worst (most winning chances lost) down, each linking to its position (every moment has a `moment-N` anchor). It relates to F-1.3's selection of best games. |
| F-10 | "A link in critical position to a pop up link, where you can start stockfish and analyze the current position" | requested | | Asked by the owner on 2026-09-25, after F-6 landed, as one of four requested features (F-8 to F-11). Not shaped yet. The owner decided on 2026-09-25 that F-8 to F-11 come before F-1.3. **Owner decision (2026-09-25): a link that opens the position on lichess's analysis board** (by FEN). It was recommended as the default because it needs no JavaScript and no bundled engine, and brings in no licence question, at the cost of needing the network and a third-party site. The alternative not chosen was Stockfish in the browser (a bundled WebAssembly build: offline, several MB per site, JavaScript, and Stockfish's GPL licence; see F-1's licence question). Also in the owner's words (2026-09-25): "Another feature to add is having a link to open the full PGN game on lichess,". **Owner decision (2026-09-25): that request is part of F-10**, recommended as the default because both are plain links to lichess (the position's analysis board and the whole game), shaped and built as one iteration. The alternative, a separate request, was not chosen. |
| F-11 | "The possibilty to add notes in critical positions, also as a pop up-" | requested | | Asked by the owner on 2026-09-25, after F-6 landed, as one of four requested features (F-8 to F-11). Not shaped yet. The owner decided on 2026-09-25 that F-8 to F-11 come before F-1.3. Notes for shaping: with no server, notes would live in the reader's browser (per device), which brings JavaScript into the site (see F-8), and the EPUB would not carry them. Browser storage survives a rebuild of the site; the risk is a page renamed when a game's id changes (a corrected `Date` or `Result`, see F-7). Keeping notes across devices would need an export/import to a file, or a write-back into the owner's repository (the pipeline, F-3). How notes are kept is an owner decision. |

## Accepted requests

### F-1 — A library: from a PGN collection to a Wikipedia-style site and an EPUB

- **Original request:** "first publishing a pip / python library that creates a wikipedia / epub from a pgn collection"
- **Also in the owner's words** (the same session, 2026-09-24; confirmed by the owner that day): "I would like to read a book about
  me and my best and worst games like I was Fischer or Capablanca"; ""worst games" is kind of a
  bad idea, "best games that I lost", not just blunders.  But all games must be there, wikipedia
  style."; "in English, German comments are from old engines, strip comments and variants from
  games. But it is more about the idea that we need games collections as sources"; "Yeah I need to
  use my old games because as of now I totally suck at chess".
- **Player value:** a player gets to reread years of their own games as a book about themselves,
  the way the classic "My Memorable Games" collections read, from whatever PGN files they already
  have, offline and on a phone, without operating a chess GUI or a website. The owner's own case is
  about 1,800 games (as counted by the spike on `book-poc`), scattered across a git repository of
  PGN collections, chess.com and lichess.
- **Scope:** after F-1 lands, an installable Python library (API and command line) takes one or more
  PGN collections and a player (a name plus aliases) and writes:
  - a **static Wikipedia-style site**: a career article about the player (an infobox, career by
    year, repertoire, frequent opponents, notable games), featured chapters (**best wins, best
    losses, best draws**), an article for **every** game (an infobox, a lead paragraph, the moves
    with notes and captioned diagrams at the critical moments, a conclusion, the PGN), a game index
    by year, and a revision mode ("what would you play?", answer revealed on tap). It works offline
    and from `file://`, and reads well on a phone.
  - an **EPUB 3** of the same book.

  Its input handling: multi-game files are read in full; the player's games are kept by name or
  alias; duplicates are kept once, by content; everything the source attaches to the moves —
  comments (including any `[%eval]`), variations and NAGs — is stripped. **Every game is
  re-analyzed by the library itself** (the slot's *decided* list): analysis runs Stockfish where
  the user runs the library, in parallel, and is incremental only in that a game the library has
  already analyzed (in its own output) is not analyzed again. The library's output carries standard
  `[%eval]` comments. The site can also be built from games not analyzed yet: every game still gets
  an article, with no selection and no critical moments. All prose comes from templates (the LLM is
  F-2). It is released on PyPI.
- **The split** — F-1 is larger than one iteration, so it lands as four, in this order; each is one
  session, one branch, one review, one merge (`PLAN.md`):

  | slice | lands | done when |
  |---|---|---|
  | **F-1.1** — read and analyze | the library package with its API and command line; reading PGN collections (files, directories, globs) with player aliases, content-based duplicate removal and stripping; the parallel, incremental Stockfish step writing `[%eval]`; the Python version of open question 3 in `pyproject.toml`, the CI matrix and the gates table | the gates pass, including new tests that: read a multi-game file whole; collect files through a glob across directories; keep only the player's games under any alias; keep a game found in two files once; strip comments (a source `[%eval]` included), variations and NAGs; analyze a forced mate and flag it with `[%eval]` output (Stockfish test, as today); analyze nothing on a second run over the same games; give the same output with two workers as with one; and run the command line end to end on a fixture collection (read, then analyze) as a subprocess. Each new assertion is shown failing before it passes (`PRINCIPLES.md`) |
  | **F-1.2** — every game as an article | the static site: an article for every game, the game index by year, the diagrams (HTML/CSS boards), the template prose, the revision mode; building from games not analyzed yet | the gates pass, including: a golden-file test that a small fixture collection renders to committed pages byte for byte; a test that the site has one article per game and no broken internal links; a test that every critical moment in the fixture has its revision-mode question and hidden answer; a test that a fixture with no analysis still builds one article per game with no critical moments. Then, before merging, the owner opens the fixture site on a phone and from `file://` and records the verdict as a comment on the slice's pull request; a "no" sends the slice back to the builder and it does not merge; the completion note transcribes the verdict |
  | **F-1.3** — the book around the games | the career article; the selection of best wins, best losses and best draws; the chapters; the demo collection of open question 7, committed with its source named | the gates pass, including tests that the selection ranks hand-made fixture games as intended (a hard-fought loss above a loss decided by one early blunder; a draw saved from a lost position; no game in two chapters) and a golden-file test of the career article on the fixture. Then, before merging, the owner reads the book built from the demo collection and records on the slice's pull request whether the chapter picks are right; a "no" sends the slice back with what to change, and it does not merge; the completion note transcribes the verdict |
  | **F-1.4** — EPUB and release | the EPUB 3 writer (carrying no script: F-8's history is for the site only); packaging and documentation; the demo book; a test in the tests gate that validates the demo EPUB with `epubcheck` (the Ubuntu package, installed in CI; skipped locally when `epubcheck` is missing, as the Stockfish test is), with the tests row of the gates table updated in the same change; a tag-triggered trusted-publishing workflow for PyPI | the gates pass, the `epubcheck` test included; before merging, the owner opens the demo EPUB in the e-readers of open question 8 and records the verdict on the slice's pull request (a "no" sends it back and it does not merge). After the merge, **the owner publishes the release** — pushing the tag that triggers the workflow, or uploading it; the builder never handles PyPI credentials. F-1.4, and with it F-1, is complete only when `pip install <name>==<version>` from PyPI in a clean environment builds the demo book; the completion note records the PyPI URL and that run |

- **Done when:** all four slices have landed as above.
- **Out of scope** (recorded so it is not lost):
  - LLM-written prose — F-2.
  - Fetching from chess.com, lichess or git repositories, the `pgn-postmortem.toml` workspace config,
    publishing to folders, cloud storage, GitHub Pages or e-mail, a Docker image, a GitHub
    template repository, scheduling — F-3.
  - PDF output and a single-file HTML version — later, not yet requested.
  - Trusting evals that source PGNs already carry: it would re-open *every game is re-analyzed*
    (the `CLAUDE.md` slot), so it is not proposed.
  - Analyzing the owner's whole archive: it runs only when the owner asks (`CLAUDE.md`,
    *conventions*); fixtures and the demo collection are enough to build and test F-1.
  - Book languages other than English.
  - Changing the current Markdown pipeline (`scripts/`, `examples/docs/`, the Pages demo), beyond
    what open question 4 decides.
- **Depends on:** nothing. (The harness is adopted; `book-poc` holds spike code that F-1.1 may reuse,
  see open question 5.)
- **Open questions** — owner decisions, each with a recommended default, its reason, and the slice
  that cannot start before it is answered:
  1. **Owner decision — package name** (before F-1.1). Default: **`pgn-postmortem`**, the current
     repository name — no rename of the repository, the demo URL or the README, and it was free on
     PyPI on 2026-09-24. Alternatives: `pgnbook`, `pgn-memoir`, `chess-memoir` (also free then); a
     name that says "book" describes the product better.
     **Decided by the owner on 2026-09-24: `pgn-postmortem`** (the default).
  2. **Owner decision — licence** (before F-1.4). Default: **keep MIT**. python-chess is GPL-3.0+;
     a PyPI package that depends on it without bundling it can be MIT. Revisit in F-3 if a Docker
     image bundles it. Alternative: GPL-3.0, which removes the question.
     Settled with it, before F-1.4: the licence of the board pieces' artwork that every generated
     site embeds (Colin M.L. Burnett's set as bundled with python-chess; unverified, since
     python-chess ships no notice for it; review 008, finding 5).
  3. **Owner decision — Python version** (before F-1.1). Default: **3.11 or newer**: Python 3.10
     reaches its end of life in October 2026, before F-1 can be released. F-1.1 then moves the CI
     matrix and the gates table from 3.10/3.12 to 3.11/3.13. Alternative: keep 3.10 until F-1.4.
     **Decided by the owner on 2026-09-24: 3.11 or newer** (the default).
  4. **Owner decision — the current Markdown pipeline** (before F-1.4). Default: **keep it
     unchanged until F-1.4 lands**, then decide whether to retire it or keep it as a second
     renderer; the live demo keeps working meanwhile.
  5. **Owner decision — the spike on `book-poc`** (before F-1.1). Default: **F-1.1 reuses the
     reading, duplicate removal and parallel analysis code** (already run on real data), reviewed
     like any new code, and leaves the fetching and config code for F-3.
     **Decided by the owner on 2026-09-24: reuse those parts** (the default).
  6. **Owner decision — the evals format** (before F-1.1). Default: **the library writes standard
     `[%eval]` comments** in its own output; the current scripts keep their own `{ +0.23 }`
     comments, so their golden files do not change.
     **Decided by the owner on 2026-09-24: standard `[%eval]`** (the default).
  7. **Owner decision — the demo collection** (before F-1.3). Default: **Capablanca's games** from a
     public source whose terms allow redistribution; the builder proposes the source when F-1.3 is
     shaped for its session, and it is named in the README.
  8. **Owner decision — the e-readers the EPUB must work in** (before F-1.4). Default: **Apple
     Books and Kindle** (via Send to Kindle). Alternative: add Google Play Books, which
     `docs/book-plan.md` lists too.
  9. **Owner decision — selection weights** (before F-1.3). Default: tune them on fixtures and the
     demo collection in F-1.3; tuning on the owner's archive needs it analyzed, which happens only
     when the owner asks.

### F-5 — A result for games whose result was not recorded

- **Original request:** "There are a few where the results is not recorded, default to victory for the one with much higher winning chances, or draw if unclear."
- **Player value:** every game in the book reads as finished. Today a game with an unrecorded result
  shows "\*" in the infobox, at the end of its moves and in "The game ended \* after …". In the
  owner's own book that's 12 of the 148 over-the-board games. F-1.3's chapters (best wins, losses,
  draws) also need a result for every game.
- **Scope:** for a game whose `Result` is `*` or missing, the book shows a result in this order:
  1. **The board decides it** if the final position is checkmate (the mating side wins), or is
     stalemate or has insufficient material (a draw). This applies whether or not the game is
     analyzed.
  2. **Otherwise it is presumed from the analysis,** if the game carries the library's analysis and
     its final position has an eval, whether in centipawns or a mate score (`[%eval #N]`): a win
     for the side with **at least 70% winning chances**, using the same win-percentage model as the
     move grading (a forced mate counts as 100%), and a draw otherwise.
  3. **Otherwise** the book says the result was not recorded.

  The result is **shown exactly like a recorded result**, with no marker, everywhere the site shows
  a result outside the PGN section: the infobox, the lead, the end of the moves, the conclusion and
  the index. The game's PGN is untouched. Its `Result` header stays as the source had it, so the
  game's identity (which includes the result), its file names and its analysis don't change, and
  the article's PGN section shows the source as is.

  The threshold is a library parameter with 70% as its default. It must be at least 55% and at most
  95%; any other value is rejected with an error. The conclusion's wording must agree with the
  result shown: a presumed win is never described as a result that "came from outside the position".

  The same change fixes a defect found in the owner's book: the conclusion's counts pluralize
  "inaccuracy" as "inaccuracys".
- **Done when:** the gates pass, including tests on fixtures. These are small synthetic PGNs that
  carry the library's analysis marker header and hand-set `[%eval]` comments. They are written for
  these tests, not produced by Stockfish, and live in their own directory
  (`tests/fixtures/site/synthetic/`), documented there as hand-written. They are not under the
  generated `tests/fixtures/site/analyzed/`. The tests check that:
  1. an unrecorded game ending at about 72–75% for White shows 1–0 in the infobox, lead, end of the
     moves, conclusion and index;
  2. one ending at about 25–28% for White shows 0–1, and one ending at about 32–35% for White shows
     ½–½;
  3. one ending at about 65–68% for White shows ½–½, which proves the default threshold is 70%, not
     60%;
  4. the 72–75% game shows ½–½ when the threshold parameter is set to 80, which proves the parameter
     is used;
  5. a threshold below 55 or above 95 is rejected;
  6. an unrecorded, unanalyzed game ending in checkmate shows the mating side's win, and ones ending
     in stalemate or with insufficient material show ½–½;
  7. an unrecorded, analyzed game whose final eval is a mate score (`[%eval #N]`, not checkmate on
     the board) shows the win of the side with the mate;
  8. an unrecorded game that is neither analyzed nor ended on the board shows "not recorded" wording,
     and no bare "\*" appears anywhere outside the PGN section;
  9. the PGN `Result` header, the `PostmortemId` and the file names of all these games are unchanged;
  10. counts read "inaccuracies" when there are two or more.

  Each new assertion is shown failing first. The golden files are regenerated where the output
  changes.
- **Out of scope:**
  - writing a presumed result into any PGN;
  - how F-1.3 uses presumed results in its selection (F-1.3's own shaping);
  - diagrams for moves that changed the expected result, which is F-6;
  - presuming anything for a game whose `Result` is recorded, even if it contradicts the final
    position;
- **Depends on:** F-1.2 (landed).
- **Open questions:** none remain. The owner decided on 2026-09-24, each against a recommended
  default:
  - **Owner decision: a presumed result is shown as the result, without a marker.**
    - Recommended default: mark it "presumed", so the book doesn't state as fact what the source
      didn't record.
    - Owner's choice: no marker, so the book reads as complete. The source's "\*" stays visible in
      each article's PGN section.
  - **Owner decision: the threshold is 70%.**
    - Recommended default: 80% (about +3.8 pawns), so that only clearly won positions become wins.
    - Owner's choice: 70% (about +2.3 pawns). Any value from 55% to 85% gives the same results for
      all 12 of the owner's games.
  - **Owner decision: F-5 lands now, before F-1.3.**
    - Recommended default: the same.
    - Reason: F-1.3's selection of best wins, losses and draws needs a result for every game.

### F-6 — More diagrams: the moves that changed the expected result

- **Original request:** "I am looking at the games and I think there should be more diagrams, for instance in this game https://diegoami.github.io/chessgamescollection/games/2008-01-04-4e5d4e182f.html just an error is shown that did not affect the end result. It was move 40 that was deciding, not 31"
- **Player value:** the book shows where a game was really decided, not only where a single move lost
  a lot. Today a question is asked only at a critical moment, a move that costs at least 20 points
  of winning chances. A game is often decided by smaller moves that tip it from level to lost, or
  from won to level.
  - **The owner's example:** Pedroni – Amicabile, Festival Verona 2008. It shows only 31… Qa2? (a
    28-point mistake that didn't change the result). The moves that did were 37… Rg2+ (White from
    25% to 41%, 16.4 points) and 40. Ra4 (49% to 32%, 17.0 points). With the 40–60% band below,
    15. Nxc5 (47% to 37%) is a question too, so the example game's questions are 15. Nxc5,
    31… Qa2, 37… Rg2+ and 40. Ra4.
  - **On the owner's 148 analyzed OTB games,** the rule below adds 285 questions in 109 games, on
    top of 390 critical moments (675 in all). Another 318 swings are already critical moments. The
    orchestrator computed the counts on 2026-09-25 from the owner's analyzed files, with the
    library's win-percentage model and the rule as written, at the 40–60% band.
- **Scope:** each analyzed position gets an *expected outcome* from White's winning chances after
  the move:
  - **White winning** at 60% or more;
  - **Black winning** at 40% or less;
  - **level** in between.

  A move is an **outcome swing** when all three hold:
  1. it makes the expected outcome worse for the side that played it (winning → level, level →
     losing, or winning → losing);
  2. it cost that side at least as many points of winning chances as the inaccuracy threshold in
     use (10 by default, the decided grading), so that every swing is a graded move. With custom
     `thresholds`, the floor follows the inaccuracy threshold; it is not a new parameter;
  3. **a better move exists**: the engine's first choice in the position before differs from the
     move played. The first choice is read from the stored analysis as the first move of **any**
     engine line stored at that position: the move's own better line, or the previous move's
     refutation, which is the engine's line from the same position. If no line is stored there,
     the move played was the first choice. "A line is stored before the move" is **not** the test,
     because the previous move's refutation is stored there too and can start with the move played,
     as in all 3 exclusions below.

  Condition 3 matters because a move that was the engine's own first choice is not an error: its
  drop comes from the engine's search limit. There is also nothing better to show as the answer.
  In the owner's book this excludes 3 of 288 candidates: 45… Qa6 and 47… Qa6 in
  `2005-09-24-3bd9df323c`, and 18. Qxd4 in `2008-01-05-ec4df50311`.

  Every outcome swing that is not already a critical moment **becomes a critical moment too.** It
  gets a diagram, a "what would you play?" question, the engine's better line and, when the analysis
  has one, the refutation. There is none after a game's last move. It counts in the infobox's
  number of critical moments and in the lead's. The lead's description of a critical moment must
  stay true: today it says each one "cost at least 20 points", and with F-6 it must say "cost at
  least 20 points or changed the expected result".

  The note in the moves says how the expected result changed (e.g. "level → losing"). This applies
  to swings, and also to the 318 critical moments that are swings too (e.g. "a mistake that turned a
  level game into a losing one"). A move that is both is shown once.

  The bands are a library parameter pair with 40/60 as the default. The pair is valid only if both
  are finite numbers, the lower is above 0 and below 50, and the upper is above 50 and below 100. It
  is checked up front before anything is written, even for an empty collection, as F-5's threshold
  is. The rule uses only the analysis that exists, so nothing is re-analyzed and no Stockfish run is
  needed.
- **Done when:** the gates pass, including tests on synthetic fixtures (hand-set `[%eval]`s, in
  `tests/fixtures/site/synthetic/` or a sibling directory, documented as hand-written) that:
  1. a White move from level to Black winning, and a Black move from Black winning to level, each
     costing 10–20 points with a different engine first choice, become critical moments with
     question, better line and refutation, and their notes say how the expected result changed;
  2. a move that changes the band **in favour of** the side that played it is not a moment;
  3. a band change costing less than 10 points is not a moment;
  4. a 10–20-point loss that stays inside one band is not a moment;
  5. a 10–20-point band change whose move **was the engine's first choice** is not a moment, both
     with no line stored before it and with the previous move's refutation as the only line there,
     starting with the move played (the shape of the owner's 3 exclusions);
  6. a move that is both a 20-point critical moment and a swing is shown once, and its note says the
     expected result changed;
  7. **the edges and the parameter:**
     - White's chances exactly at the upper edge count as White winning, and exactly at the lower
       edge as Black winning. This is tested by setting the parameter to a fixture's exact value,
       since a hand-set `[%eval]` can't hit 60.000%.
     - A changed band pair changes the moments.
     - Invalid pairs are rejected up front, even for an empty collection: lower ≥ upper, a value
       outside its half, and NaN;
  8. **the counts and the lead:** in a game whose only critical moments are swings, the infobox count
     and the lead count them, and the lead's wording is true for them;
  9. unanalyzed games still have no moments.

  Then there are two checks:
  - **Golden files:** they are regenerated with the documented command where output changes, and
    the PR says which pages changed and why.
  - **The owner's verdict:** before merging, the owner's book is rebuilt locally from the branch,
    with no re-analysis. The owner checks the example game shows 15. Nxc5, 31… Qa2, 37… Rg2+ and
    40. Ra4, and records a verdict on the PR. A "no" sends it back.

  Each new assertion is shown failing first.
- **Out of scope:** re-analyzing games; changing the 20-point critical-moment line or the grading
  thresholds (decided); F-1.3's use of swings in its selection (its own shaping); F-7.
- **Depends on:** F-5 (landed), F-1.2 (landed).
- **Open questions:** decided by the owner, each against a recommended default:
  - **Owner decision (2026-09-24): which moments get extra diagrams.**
    - Offered: "the deciding moment", "inaccuracies too" and "swings that changed the outcome".
    - Recommended default: the deciding moment. It is one diagram per decisive game, which keeps
      articles short and marks exactly the move the owner pointed at.
    - Owner's choice: **swings that changed the outcome**, which covers every move that changed the
      expected result, not only the last.
  - **Owner decision (2026-09-25): the level band is 40–60%.**
    - Recommended default: 35–65%, because a narrower 30–70% band misses the owner's own example,
      40. Ra4 (49% → 32%). The owner first chose it, on 2026-09-25.
    - Owner's choice, changed the same day after checking the preview of the book built from this
      iteration's branch (pull request #15): **40–60%**, because 15. Nxc5 (47% → 37%) in the example
      game should be a question too. A narrower 45–55% band would lose 37… Rg2+ (25% → 41%).
  - **Owner decision (2026-09-24): when.**
    - Recommended default: right after F-5, before F-1.3, so that F-1.3's selection can use the
      swings.
    - Owner's choice: the recommended default.
  - **Proposed with this shaping, confirmed by the owner's merge:** a swing must cost at least 10
    points (the inaccuracy threshold), and a better move must exist.
    - Recommended default: yes. Only then does every question have a real better move as its
      answer, and small crossings near a band edge are noise.
    - On the owner's book this adds 285 questions in 109 games (at the 40–60% band).
    - Alternative: any band change, which would need re-analysis or questions without an answer.

### F-8 — A reading history in the reader's browser

- **Original request:** "A local history reminding what games have you been watching and ideally the spoilers you have looked"
- **Player value:** on the road, the reader sees at a glance which games they have already opened and
  how many of each game's answers they have already revealed, so they can go back to the questions
  they haven't seen yet.
- **Scope:** a small script, written into each page. It uses no libraries and makes no network use.
  It keeps a reading history in the reader's own browser (`localStorage`), per device and per
  browser, never shared and never sent anywhere.
  - **What it records:**
    - a game as **viewed** (with the time) when its article is opened;
    - an answer as **revealed** when its "what would you play?" answer (`<details class="answer">`) is
      opened.
  - **The history belongs to one site.** Browser storage is shared by every page of one origin:
    all of a user's GitHub Pages sites under one `github.io` domain share one (a site on its own custom
    domain has its own), and some browsers give every local `file://` page the same one. So:
    - every stored key starts with a prefix of the tool's own plus a **site key**. The site key is
      written into the pages at build time, so it survives rebuilds. By default it is derived from the
      site's title, which is what `build_site` receives; a `site_key` parameter (and a command-line
      option) can set it explicitly. Two books with the same title on one origin share one history,
      and "Clear history" on one clears both. This is accepted, because the limit of 10 below is
      applied after filtering to the index's own games, so each book still shows only its own games,
      and an explicit site key separates them;
    - "Clear history" removes only keys with that prefix and site key;
    - "Recently viewed" and the marks show only games that are in the index's current list.
      Anything else stored (other books, games that no longer exist) is ignored.
  - **The data in the pages.** For the script, the pages carry a few `data-` attributes, and only
    these:
    - each article: its game id (`PostmortemId`);
    - each answer: the move it is about (move number and side, e.g. `31b`);
    - each game in the index: its id and the moves of its current questions;
    - every page (on `<html>`): the site key.

    Answers are keyed by move, not by the moment's number, which can change when the rules for
    critical moments change (as F-6 did). A game's "k/m" counts only revealed answers whose move is
    among the game's current questions, so m is the current number of questions.
  - **The index shows:**
    - a **"Recently viewed"** list at the top, newest first: the latest 10 of this index's own games
      (filtered first, then limited), so it fits a phone screen without scrolling;
    - in the game list, a **mark** on each viewed game, with how many of its answers were revealed
      out of its current number of questions (e.g. "2/4").
  - **A "Clear history" button** on the index removes the site's history after the reader confirms.
  - **Everything still works without the script.** The history parts are in the HTML with the
    `hidden` attribute and are shown only by the script. With scripts off, or where the browser gives
    no storage (some private windows; some browsers for `file://` pages), the pages read exactly as
    today.
  - **The history can be lost:** when the reader clears the browser's data; in Safari, which deletes
    script-written storage after 7 days without a visit; and for one game, when its id changes (a
    corrected `Date` or `Result`, see F-7). It is a convenience, not a record.
  - **Where the script lives:** one file in the package (`pgn_postmortem/static/history.js`),
    declared as package data. The site builder inlines it into every page, the same bytes in every
    page. `README.md` and `pgn_postmortem/site.py` stop saying "there is no JavaScript" and describe
    the optional history script instead.
  - **The EPUB (F-1.4) carries no script.**
  - **A switch:** `build_site(..., history=False)`, and a `--no-history` option on the `site` command,
    build the pages without the script, the containers and the `data-` attributes.
- **Done when:** the gates pass, including:
  1. **Python tests on the pages:**
     - every page carries the script inline, byte-identical to `pgn_postmortem/static/history.js`,
       with no `src` attribute;
     - the script contains no URL and no network or loading call: no `fetch`, `XMLHttpRequest`,
       `sendBeacon`, `WebSocket`, `EventSource`, `import(` or `importScripts`;
     - the history containers carry `hidden` in the static HTML;
     - **two golden sets:**
       - the pages without the history, built with `--no-history` into their own directory
         (`tests/golden/site-no-history/`), are **byte-identical to today's golden pages on `main`**.
         That proves `history=False` changes nothing. From then on the set is regenerated with its
         own documented command, never edited by hand;
       - the pages with the history go in `tests/golden/site/`, regenerated with the documented
         command;
     - **the history adds nothing else:** a test strips the script, the history containers and the
       `data-` attributes from every page with the history, and finds exactly the page without it;
     - **the package ships the script:** in CI, a step builds the wheel (`pip wheel --no-deps
       --no-build-isolation .`, with `setuptools` pinned in `requirements-dev.txt`) and checks it
       contains `pgn_postmortem/static/history.js`. Keeping this in CI keeps the local tests gate
       free of the network.
  2. **A new gate, "script"**, with the command `node --test 'tests/js/*.test.mjs'`. It must be a glob:
     on Node 21 and newer a bare directory fails, and the explicit path keeps the gate out of
     `.claude/worktrees/`. A glob that matches no file passes with 0 tests, which would be a false
     green. So a Python test asserts the test files exist, and the gate's reported test count is
     shown in the pull request. It uses Node's built-in test runner and no npm packages, and the
     script's logic is written so it can be tested with a stand-in storage and page. The tests
     cover:
     - opening an article records the game as viewed;
     - revealing an answer records it once, keyed by move;
     - the index lists the latest 10 games newest first, and only games in its current list;
     - the "k/m" mark counts only answers of the game's current questions;
     - "Clear history" removes this site's keys only, and only after the confirmation; another site
       key's data and unrelated keys survive;
     - storage that throws or is missing leaves the page working with the history hidden;
     - corrupt stored data is ignored, not trusted.

     **Gate details for the table:** it runs on every change, locally and in CI, with 1 repeat, and
     it is deterministic. CI pins Node 22 with `actions/setup-node`. Locally it needs Node 22 or
     newer; without Node the builder says so in the pull request, and CI's run decides.
     `CLAUDE.md`'s gates table gets the row, and "only the two gates above decide a merge" becomes
     three.
  3. **The owner's check:** before merging, the owner's book is rebuilt from the branch (no
     re-analysis). The owner opens some games on a phone and on a desktop browser, both online and
     from `file://` on the desktop, reveals some answers, and checks the index's "Recently viewed"
     list, the marks and "Clear history". The verdict is recorded on the PR, and a "no" sends it back.

  Each new assertion is shown failing first.
- **Out of scope:**
  - syncing or exporting the history across devices (not chosen);
  - notes (F-11);
  - the quiz list (F-9);
  - the engine link (F-10);
  - marks inside articles (not chosen);
  - any server or network use.
- **Depends on:** F-6 (landed).
- **Open questions:** decided by the owner on 2026-09-25, each against a recommended default:
  - **Owner decision: a small inline script is allowed.**
    - Recommended default: yes. There is no static way to remember what a reader viewed, and the
      pages stay complete without it.
    - Owner's choice: the recommended default.
  - **Owner decision: where the history shows.**
    - Recommended default: a "Recently viewed" list on the index and marks in the game list. The
      third option offered, marks on the revealed answers inside articles, was not recommended.
    - Owner's choice: the recommended default.
  - **Owner decision: this browser only, with a reset.**
    - Recommended default: the same, because anything more needs a file export or a server.
    - Owner's choice: the recommended default. Export/import, the alternative, was not chosen.
  - **Proposed with this shaping, confirmed by the owner's merge:**
    - the limit of 10 recent games, so the list fits a phone screen;
    - answers keyed by move, and the `data-` attributes that carry the ids and moves;
    - a site key for the history's storage (from the title by default, settable with `site_key`),
      and a clear that removes only that site's history;
    - the `history=False` switch and the `--no-history` option, with the second golden set;
    - the new "script" gate, with Node 22 pinned in CI.

## Statuses

`requested` → `accepted` → `in design` → `in review` → `landed`; plus `parked`
and `refused`. The agent sets the middle states. **Only the owner parks or
refuses**, and the reason is recorded.

## How to request

Add one row to the table, in your own words — or say it in a session ("add to
the roadmap: …") and the agent appends the row and stops. **A request is not a
request to implement**: the shaping and the design stage still happen, and the
original wording is quoted verbatim in the block and never silently reworded.

## The block, written when a request is accepted

```
### F-N — <title>
- **Original request:** "<verbatim>"
- **Player value:** why this matters
- **Scope:** what will exist after it lands
- **Done when:** the runnable checks
- **Out of scope:** the temptations deferred, so they are recorded not lost
- **Depends on:** other requests, or none
- **Open questions:** owner decisions marked as such
```

## The agent's job

- **Shape** a request when it is picked up: player value, scope, done-when,
  out-of-scope, dependencies, open questions. The shaping *is* the design
  stage — in OpenCode mode it becomes the design record, in Claude mode the
  brief.
- **Size it to one iteration.** Split before starting if it does not fit; never
  let a task grow while in flight.
- Take the **first unblocked** request when told "do the next roadmap item",
  and stop after it.
- Never implement an unshaped request; never mark an owner status; never edit
  the original wording.

## Artistic license

In this project the product is the deliverable, so the license is narrower than
in a process testbed. The agent has **artistic license inside a request**:

- invent the names, the template prose, the layout and styling, the small
  mechanics;
- implement the thing that reads best, not the thing that follows the request
  word for word;
- record what was invented, so the choice is visible and reversible;
- do not ask the owner about wording, names, or flavour.

What the license does not cover: **the intent of the request**, **scope**, **the
done-when and the gates** (extendable with the reason recorded, never
weakened), and **owner decisions**.

The request is a direction; the done-when is the contract.

## How it plugs into the rest

- **Iterations after the scaffold are the landed requests**, in order.
- **When GitHub exists**, each row becomes an issue, with the block as its body
  and the status as a label; the posting rule is in `PRINCIPLES.md`.
- **A comparison run copies a frozen subset** as its task list: same text, same
  base commit, same gates for every arm.
- The design and review records refer to the request id.
