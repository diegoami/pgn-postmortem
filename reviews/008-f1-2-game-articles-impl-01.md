# Review 008 — F-1.2, every game as an article — implementation, round 01

- **Revision covered:** `f41380421f54dc53db8f6668f566bdfedf3efac2` (PR #8, branch
  `iteration-2-game-articles`, base `main`; merge base `38c27619f52f1ec36b636c8678bd4697e8303d77`).
- **Target proof:** `git fetch origin`, detached checkout of `origin/iteration-2-game-articles`;
  `git rev-parse HEAD` = `f41380421f54dc53db8f6668f566bdfedf3efac2` = `gh pr view 8 --json headRefOid`.
  `git remote get-url origin` = `git@github.com:diegoami/pgn-postmortem.git`.
- **File list** (24 files). `gh pr view 8 --json files` equals
  `git diff --name-only 38c2761..f413804`:
  `CLAUDE.md`, `PLAN.md`, `README.md`, `pgn_postmortem/__init__.py`, `pgn_postmortem/cli.py`,
  `pgn_postmortem/collection.py`, `pgn_postmortem/site.py`,
  `tests/fixtures/site/analyzed/{2019-03-14-bf58e2afa0,2019-04-02-5d1415e1ac,2020-06-01-9705c13f05,2021-09-10-a9c90416b2,2021-12-24-9137b96576,undated-5ce208cdcb}.pgn`,
  `tests/fixtures/site/games.pgn`, `tests/golden/site/assets/style.css`,
  `tests/golden/site/games/` (the same six stems, `.html`), `tests/golden/site/index.html`,
  `tests/test_cli.py`, `tests/test_site.py`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. It did
  not see the implementation session.
- **Mode:** Claude Code (PLAN.md iteration 2 row). No design record; the contract is the F-1.2
  row of F-1's block in `ROADMAP.md`.

## What I ran

- **Gates**, in a fresh venv in my worktree (`requirements-dev.txt` plus `pip install -e .`,
  with Stockfish 16 at `/usr/games/stockfish` on PATH):
  - `ruff check .`: All checks passed!
  - `pytest -q`: 72 passed, 0 skipped.
  - CI (`gh pr checks 8`): test (3.11) pass, test (3.13) pass, GitGuardian pass.
- **The fixture is generated, not hand-edited.**
  `pgn_postmortem analyze tests/fixtures/site/games.pgn --out <tmp> --depth 12 --workers 1`
  with Stockfish 16 gives output that `diff -r` finds identical to
  `tests/fixtures/site/analyzed/`. The golden test itself rebuilds `tests/golden/site/` with the
  documented `REGENERATE` command through `cli.main`.
- **My own breaks.** For each one I edited the file, ran the tests, then restored it with
  `git checkout --` and checked that `git status` was clean.
  1. Critical threshold `loss >= thresholds.mistake` changed to `thresholds.blunder`
     (`site.py:143`): **red**. The golden test fails on `2021-12-24-9137b96576.html`, and
     `test_the_critical_moments_of_the_fixture_are_the_expected_ones` fails too.
  2. `<details class="answer">` changed to `<details class="answer" open>` (`site.py:580`):
     **red**. The golden test fails, and so does
     `test_every_critical_moment_has_its_question_and_a_hidden_answer` ("the answer is not
     hidden").
  3. Index links written without `games/` (`site.py:746`): **red**. The golden test fails, and
     the one-article/no-broken-links test fails in all three parametrizations.
  4. The stale-article cleanup no longer checks `ARTICLE_NAME` (`site.py:896`): **red**, in
     `test_an_earlier_build_leaves_no_stale_article` (`notes.html` deleted).
  5. `keep_analysis` trusts every game, not only marker-bearing ones (`collection.py:312`):
     **red**, in `test_keep_analysis_still_strips_a_source_that_the_library_did_not_analyze`
     only. The site's own `is_analyzed` check is a second guard.
  6. `esc()` changed to return `str(text)`, so no escaping at all (`site.py:172`): **green**,
     with all 19 site and CLI tests passing. See finding 1.
- **Pages rendered and inspected.** I read the golden HTML directly and took screenshots with
  headless Chromium (`file://`, 390 px and 1100 px):
  - The infobox is full width on a phone and floats right at desktop width.
  - Diagrams at a critical moment are flipped for Black, with correct squares and highlights.
  - "Show the answer" is collapsed, and no JavaScript is needed.
  - Links are relative. There is no `<script>`. The only `http` strings are the SVG `xmlns`
    inside the stylesheet's data URIs, which load nothing.
- **Escaping.** I built a site from a hostile fixture: `<script>`, `&`, `"` and `'` in Event,
  Site, Round, White, Black, WhiteElo, Opening and Termination, plus `--title '<T> & "q"'`.
  Everything came out escaped. The pages parse with the test's strict tree builder, and
  `check_links` passes.

## Contract (the F-1.2 row)

- **The gates pass:** yes (above).
- **Golden byte-for-byte test, with a documented regeneration command:** yes.
  `test_the_fixture_site_renders_to_the_golden_pages_byte_for_byte` compares the file set and
  every file's bytes. The command is in `REGENERATE`, the CLAUDE.md slot and the README.
- **One article per game and no broken internal links:** yes.
  - The set of `games/` files equals one stem per collected game.
  - The index lists each game exactly once.
  - Every `href`/`src` is relative, resolves to a file inside the site, and every fragment
    exists as an id.
  - This runs on the analyzed fixture, on the same games unanalyzed, and on the reading fixture.
- **Every critical moment has its question and hidden answer:** yes. The moments are listed by
  hand (`EXPECTED_MOMENTS`), and the ids must match exactly, so an extra moment or a missing
  one fails. The test also checks:
  - a diagram and "What would you play?" in the caption;
  - a closed `<details>` whose first element is the summary;
  - an answer with "Best was" and the move played;
  - that the best move appears nowhere outside the `<details>`.
- **A no-analysis fixture builds one article per game with no critical moments:** yes, on
  `games.pgn` and on `tests/fixtures/collection/`, which carries a source `[%eval]`.
- **Owner's phone and `file://` check:** correctly left pending in the PR body. It precedes the
  merge and is not mine to give.
- **Nothing of F-1.3 or F-1.4 slipped in:** no career article, no selection or chapters, no
  demo collection, no EPUB, no release workflow.
- **`scripts/` and `examples/` are unchanged:** the diff has 0 lines under either.
- **Decided items:**
  - The site is in English.
  - Every game gets an article.
  - The prose comes only from templates.
  - Grading uses win % lost with `analysis.classify` and the 10/20/30 thresholds.
  - No source annotation reaches a page for a game without the marker.

  Nothing decided is contradicted, with the caveat in finding 2.

## Findings

1. **non-blocking — Escaping is correct but no test asserts it.**
   - No fixture contains `<`, `>` or `&`: `grep -c "[<>&]"` gives 0 for
     `tests/fixtures/site/games.pgn` and `tests/fixtures/collection/club/2019.pgn`.
   - Removing all escaping (`site.py:170-172`, `esc` returning `str(text)`) leaves every site
     and CLI test green (break 6 above).
   - Real headers do carry these characters: names such as "O'Kelly", and events with `&` or
     `<`.
   - Suggested fix: add one fixture game whose Event and player names carry `<`, `&`, `"` and
     `'`, and let the golden test and the strict `parse()` cover it. Then a regression goes red.

2. **non-blocking — `keep_analysis` trusts the marker, not provenance, and the docs overstate
   it.**
   - The rule is right as far as it goes. Only a game carrying `PostmortemAnalysis` keeps its
     analysis (`collection.py:312`), and the site grades only such games (`site.py:107-109`,
     `128`, `133`).
   - A crafted source PGN with that header bypasses the rule. I reproduced it with a
     "Fritz 6" game that has a forged `[PostmortemAnalysis "Fritz 6, irgendwas"]`, source
     `[%eval]`s and a source variation `( 2. d4 )`. `site` produced:
     - one critical moment from the source evals;
     - a note "A blunder: White's winning chances fall from 52% to 4%";
     - "Best was 2. d4", taken from the source's own variation (`engine_line`, `site.py:155-164`);
     - "Analysis: Fritz 6, irgendwas" in the infobox.

     Its text comments did not reach the page.
   - Under the decided rule this does not matter in practice. The rule targets real-world
     annotations (chess.com evals, Fritz/Hiarcs notes), which never carry the library's own
     header. F-1.1 already trusts the same marker for incrementality (`analyzed_ids`). So I do
     not block on it.
   - But the claims are literally false for a marker-bearing source:
     - "a source's own `[%eval]` is never trusted" (`collection.py:17`, repeated in the PR
       body);
     - the README's "whose only evaluations came from their source … without notes or
       questions".
   - `keep_analyzed` (`collection.py:254`) also keeps everything else in such a game: the
     `Annotator` header, text comments, NAGs and every variation.
   - Suggested fix: state the boundary exactly, i.e. "a game's evaluations are trusted if and
     only if it carries the `PostmortemAnalysis` header the analysis step writes; a file that
     forges it is taken at its word". Optionally, pin that no text comment of a marker game
     reaches a page.
   - If the owner wants trust tied to provenance instead (for example a separate
     `--analysis DIR`), that is an owner decision, not a builder fix.

3. **non-blocking — One odd `Date` aborts the whole build.**
   - `date_parts` tests `y.isdigit()` and then calls `int(y)` (`site.py:207-208`).
     `str.isdigit()` accepts characters such as `²` that `int()` rejects.
   - A single game with `[Date "²019.01.01"]` makes `pgn-postmortem site` exit with
     `ValueError: invalid literal for int() with base 10: '²019'` (reproduced). No article is
     written for any game.
   - Unlikely in real PGN, but "every game gets an article" argues for robustness.
   - Suggested fix: use `isdecimal()` together with an ASCII check, or `re.fullmatch("[0-9]+")`.
     The same applies to `format_date`'s callers.

4. **non-blocking — The stale-article cleanup and the file-name grammar disagree.**
   - `ARTICLE_NAME` (`site.py:74`) requires `\d{4}-\d{2}-\d{2}`. `file_stem`
     (`collection.py:201-210`) can produce a longer month or day: `2019.123.05` gives
     `2019-123-05-<id>.html`. After such a game leaves the collection, its page is never
     removed. I reproduced this: two files in `games/` for one game, one of them orphaned.
   - Conversely, the cleanup deletes by name alone. A file the user put at
     `<out>/games/2019-01-01-0123456789.html` is deleted although the builder never wrote it.
     This is documented ("only files named like articles") and low-risk.
   - Suggested fix: mark each generated page (for example
     `<meta name="generator" content="pgn-postmortem">`) and delete only files that carry the
     mark. That closes both holes.

5. **non-blocking — The piece set is credited, but its licence is not recorded.**
   - The credit appears in the footer (`site.py:430-431`), the README (`README.md:237`) and the
     CSS comment. Every generated stylesheet redistributes the artwork as data URIs.
   - The installed python-chess 1.11.2 carries no attribution or licence notice for the pieces:
     a grep of `chess/` and its `dist-info` for Burnett/Wikimedia finds nothing. So "Colin M.L.
     Burnett's, as python-chess ships it" rests on outside knowledge. It is plausible, but I
     did not verify it and did no network lookup.
   - Suggested fix: record the pieces' licence and its source in the README. Settle it with
     open question 2 (the licence) before F-1.4, since the site output ships the artwork.

6. **non-blocking — The player appears under whatever alias the PGN used.**
   - The site is "Games of Ada Example", yet the index and titles show "AdaEx vs. Gino
     Newcomer, 2021" and "Fabio Quick vs. AdaEx" beside "Ada Example vs. Bruno Rival"
     (`tests/golden/site/index.html`). `display_name` only reorders "Last, First"
     (`site.py:185-195`).
   - This is inside artistic license. For a book about one player, showing the `--player` name
     wherever an alias matched would read better. The owner's phone check may decide.
   - Minor, same category: at 1100 px the moment caption wraps as "What would / you play?".

## Verdict

The contract items are met, and each has a test that went red when I broke what it guards: the
threshold, `<details>`, links, the cleanup guard and the marker check. The exception is
escaping: the code is correct, but no test covers it (finding 1). The fixture is reproducibly
generated. No out-of-scope work slipped in, and nothing decided is contradicted. Merge still
waits on the owner's phone and `file://` verdict, which the F-1.2 row requires.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
