# Roadmap — requests and iterations

> How the project grows. The owner writes requests; the agent shapes them; an
> accepted request is one iteration, one session and one review
> ([`PLAN.md`](PLAN.md), when the overlay is used).

## The queue

The owner confirmed on 2026-09-24 that the quoted wording of F-1 to F-3 is the owner's own.

| id | request | status | iteration | notes |
|---|---|---|---|---|
| F-1 | "first publishing a pip / python library that creates a wikipedia / epub from a pgn collection" | accepted | 1, 2, 4, 5 (F-1.1 to F-1.4; iteration 3 is F-5) | The direction is in [`docs/book-plan.md`](docs/book-plan.md), *Layer 1*. Also in the owner's words: "I would like to read a book about me and my best and worst games like I was Fischer or Capablanca"; ""worst games" is kind of a bad idea, "best games that I lost", not just blunders.  But all games must be there, wikipedia style."; "in English, German comments are from old engines, strip comments and variants from games". Spike code on the branch `book-poc`. |
| F-2 | "Yes, LLM, but of course Claude with API key would be too expensive, Deepseek is the realistic option, BYOK for other users" | requested | | The book's prose. Depends on F-1. `docs/book-plan.md`, *Prose*. |
| F-3 | "then wire that into a pipeline that may fetch games from somewhere on the input or put the published files somewhere on the output" | requested | | Depends on F-1. Also in the owner's words: "as sources it must be able to parse a collection of games"; "if it has to be reusable we have to think about people who do not have a github, so output must be pluggable somehow"; "I am not maintaining their repository or web pages". `docs/book-plan.md`, *Layer 2*; the chess.com, lichess and git sources exist as spike code on `book-poc`. |
| F-4 | "yes, queue the name matching improvement" | requested | | Raised in the owner's own trial run (2026-09-24), in the owner's words: "Why are there games that are not mine, they might be mislabeled". Reading the owner's 149 OTB games kept 140 and left out 8 of the owner's own, spelled `Amicabile Diego` and `Diego , Amicabile`, because player names match exactly except for letter case, so every spelling needs its own alias. The implementer's proposal, to be shaped when picked up: match names ignoring spacing, commas and word order; and have `read` report the names seen most often in the games it left out, so a missed alias is easy to spot. Touches F-1.1's reading; the owner decides at shaping whether it lands before F-1.3 or within it. |
| F-5 | "There are a few where the results is not recorded, default to victory for the one with much higher winning chances, or draw if unclear." | accepted | 3 | Raised on the owner's own book (2026-09-24): 12 of the 148 OTB games, all from 2012, have no recorded result. Shaped below. |
| F-6 | "I am looking at the games and I think there should be more diagrams, for instance in this game https://diegoami.github.io/chessgamescollection/games/2008-01-04-4e5d4e182f.html just an error is shown that did not affect the end result. It was move 40 that was deciding, not 31" | requested | | The owner's choices on 2026-09-24, when asked which extra moments should get a diagram: "Swings that changed the outcome" (a move that changes the expected result, e.g. winning → level or level → losing, even below the 20-point critical-moment line), not the other two options offered ("the deciding moment" and "inaccuracies too"); and when: "Right after F-5, before F-1.3". The owner's example game (Pedroni vs. Amicabile, Verona 2008) has only 31... Qa2? as a critical moment; 37... Rg2+ (25% → 41% for White) and 40. Ra4 (49% → 32%) changed the outcome but cost 16 and 17 points. Not shaped yet; it is shaped after F-5's shaping lands. |

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
  | **F-1.4** — EPUB and release | the EPUB 3 writer; packaging and documentation; the demo book; a test in the tests gate that validates the demo EPUB with `epubcheck` (the Ubuntu package, installed in CI; skipped locally when `epubcheck` is missing, as the Stockfish test is), with the tests row of the gates table updated in the same change; a tag-triggered trusted-publishing workflow for PyPI | the gates pass, the `epubcheck` test included; before merging, the owner opens the demo EPUB in the e-readers of open question 8 and records the verdict on the slice's pull request (a "no" sends it back and it does not merge). After the merge, **the owner publishes the release** — pushing the tag that triggers the workflow, or uploading it; the builder never handles PyPI credentials. F-1.4, and with it F-1, is complete only when `pip install <name>==<version>` from PyPI in a clean environment builds the demo book; the completion note records the PyPI URL and that run |

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
  6a. an unrecorded, analyzed game whose final eval is a mate score (`[%eval #N]`, not checkmate on
     the board) shows the win of the side with the mate;
  7. an unrecorded game that is neither analyzed nor ended on the board shows "not recorded" wording,
     and no bare "\*" appears anywhere outside the PGN section;
  8. the PGN `Result` header, the `PostmortemId` and the file names of all these games are unchanged;
  9. counts read "inaccuracies" when there are two or more.

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
