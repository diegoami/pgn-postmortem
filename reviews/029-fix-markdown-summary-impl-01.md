# Review 029, defect fix "The HTML is broken" (Markdown summary), implementation round 01

- **Revision covered:** `fe8bc03dc137dcc9abd6e5e2b8f9104d69023940`, the head of pull request #29
  (branch `fix-markdown-summary`). The checked-out `HEAD` (detached at
  `origin/fix-markdown-summary`) equals the PR's `headRefOid`.
- **Base:** `f92463a962173e9ec29059d0062ce2e5a38bc157` (`git merge-base origin/main HEAD`, equal to
  `origin/main`).
- **File list and how it was obtained:** `gh pr view 29 --json files,headRefOid` and
  `git diff --name-only <merge-base>..HEAD` give the same 8 files:
  - `CLAUDE.md`;
  - `examples/docs/games/{1,2,3,4,5}.md`;
  - `scripts/publish_games.py`;
  - `tests/test_publish.py`.
- **Commits:** `5c456ba` (the fix, the test, the regenerated `examples/docs/`) and `fe8bc03` (the
  gates table's "covers" cell).
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that did
  not see the implementation.
- **Mode:** Claude Code. The change is a defect fix under the defect path of `PRINCIPLES.md`
  (Claude mode: no design stage; reviewed like any change).
- **Contract:** the defect as reported by the owner on 2026-09-26 ("The HTML is broken in
  https://diegoami.github.io/pgn-postmortem/markdown/games/1.html, you can see in the web page html
  tags like </summary> and </details>"), the fix path the owner chose ("Fix the generator"), the
  defect path in `PRINCIPLES.md` (the fix lands the assertion that would have caught the defect),
  the Markdown pipeline being otherwise frozen (ROADMAP F-1 open question 4), and `CLAUDE.md`'s
  slot (the gates; `examples/docs/**` generated, never hand-edited, with its documented command).

## What was checked

- **Gates, in a fresh venv in the reviewer's worktree** (`pip install -r requirements-dev.txt &&
  pip install -e .`, Stockfish on PATH, Node v24):
  - `ruff check .`: all checks passed;
  - `pytest -q`: 221 passed, none skipped;
  - `node --test 'tests/js/*.test.mjs'`: 32 passed.
- **CI** on the head: `test (3.11)` and `test (3.13)` pass (run 36263591622).
- **The fix.** `scripts/publish_games.py:435` adds `summary_line(text)`, returning
  `<summary markdown="span">{text}</summary>`; the two places that wrote a `<summary>` use it
  (`:535`, the inaccuracy blocks; `:546`, "Show movetext"). Nothing else in `scripts/` changed.
  A grep of `scripts/*.py` for HTML tags finds only these two summaries and their `<details>` /
  `</details>` lines (`:534`, `:538`, `:545`, `:551`), each alone on its line, which kramdown with
  `parse_block_html` handles as intended; `index.md` has no raw HTML. The fix is limited to the
  defect.
- **The origin claim.** `parse_block_html: true` was introduced by `4e2269b` (the first Pages
  workflow), and `examples/docs/games/1.md` at `4e2269b` already had the one-line summaries, so the
  defect dates from the first publish, as the PR says, not from F-12.
- **`examples/docs/` regenerated as claimed.** Running the documented command
  (`scripts/publish_games.py --player '*' --data-dir examples --source analyzed_games`) on the head
  leaves `git status` clean. Against the base, `examples/` differs in 8 lines of the five game
  pages (3, 1, 1, 1, 2), every one a `<summary>` line gaining ` markdown="span"`; no SVG, PGN or
  `index.md` changed.
- **The assertion fails on `main`, for the right reason.** With the base's
  `scripts/publish_games.py` and `examples/docs/` swapped in and the tests unchanged,
  `tests/test_publish.py` gives 3 failed, 1 passed: `test_single_player_filter` and
  `test_every_summary_in_the_committed_examples_is_a_span` on "`games/1.md:35: '<summary>Show
  movetext</summary>' is not a one-line <summary markdown="span">`" and `:31` (the inaccuracy
  summary), and `test_summary_line_is_one_span_element` on the missing `summary_line`. This is
  exactly the PR's quoted output. Files restored; `git status` clean.
- **Mutations.** I applied nine mutations to `scripts/publish_games.py`. Each was run twice: with
  the committed docs as they are, and after regenerating `examples/docs/` with the documented
  command, which is the case where the golden test no longer helps. Only `tests/test_publish.py`
  was run. The generator and the docs were restored after each mutation, and `git status` was clean
  at the end. With the docs regenerated, the new assertion catches all nine:
  1. attribute dropped at the inaccuracy site: `test_every_summary_in_the_committed_examples_is_a_span`
     (see finding 1);
  2. attribute dropped at the movetext site: the single-player and committed-examples tests;
  3. the summary split over two lines (text on the next line): all three new tests;
  4. the closing tag on its own line: all three new tests;
  5. `markdown="block"`: all three new tests;
  6. `markdown="1"`: all three new tests;
  7. an uppercase `<SUMMARY>` written directly, bypassing `summary_line`: the single-player and
     committed-examples tests (the check lowercases the line);
  8. trailing text after `</summary>`: all three new tests;
  9. no closing tag: all three new tests.

  Without regeneration, the golden test also fails in each case.
- **The test itself** (`tests/test_publish.py:26-44`, `:98`, `:101-113`).
  - The check reads every line of `docs/**/*.md` containing `<summary` (case-insensitive). Each
    one must fully match `<summary markdown="span">(.*)</summary>`, with no further "summary"
    inside, so a second element on the line is rejected.
  - The committed-examples test also requires a `<summary` on every game page. Combined with the
    check, every page has at least one span summary, so no page can be skipped silently.
  - The check is stricter than kramdown needs: single quotes or extra attributes would fail. It
    also gives a false positive for a player whose name contains "summary". Neither is a concern
    for the committed examples.
- **The kramdown render, with the Pages action's own image** (`ghcr.io/actions/jekyll-build-pages:v1.0.13`,
  kramdown 2.4.0). Each page of the base's and the head's `examples/docs/` was rendered with
  `Kramdown::Document.new(text, input: "GFM", parse_block_html: true).to_html`, and the output
  was checked with Python's `html.parser`:

  | | escaped `&lt;/summary&gt;` + `&lt;/details&gt;` | `<details>` | nested `<details>` | block elements inside a `<summary>` |
  |---|---|---|---|---|
  | base, games 1–5 | 6, 2, 2, 2, 4 | 3, 1, 1, 1, 2 | 2, 0, 0, 0, 1 | 28, 3, 3, 3, 11 |
  | head, games 1–5 | 0 | 3, 1, 1, 1, 2 | 0 | 0 |
  | `index`, both | 0 | 0 | 0 | 0 |

  - On the head, every `<summary>` is a direct child of its `<details>`, and no tag is left open.
  - The `markdown` attribute is not emitted in the HTML.
  - `<h2 id="full-pgn">` comes after the inaccuracy blocks' `</details>`, not inside them.
  - The summaries read "Move 22… h4 by Wilhelm Steinitz (Inaccuracy)", "Move 29. Ne6+ by Mikhail
    Chigorin (Inaccuracy)", "Move 32… Bc6 by Viswanathan Anand (Inaccuracy)" and "Show movetext".

  This reproduces the PR's table. I did not reproduce the PR's full `github-pages build`; the
  kramdown call is the part that decides the output.
- **GitHub's own rendering.** `gh api markdown -f mode=gfm` on games 1, 3 and 5 gives
  byte-identical HTML for the base and the head. Together these pages cover both kinds of summary.
  GitHub drops the attribute (`<summary>Show movetext</summary>`).
- **`CLAUDE.md`.** A word diff of the tests gate's "covers" cell shows one insertion and no
  removal. It is placed after "the single-player filter;" and names the assertion, where it runs
  (in `examples/docs/`, in the single-player output, and from `summary_line`), its file and the
  defect. It also says the gates run no kramdown. It is accurate for the test as written.
- **Commits.** Both have an imperative summary line ("Render each Markdown page's <summary> as a
  span for kramdown", "Name the <summary> assertion in the tests gate's covers cell"), a body
  saying why, and the `Co-Authored-By: Claude Opus 5.5` line.
- **The PR body.** Its counts are accurate: 221 and 32 tests passing; 8 lines changed; the failure
  output on `main`; the escape and `<details>` counts; the grep of `scripts/`. It also says why no
  kramdown runs in the gates, and it lists what is left out (the workflow, markup in player names,
  a ROADMAP row).

## Findings

1. **non-blocking**: the single-player output covers only one of the two summary sites.
   `tests/test_publish.py:98` runs the assertion on the single-player output, but that output has
   no inaccuracy block. Mutation 1 above (attribute dropped at `scripts/publish_games.py:535`) was
   caught only by `test_every_summary_in_the_committed_examples_is_a_span`, through games 1 and 5.
   Today the committed examples have inaccuracies, and the golden test ties them to the generator,
   so the defect stays caught. If the examples ever lost all their inaccuracies, that site would
   be unchecked, unless it keeps going through `summary_line`. A cheap guard would assert that the
   committed examples contain at least one inaccuracy summary. The owner decides whether it is
   worth it.
2. **non-blocking**: the committed assertion is structural, not a render. It checks the form
   kramdown needs, not kramdown's output; the gates run no Ruby. The PR says so and gives its
   reasons. The manual render with the Pages image (reproduced above) is the evidence that the
   form is right. The PR's last done-when item is still open: the live page after the Pages
   redeploy (`examples/docs/**` is a trigger of `.github/workflows/pages.yml`). That is the only
   check on the page where the owner saw the defect, and it is recorded after merge.
3. **non-blocking**: the summary text is now inline Markdown on Pages. With `markdown="span"`,
   kramdown reads the summary's text as Markdown. A `*` or `_` in a player's name would become
   emphasis, and `...` renders as `…` (it already did on the base, inside the escaped paragraph).
   The PR's "Left out" states this, and no example is affected. No action needed.
4. **non-blocking**: where the defect is recorded. As in #24 (review 024, finding 4), the defect
   has no `ROADMAP.md` or `PLAN.md` row. It is recorded in the commit message, the test module's
   docstring (`tests/test_publish.py:7-13`), the `CLAUDE.md` covers cell, the PR and, once
   committed, this review file. That satisfies the rule as written. The owner decides whether a
   roadmap line is wanted.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
