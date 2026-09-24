# Review 008 — F-1.2, every game as an article — implementation, round 02

- **Revision covered:** `91d6795097a419a4713f26594c186d743ef58616` (PR #8, branch
  `iteration-2-game-articles`, base `main`; merge base `38c27619f52f1ec36b636c8678bd4697e8303d77`).
  Round 01 covered `f41380421f54dc53db8f6668f566bdfedf3efac2`. Four commits since:
  - `c124b59`: the round-01 review, committed;
  - `0602071`: the fixes for findings 1, 3 and 4, with their tests;
  - `e320079`: finding 5 recorded in `ROADMAP.md`;
  - `91d6795`: CLAUDE.md and README updates.
- **Target proof:**
  - `git fetch origin`, then a detached checkout of `origin/iteration-2-game-articles`.
  - `git rev-parse HEAD` = `91d6795097a419a4713f26594c186d743ef58616` =
    `gh pr view 8 --json headRefOid`.
  - `git remote get-url origin` = `git@github.com:diegoami/pgn-postmortem.git`.
  - `git show HEAD:reviews/008-f1-2-game-articles-impl-01.md | cmp -` against my scratchpad
    round-01 file: byte-identical.
- **File list** (27 files). `gh pr view 8 --json files` equals
  `git diff --name-only 38c2761..91d6795`. It is round 01's 24 files plus these three:
  - `ROADMAP.md`;
  - `reviews/008-f1-2-game-articles-impl-01.md`;
  - `tests/fixtures/site/odd.pgn`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a Claude Code subagent. This round continues
  the round-01 reviewer session, as `PRINCIPLES.md` allows for a re-review. I have not seen the
  implementation session, and I re-read the current revision.
- **Mode:** Claude Code.

## What I ran

- **Gates** (my venv, `pip install -e .` re-run, Stockfish 16 on PATH):
  - `ruff check .`: All checks passed!
  - `pytest -q`: 75 passed, 0 skipped. That is 72 before, plus the escaping test and the
    odd-date test, with the stale-page test split in two.
  - CI run 36021135159 (`pull_request`, headSha `91d6795…`): test (3.11) pass, test (3.13) pass.
- **Golden and fixture delta.** `git diff f413804..HEAD -- tests/golden tests/fixtures/site/analyzed
  tests/fixtures/site/games.pgn` has exactly 7 changed lines. Every one is the added
  `<meta name="generator" content="pgn-postmortem">`, one per page: the 6 articles and the index.
  - `style.css` is unchanged.
  - The analyzed fixture and `games.pgn` are unchanged.
  - The golden test passes, so the regenerated files match the documented command's output.

  This is what the PR says.
- **Breaking each fix.** Each break was restored with `git checkout --`, and `git status` was
  clean every time.
  1. `esc()` returns `str(text)`: **red**. `test_names_with_markup_characters_are_escaped` fails
     (and so does the odd-date test, which parses the same pages). In round 01 this break
     stayed green.
  2. `is_number` back to `str.isdigit()` (`collection.py:202-205`): **red**, with
     `ValueError: … '²019'` in the escaping test and the stale-page test.
  3. Only `file_stem`'s year check back to `y.isdigit()`, with the site's check intact: **red**,
     in `test_a_malformed_date_still_gets_an_article_filed_as_undated` (the `undated-<id>`
     name).
  4. The cleanup without `is_generated` (`site.py:915-916`): **red**, in
     `test_a_file_the_builder_did_not_write_is_never_removed`.
  5. The cleanup back to round 01's name regex: **red**, in both stale-page tests.
  6. `GENERATOR` removed from `page()` (`site.py:432`): **red**, in the golden test and
     `test_a_stale_page_the_builder_wrote_is_removed_whatever_its_name`.
- **Finding 3's effect on F-1.1 file names**, reproduced with the CLI on `odd.pgn`:
  - `analyze` writes `undated-8dce5aad57.pgn` for `[Date "²019.01.01"]`, and the file keeps
    `[Date "²019.01.01"]` and `PostmortemId "8dce5aad57"`.
  - A second `analyze` finds "0 game(s); 3 already there". A `read --out` into the same folder
    finds "3 already analyzed there, left as they are".
  - For a folder holding a stripped copy under the pre-fix name `²019-01-01-8dce5aad57.pgn`,
    `analyze` writes `undated-8dce5aad57.pgn` beside it. `site` then builds 3 articles, all
    3 analyzed, because the analyzed copy wins the duplicate.
- **The generator marker.** `is_generated` (`site.py:867-872`) reads the first 1024 bytes and
  looks for `"\n" + GENERATOR + "\n"`. `page()` puts that line fifth in the head, about 150
  bytes in, so every page this builder writes carries it. A foreign file named like an article
  survives, as the new test shows.

## Round-01 findings

1. **Escaping is untested: closed.**
   - `tests/fixtures/site/odd.pgn` puts `<`, `>`, `&`, `"` and `'` in White, Black, Event,
     Site, Round, WhiteElo, Opening and Termination, and the test adds a hostile `--title`.
   - The test (`tests/test_site.py`, `test_names_with_markup_characters_are_escaped`) checks
     every page of that site:
     - strict well-formedness;
     - a whitelist of tag and attribute names, so no header text turned into markup;
     - the absence of the raw strings;
     - an exact read-back of the infobox values and the title.
   - It went red with escaping removed (break 1).
2. **`keep_analysis` trusts the marker: left as is by the owner.** It is recorded under *Left
   out* in the PR body, with the exact boundary. Not re-opened here.
3. **An odd `Date` aborts the build: closed.** `is_number` (ASCII digits only) replaces
   `isdigit` in `file_stem` and `date_parts`, so `²019.01.01` becomes an undated article and no
   longer crashes the build. The test goes red on either half of the change (breaks 2 and 3).
   - **The F-1.1 naming change is correct and safe.**
     - `game_id` still hashes the `Date` as written (`collection.py:186-198`, unchanged), so the
       owner's identity rule and every id stay the same.
     - The incremental skip in `analyze_games` and in `Collection.write` goes by `PostmortemId`,
       not by file name.
     - The only change is the name given to a year that is not ASCII digits: it follows the
       existing "unknown year → `undated-<id>`" convention.
     - An old stripped copy under a `²019-…` name stays beside the new analyzed file (see
       finding 8). That is the same shape as the pre-padding names F-1.1 already tolerates.
4. **The stale cleanup and the name grammar disagree: closed.** Deletion now goes by the
   builder's own marker, not by name.
   - A `2019-123-05-<id>.html` page is removed once its game leaves the collection.
   - A foreign `2000-01-01-0123456789.html` and a `notes.html` survive.
   - Breaks 4 to 6 each go red.
5. **The piece-set licence is unrecorded: closed as recorded.** `ROADMAP.md:88-90` adds the
   pieces' licence to open question 2, before F-1.4, and says it is unverified. The owner asked
   for this. The owner decision itself is unchanged.
6. **The player shows under an alias: left as is by the owner** (*Left out*).

## New findings

7. **non-blocking — A directory named `*.html` in `games/` crashes the rebuild.**
   - The cleanup globs `games/*.html` (`site.py:915`) and calls `is_generated`, which does
     `path.open("rb")` (`site.py:870`). A directory matching the glob raises
     `IsADirectoryError`.
   - Reproduced: after `mkdir <out>/games/archive.html`, `pgn-postmortem site` exits 1 with that
     traceback. The pages are already written by then, but the command reports failure.
   - Before this round, only a directory named like an article could trigger this. Now any
     `*.html` directory does.
   - Suggested fix: skip anything that is not a regular file (`path.is_file() and
     is_generated(path)`).
8. **non-blocking, informational — The leftover stripped copy under an old name.**
   - A game with a non-ASCII-digit year that an earlier build wrote stripped as
     `²019-01-01-<id>.pgn` keeps that file after the new `analyze` writes
     `undated-<id>.pgn` (reproduced above).
   - Nothing is analyzed twice. Reading prefers the analyzed copy, and duplicates are removed
     by id, so nothing the user sees changes.
   - The window is tiny: such a date, written by an unreleased F-1.1 build. This needs no fix.
     A sentence in the PR body would make it visible.

## Verdict

Findings 1, 3 and 4 are fixed, each with a test that goes red when its fix is broken. Finding 5
is recorded where the owner asked. Findings 2 and 6 are left out by the owner's decision and
recorded in the PR body. The golden files differ from round 01 only by the generator line. The
F-1.1 naming change keeps ids and incremental analysis intact. The gates and CI are green on
`91d6795`. Merge still waits on the owner's phone and `file://` verdict, which the F-1.2 row
requires.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
