# Review 003 — Shape F-1, implementation round 01

- **Revision covered:** `103a165f635508af1d5b1dbe22bead26be590eb8` (branch `shape-f1`, pull
  request #3).
- **Target proof:** `git rev-parse shape-f1` gives `103a165f635508af1d5b1dbe22bead26be590eb8`, which
  equals `gh pr view 3 --json headRefOid` (`103a165f…`). The checked-out `HEAD` is the same
  revision.
- **Files checked:** `PLAN.md`, `ROADMAP.md`. Obtained from `gh pr view 3 --json files` and from
  `git diff --name-only $(git merge-base main shape-f1)..shape-f1`; the two lists are equal.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that did not
  see the implementation.
- **Mode:** Claude Code.

## What I checked, and how

- The rules were read on `main`: `PRINCIPLES.md`, `CLAUDE.md` (the project slot), `ROADMAP.md`,
  `PLAN.md`, `reviews/README.md`, and `docs/book-plan.md`.
- **The gates, on `103a165`:**
  - `.venv/bin/python -m ruff check .` → `All checks passed!`
  - `.venv/bin/python -m pytest -q` → `30 passed`. Stockfish is at `/usr/games/stockfish`, so the
    smoke test ran and was not skipped.
- **Block fields:** every field of the format in `ROADMAP.md` (*The block*) is present:
  - original request, player value, scope, done when, out of scope, depends on, open questions;
  - also the split, as *The agent's job* asks.
- **Original wording:** the *Original request* line (`ROADMAP.md:21`) matches the F-1 row on `main`
  byte for byte. The row's request cell is unchanged. Only its status (`accepted`, a middle state the
  agent may set) and its iteration cell change.
- **Owner decisions:** all nine open questions (`ROADMAP.md:74-99`) carry the owner-decision mark, a
  recommended default and a reason, as `PRINCIPLES.md` (*Owner decisions*) requires.
- **Factual claims, reproduced:**
  - `pip show chess`: 1.11.2, `License: GPL-3.0+`. PyPI metadata agrees (GPLv3+).
  - PyPI names: `pgn-postmortem`, `pgnbook`, `pgn-memoir` and `chess-memoir` all return HTTP 404,
    so they are free.
  - `main`'s `LICENSE` and `pyproject.toml` are MIT, so "keep MIT" describes the current state.
  - `book-poc` contains `pgn_postmortem/{ingest,analysis,sources,config,markdown_site,cli}.py`, and
    its `pyproject.toml` says `requires-python = ">=3.11"`.
  - Python 3.10 does reach end of life in October 2026.
- **Markdown:** I rendered lines 17–60 of `ROADMAP.md` with GitHub's GFM renderer (`gh api markdown`,
  output kept local). The slice table renders as a table inside the list item. The nested
  `""worst games" …"` quote renders as written.
- **Checked against the slot's *decided, and not to be re-opened* list.** These are consistent:
  - English only;
  - chapters of best wins, best losses and best draws, with every game getting an article;
  - DeepSeek/BYOK left to F-2, with templates only in F-1;
  - library before pipeline;
  - no hosting: fetching and publishing stay in F-3.
  - The multi-game reading applies to the new library only. The current pipeline stays unchanged
    (question 4), so it does not contradict "one game per file" for the current pipeline.
  - The one conflict is finding 1.
- **Out of scope and dependencies:** consistent with the F-2 and F-3 rows. LLM prose is left to F-2.
  Fetching, the toml config, the outputs, Docker, the template repository and scheduling are left to
  F-3.
- **Planning is not building:**
  - The change has no code.
  - Analyzing the owner's whole archive is explicitly out of scope (`ROADMAP.md:66-67`), and the
    selection weights are tuned without it (question 9).
- **`PLAN.md`:** every column of the new rows 1–5+ is filled (`PLAN.md:38-42`).

## Findings

1. **blocking.** The scope silently re-opens a decided item.
   - **Evidence:**
     - `ROADMAP.md:46-47` says "games that already carry `[%eval]` are not re-analyzed".
     - F-1.1's done-when (`ROADMAP.md:54`) tests "parse and skip `[%eval]`".
   - **What it re-opens:** the slot's *decided, and not to be re-opened* list in `CLAUDE.md` says
     "Annotations in source PGNs are ignored and stripped …, and every game is re-analyzed."
     `docs/book-plan.md` proposes trusting existing evals, but that file calls itself "direction,
     not agreed for implementation". It also defers to the slot for settled choices.
   - **Why it matters:** a lichess export's `[%eval]` is a source annotation. Trusting it is exactly
     what the decision rules out, and the block adopts the opposite without saying so.
   - **An internal conflict too:** the block says "source comments … are stripped" (line 44), while
     `[%eval]` is itself a PGN comment. The builder cannot tell which rule wins, so the "parse and
     skip" test is not specifiable as written.
   - **Fix, either way:**
     - (a) Narrow the skip to evals the library itself wrote, meaning its own incremental cache or
       output, and re-analyze every source game. This is consistent with the decision.
     - (b) Raise it as an owner decision, with a default and reason. Only the owner can re-open a
       decided item, and the slot would be amended if the owner agrees.

2. **blocking.** F-1.3 cannot be verified in the order given.
   - **What F-1.3 needs:** its done-when (`ROADMAP.md:56`) requires "the owner reads a book built from
     the demo collection". Question 9 (`ROADMAP.md:97-98`) tunes the selection weights on "the demo
     collection in F-1.3".
   - **When the collection exists:** question 7 (`ROADMAP.md:92-94`) says the demo source "is picked
     in F-1.4 and put to the owner then". F-1.4 also "lands … the demo book".
   - **The result:** when F-1.3 is built, no demo collection exists, so its last done-when item
     cannot be run.
   - **Fix, any of these:**
     - move the choice of demo source (and getting it into the repository or a fixture) to F-1.3,
       or earlier;
     - or change F-1.3's check to a collection that exists by then.
   - **Also:** say which open question must be answered before which slice (see finding 9).

3. **non-blocking.** F-1.4's `epubcheck` check (`ROADMAP.md:57`, "a test that the EPUB validates
   (`epubcheck` in CI)") relies on a tool that is not declared anywhere.
   - **The tool:** `epubcheck` is a Java program. It is not in `requirements*.txt`, not in
     `.github/workflows/ci.yml`, and not in the gates table. Neither `epubcheck` nor `java` is on
     this machine (`which epubcheck java` finds nothing), so a builder cannot run the check locally
     as written.
   - **Gates discipline 1:** adding a CI step changes what the `tests` gate covers. That means
     updating the gates table in `CLAUDE.md`, which is a harness change under the bootstrap.
   - **Suggested fix:** state both in the done-when:
     - how epubcheck is pinned and installed, locally and in CI;
     - that the gates table row is updated.
   - **Also say** whether the test is skipped locally without the tool, as the Stockfish test is.

4. **non-blocking.** "The release is on PyPI" (`ROADMAP.md:57`) is an irreversible action that
   needs credentials.
   - **The conflict:** the builder must not read secrets (`CLAUDE.md`, *never read or echo*).
   - **Suggested fix:** say in the done-when who performs or authorizes the upload, either the owner
     or a trusted-publishing workflow the owner approves. Say how it is verified:
     - `curl -s -o /dev/null -w '%{http_code}' https://pypi.org/pypi/<name>/json` → 200;
     - then `pip install <name>` in a clean venv builds the demo book.
   - **Dependencies to note:** this item depends on question 1 (the name) and question 2 (the
     licence). A published name cannot be taken back.

5. **non-blocking.** Three owner-judgment done-when items are fine as a "play the result" step
   (`PLAN.md`, *The owner's part*; gates discipline 5). One of them can never fail as written, and
   none says where its outcome is recorded.
   - **Where they are:**
     - F-1.2: "the owner … says it reads well";
     - F-1.3: "agrees with the chapter picks, *or records what to change*";
     - F-1.4: "opens the demo EPUB in the e-reader apps".
   - **The F-1.3 clause:** "or records what to change" makes the item pass whatever the owner finds.
     Say whether recorded changes block the landing or become a new roadmap row.
   - **F-1.4:** say what happens if an e-reader fails. `docs/book-plan.md` expects a possible PNG
     fallback for Kindle's SVG support, and that fallback is not in any slice's scope.
   - **Suggested fix:** record each outcome in the slice's review completion note.

6. **non-blocking.** Question 3's default (`ROADMAP.md:81-82`, "3.11 or newer — what the spike on
   `book-poc` already needs") has two problems.
   - **The reason rests on code F-1 does not reuse.** On `book-poc`, the only 3.11-only construct is
     `import tomllib` in `pgn_postmortem/config.py`. The block leaves `config.py` to F-3 (question 5,
     out of scope), so the reused ingest and analysis code does not need 3.11. The EOL reason alone
     still holds.
   - **It conflicts with the gates table and is not reflected in F-1.1's done-when.** The gates table
     in `CLAUDE.md` says "CI on Python 3.10 and 3.12", and `ci.yml` has the matrix `["3.10", "3.12"]`.
     A package requiring ≥3.11 in this repository breaks the 3.10 job.
   - **Suggested fix:** if the default is taken, F-1.1's done-when should include moving the CI
     matrix and the gates-table row (a bootstrap change).

7. **non-blocking.** The *Also in the owner's words* line (`ROADMAP.md:22-27`) adds wording that the
   repository cannot trace to the owner.
   - **The additions:**
     - It extends the row's third quote beyond where the row ends: "… from games. But it is more
       about the idea that we need games collections as sources".
     - It adds "Yeah I need to use my old games because as of now I totally suck at chess".
   - **Where they appear:** neither appears anywhere on `main` or `book-poc`. `git log --all -S"suck
     at chess"` finds only `103a165`.
   - **What the owner confirmed:** on 2026-09-24 the owner confirmed "the quoted wording of F-1 to
     F-3" (`ROADMAP.md:8`), which covers the row quotes only.
   - **Why it is non-blocking:** the *Original request* itself is untouched, and these words may well
     be the owner's.
   - **The same applies to:** "from 2005 onwards" in the player value (`ROADMAP.md:31`), which appears
     nowhere else. `docs/book-plan.md` gives 1,791 games but no start year.
   - **Suggested fix:** have the owner confirm the added quotes, as was done for the row, or drop
     them.

8. **non-blocking.** Some scope has no done-when check. All of these can be tested cheaply.
   - **F-1.1** (`ROADMAP.md:54`) has no check that:
     - analysis is incremental (a second run analyzes nothing new) or parallel;
     - directories and globs are read, not only files;
     - the command line and API exist and the package installs (`pip install -e .`).
   - **F-1.2** (`ROADMAP.md:55`) has no check that:
     - a collection without evals builds (scope, line 47–48);
     - critical moments are chosen, and by which rule (the slot's win-%-lost grading is the natural
       one);
     - the revision mode is present.

9. **non-blocking.** The block does not say which slice each owner decision gates.
   - **The block:** "Depends on: nothing" (`ROADMAP.md:71`).
   - **The pull-request body:** "for the owner to answer before F-1.1 starts".
   - **The mismatch:** questions 7, 8 and 9 are explicitly answered later.
   - **Suggested fix:** one line per question naming the slice that needs it:
     - before F-1.1: 1 (the module name is in the package path), 2, 3, 5, 6;
     - before F-1.3: 7 (see finding 2), 9;
     - before F-1.4: 8;
     - question 4 is settled by default until after F-1.4.

10. **non-blocking.** Question 8's default (`ROADMAP.md:95-96`, "Apple Books and Kindle") silently
    drops Google Play Books. `docs/book-plan.md` (*Output*) lists all three readers for testing.
    - **Suggested fix:** keep it or say why it was dropped.

11. **non-blocking.** `PLAN.md:39-41` (iterations 2–4) give the roadmap id without the owner's
    wording.
    - **The rule:** `PLAN.md` (*The iteration table*) requires "the request with the roadmap id and
      the owner's wording".
    - **Why it is non-blocking:** row 1 carries the wording of the same request.
    - **Suggested fix:** repeat the quote, or write "F-1.2 of F-1 (wording as in row 1)".

— Claude Opus 5.5 (claude-opus-5-5), reviewer
Two blocking findings remain (1 and 2).
