# Review 027: shape F-12 (pull request #27), round 01

- **Revision covered:** `f34ed2108802de0b86b35d92b7c9bf25e65ca3cd` (branch `shape-f12`), on top of
  `origin/main` at `92a5a866972901de16c7f745badf0044329359ff` (the merge base, which is also the
  current `origin/main`).
- **Target proof:** after `git fetch origin`, `git rev-parse origin/shape-f12` gives
  `f34ed2108802de0b86b35d92b7c9bf25e65ca3cd`, which equals `headRefOid` from
  `gh pr view 27 --json headRefOid,files`. The branch has one commit (`f34ed21`).
- **Files checked:** `PLAN.md` and `ROADMAP.md`. The pull request's file list
  (`gh pr view 27 --json files`) equals
  `git diff --name-only $(git merge-base origin/main origin/shape-f12)..origin/shape-f12`. The files
  were read with `git show origin/shape-f12:<path>` and the diff with
  `git diff origin/main...origin/shape-f12`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that did
  not see the shaping.
- **Mode:** Claude Code, shaping review.
- **Read against:** `CLAUDE.md` and its slot (the gates, the generated paths, the conventions, the
  post-merge check), `PRINCIPLES.md` (*Owner decisions*, the verdict protocol), `PLAN.md`,
  `reviews/README.md`, `ROADMAP.md` on `main` (*The block*, *Statuses*, *Artistic license*,
  F-10's block), and reviews 022-01/-02 as the model. From `main`, also:
  `.github/workflows/pages.yml`, `examples/` (`daily_games`, `analyzed_games`, `docs`),
  `pgn_postmortem/cli.py`, `pgn_postmortem/site.py` (`build_site`, `default_site_key`),
  `tests/test_site.py` (`check_links`), `tests/test_quiz.py`, `README.md`, `docs/book-plan.md`
  (*Demo*), `pyproject.toml`, `requirements.txt`.
- **Checks run (2026-09-26):** `pgn-postmortem read` on scratch copies of both example sets (no
  analysis); read-only `curl` GETs of the live demo and the owner's book; read-only `gh api` GETs of
  the Pages settings and the `github-pages` environment.

## What holds

- F-12's block has every field of *The block*. The original request is verbatim and matches the row
  and PLAN.md's row 8. The two owner decisions each have a default, a reason, the alternatives not
  chosen and an owner-decision mark (ROADMAP.md, F-12's row). The other choices are listed under
  "Proposed with this shaping, confirmed by the owner's merge" (ROADMAP.md:783).
- The queue is consistent. F-12 is `accepted` with iteration 8. F-1's row adds "8 is F-12" and the
  v0.1.0 tag; `git rev-parse v0.1.0^{commit}` gives `724aa9d…`, as recorded. PLAN.md's row 8
  follows rows 5 to 7, and the next row and the note both put F-1.3 after F-12. F-1's open
  questions 4 and 7 are annotated, not re-decided, and its "Out of scope" bullet now leaves the
  Pages demo to F-12 and keeps the pipeline unchanged.
- The input claim reproduces. Both sets read as `Read 5 game(s) from 5 file(s): 0 not the
  player's, 0 duplicate(s), 0 without moves, 0 unparseable; kept 5.`, and
  `diff -r` of the two `--out` directories is empty. Every game has the seven standard headers
  and no `FEN`, and only 1892 Chigorin–Steinitz lacks `ECO`.
- The commands exist. `analyze` takes `--depth` and `--out` and needs no `--player`
  (`cli.py:120-130`, "Without --player or --alias, every game is kept"). `site` takes `--title`,
  `--site-key` and `--out` (`cli.py:132-149`). Without names `build_site` writes no quiz and no
  index link, and removes only a `quiz.html` it wrote (`site.py:1506-1526`). The rebuild removes
  only `games/*.html` pages carrying its generator line. Depth 22 matches `chessgamescollection`'s
  README ("Stockfish 19 at depth 22").
- The site-key reasoning holds. The live book's `<html>` has
  `data-site="diego-amicabile-over-the-board-games-73e534ff"`. `pgn-postmortem-demo` passes
  `check_site_key` and is not a prefix of the book's key, and F-8's "Clear history" ignores keys
  that only start with this one anyway.
- The `baseurl` reasoning holds on the live demo. The Markdown sources link relatively
  (`](games/1.md)`, `](1/blunder_2_move23b.svg)`), and the served pages link root-relatively under
  the base path: `href="/pgn-postmortem/games/1.html"`,
  `src="/pgn-postmortem/games/1/blunder_2_move23b.svg"`. The theme's edit link is
  `…/edit/main/index.md`, as noted at ROADMAP.md:774. `jekyll-github-metadata` sets `baseurl`
  only when the config leaves it unset, so an explicit one is honoured.
- The new test is feasible. `check_links` is importable (`tests/test_quiz.py:24` already does
  `from tests.test_site import … check_links`), and the marker test has a precedent
  (`tests/test_site.py:494`). Reading the committed analysis needs no Stockfish, so the test runs in
  CI's tests gate. Adding `examples/site/` doesn't disturb `test_publish.py`, which reads only
  `examples/analyzed_games` and compares only `examples/docs/`.
- Nothing contradicts the decided items. The workflow runs no Stockfish, nothing new is hosted, and
  the short analysis of public games isn't a run on the owner's data.

## Findings

1. **blocking**: done-when 3 can pass with the exact failure the `baseurl` setting exists to
   prevent.
   - **The check:** ROADMAP.md:757-759 checks that "`/markdown/` serves the Markdown index" and
     that "a Markdown game page under `/markdown/` loads its diagrams (a request for one of its SVGs
     returns 200)".
   - **Why it can pass with a wrong `baseurl`:**
     - a direct request to `/pgn-postmortem/markdown/games/1/<file>.svg` returns 200 whatever the
       `baseurl` is, because the file is there;
     - the failure the block names (ROADMAP.md:716-724, "every link of the moved pages would point
       back into the root") lives in the *served* `href`/`src` values;
     - the check doesn't cover the index's game links at all.
   - **Fix:** say the check follows the links as served:
     - the index's first game link, taken from the served `/markdown/` index, starts with the base
       path plus `/markdown/` and returns 200;
     - on that game page, one diagram's `src`, as written in the page, returns 200.

     The same holds for done-when 2's local Jekyll build, if it runs: the PR shows one rewritten
     link.

2. **non-blocking**: the workflow is first exercised after the merge, and the order of the two
   builds may not be free.
   - **The two statements:** ROADMAP.md:726 says "the order of the two builds is the implementer's
     choice", and done-when 2 accepts "the deploy decides" when Jekyll isn't available locally.
   - **Why the order may matter:**
     - `actions/jekyll-build-pages` is a Docker container action, which runs as root, so a
       directory it creates is root-owned;
     - if Jekyll runs first with `destination: _site/markdown`, it creates `_site`, and the
       library's step as the runner user may be denied writing into it.
     - This is a known runner behaviour. I did not reproduce it, since that needs a runner.
   - **A pre-merge run is possible:** the `github-pages` environment allows deployments only from
     `main` (`gh api …/environments/github-pages/deployment-branch-policies` gives
     `{"name":"main","type":"branch"}`). A `workflow_dispatch` run on the implementation branch
     would therefore build without deploying.
   - **Suggested fix:** have the library build first (or create `_site` before Jekyll), and add to
     done-when 2 a `workflow_dispatch` run of the build job on the branch. The PR would record its
     URL and the artifact's contents (the deploy job is expected to be refused).

3. **non-blocking**: the planned `CLAUDE.md` update misses two places.
   - **The post-merge check's defect clause:** `CLAUDE.md:122-123` counts only "the workflow or the
     content of `examples/docs/`" as a failure caused by the repository. After F-12 the run also
     depends on `pgn_postmortem/**`, the package manifests and `examples/site/analyzed/`, which
     are now triggers (ROADMAP.md:727). The block (ROADMAP.md:732) only says the paragraph
     "describes the new build and its triggers".
   - **The paths to normally ignore:** `examples/site/analyzed/**` is generated. It belongs next to
     `examples/analyzed_games/**` there (`CLAUDE.md:94`), as well as in the generated-paths list
     the block already names.
   - **Fix:** list both in the `CLAUDE.md` bullet of the scope.

4. **non-blocking**: the old deep links break, and this isn't recorded.
   - **What breaks:** after the move, `https://diegoami.github.io/pgn-postmortem/games/1.html` (and
     its SVGs) stop resolving, since the root's `games/` holds only `<date>-<id>.html`. There is no
     redirect.
   - **What the record says:** open question 4's default is "the live demo keeps working
     meanwhile", which now holds only at the new address.
   - **Fix:** add a line to "Out of scope" (no redirects from the old URLs) or to the row's decision
     text, so the cost is visible to the owner at merge. Nothing in the repository links the old
     deep URLs; only `README.md:14` links the root.

5. **non-blocking**: two wording points about who decided what.
   - **The order:** PLAN.md's note says F-12 "comes first" (before F-1.3), but that order is neither
     marked as an owner decision nor listed as proposed (ROADMAP.md:783 lists the other choices).
     Mark it as one or the other.
   - **The tense:** ROADMAP.md:108 says "the owner moved the Markdown demo to `/markdown/`", but
     nothing has moved yet. "decided to move" is accurate until the implementation lands.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
Blocking findings remain (1).
