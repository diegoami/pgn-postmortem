# Review 027: shape F-12 (pull request #27), round 02

- **Revision covered:** `81d9bae85223bcd8cb60aca77ef3e68815346c31` (branch `shape-f12`), on top of
  `origin/main` at `92a5a866972901de16c7f745badf0044329359ff` (the merge base).
- **Target proof:** after `git fetch origin`, `git rev-parse origin/shape-f12` gives
  `81d9bae85223bcd8cb60aca77ef3e68815346c31`, which equals `headRefOid` from
  `gh pr view 27 --json headRefOid,files`. The branch has three commits: `f34ed21` (the shaping),
  `a07fd0e` (round 01's record) and `81d9bae` (the answer to round 01).
- **Files checked:** `PLAN.md`, `ROADMAP.md` and `reviews/027-shape-f12-impl-01.md`. The pull
  request's file list (`gh pr view 27 --json files`) equals
  `git diff --name-only $(git merge-base origin/main origin/shape-f12)..origin/shape-f12`. The files
  were read with `git show origin/shape-f12:<path>`. The whole change was read with
  `git diff origin/main...origin/shape-f12`. The changes since round 01 were read with
  `git diff a07fd0e..origin/shape-f12`, which touches only `PLAN.md` and `ROADMAP.md`. Round 01
  covered `f34ed21`; `a07fd0e` only adds its record.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that did
  not see the shaping or round 01's session.
- **Mode:** Claude Code, shaping review.
- **Read against:** `CLAUDE.md` and its slot (the gates, the generated paths, the conventions, the
  post-merge check), `PRINCIPLES.md`, `PLAN.md`, `reviews/README.md`, `ROADMAP.md` (*The block*,
  *Statuses*, *Artistic license*, F-10's block) and review 022-02 as the model. From `main`, also:
  `.github/workflows/pages.yml`, `examples/`, `pgn_postmortem/cli.py`, `README.md`,
  `docs/book-plan.md` (*Demo*), `requirements.txt` and `pyproject.toml`.
- **Checks run (2026-09-26), all read-only:**
  - `pgn-postmortem site` on a scratch copy of `examples/daily_games/`, with the block's title and
    site key (no analysis);
  - `curl` GETs of the live demo;
  - `gh api` GETs of the Pages settings and the `github-pages` environment.

## The record of round 01

`reviews/027-shape-f12-impl-01.md` hasn't changed since `a07fd0e`, the commit that added it:
`git diff --name-only a07fd0e origin/shape-f12 -- reviews/` is empty.

## Round-01 findings

1. **Blocking, now resolved.** Done-when 3 (`ROADMAP.md:767-776`) now follows the links as the
   served pages write them:
   - "its first article link, followed as served, returns 200" (the root);
   - the `/markdown/` index's first game link "starts with the base path plus `/markdown/` and
     returns 200";
   - "one diagram's `src`, as written in the served page, returns 200".

   A wrong `baseurl` now fails the check. On the live demo the index's game links are
   root-relative (`href="/pgn-postmortem/games/1.html"`), so the prefix check would catch links
   that point back into the root. Done-when 2 (`ROADMAP.md:759-762`) also shows a rewritten link
   when Jekyll runs locally. See finding 2 for a gap that is left.
2. **Resolved.** The block now builds the library's site first, or creates the output directory
   before Jekyll runs, and gives the reason (`ROADMAP.md:727-730`). Done-when 2 adds a
   `workflow_dispatch` run on the implementation branch (`ROADMAP.md:763-766`). I checked that this
   run can't deploy:
   - `gh api …/environments/github-pages` gives `"custom_branch_policies":true`, with one
     `branch_policy` rule;
   - `…/deployment-branch-policies` lists only `{"name":"main","type":"branch"}`;
   - `main`'s `pages.yml` already has `workflow_dispatch` (`pages.yml:10`), so the branch's version
     can be dispatched.

   See finding 1 for two side effects of that run.
3. **Resolved.** The `CLAUDE.md` bullet (`ROADMAP.md:735-743`) now covers both places:
   - it quotes the defect clause correctly (`CLAUDE.md:122-123`, "the workflow or the content of
     `examples/docs/`") and widens it to `pgn_postmortem/**`, the manifests and
     `examples/site/analyzed/`;
   - it adds `examples/site/analyzed/**` to the paths to normally ignore, next to
     `examples/analyzed_games/**` (`CLAUDE.md:97`).
4. **Resolved.** "Out of scope" now lists the missing redirects (`ROADMAP.md:791-795`), and F-1's
   open question 4 says the old deep links aren't redirected (`ROADMAP.md:110-111`). I checked the
   claims:
   - `curl` of `…/pgn-postmortem/games/1.html` gives 200 today;
   - `git grep` finds no link to the demo's deep URLs outside the review records and `ROADMAP.md`
     (`README.md:14` links only the root);
   - the scratch build writes only `games/<date>-<id>.html` into `games/`, for example
     `1892-02-28-9b0f13d4d6.html`, so `games/1.html` won't exist.
5. **Resolved.** The order is now proposed, not asserted:
   - `ROADMAP.md:806` lists "F-12 as iteration 8, before F-1.3" among the choices the owner's merge
     confirms;
   - PLAN.md's note says the shaping "proposes" it (`PLAN.md:50`);
   - the tense is fixed: "the owner decided to move the Markdown demo" (`ROADMAP.md:108`).

## What holds

- F-12's block has every field of *The block*. The original request is quoted verbatim, the same in
  the row, the block and PLAN.md's row 8. Each of the two owner decisions has a default, a reason,
  the alternatives and an owner-decision mark. The other choices are marked "proposed, confirmed by
  the owner's merge".
- The queue is consistent:
  - F-12 is `accepted` with iteration 8;
  - F-1's row adds "8 is F-12";
  - PLAN.md's row 8 and the "after F-12" row agree with the note;
  - open questions 4 and 7 are annotated, not re-decided, and F-1's "Out of scope" bullet
    (`ROADMAP.md:83-85`) matches.
- The workflow's command runs as written. On the scratch copy it wrote `index.html`, `assets/` and
  five `games/*.html`, with `data-site="pgn-postmortem-demo"` and no `quiz.html`. Nothing collides
  with `/markdown/`.
- `requirements.txt` is only `chess==1.11.2`. `history.js` is package data (`pyproject.toml:20`),
  so a non-editable `pip install .` in the workflow carries it.
- Round 02 only adds checks (done-when 2's GitHub run, done-when 3's link-following). Nothing is
  weakened.
- Nothing contradicts the decided items: no Stockfish in the workflow, nothing new hosted, and no
  run on the owner's data.

## Findings

1. **non-blocking**: the pre-merge `workflow_dispatch` run has two side effects the block doesn't
   mention.
   - **It shares the `pages` concurrency group,** which has `cancel-in-progress: true`
     (`pages.yml:17-19`). A branch run started while a Pages run of `main` is in progress cancels
     that deploy, and a push to `main` during the branch run cancels the branch run.
   - **The run ends red by design,** because the deploy job is refused (`ROADMAP.md:764-765`).
     CLAUDE.md says only the three gates decide a merge, but a red Pages run next to the change
     invites the question.
   - **Suggested fix:** do one of these, and have the PR note which:
     - guard the deploy job with `if: github.ref == 'refs/heads/main'`, so the branch run is green
       and deploys nothing;
     - scope the concurrency group by ref;
     - or say in done-when 2 that the run is started when no Pages run is in progress, and that its
       red deploy job is expected.
2. **non-blocking**: the check that the `baseurl` was rewritten before the merge depends on having
   Jekyll locally.
   - **Where:** done-when 2 shows "one rewritten link of the Markdown index" only "if Jekyll ran"
     locally (`ROADMAP.md:759-762`).
   - **The gap:** the GitHub run always runs Jekyll, but for it the PR records only the artifact's
     file contents (`ROADMAP.md:765-766`). File contents can't show a wrong `baseurl`, as round 01
     noted. Without local Jekyll, the `baseurl` is first checked after the merge, by done-when 3.
   - **Suggested fix:** also require, for the GitHub run's artifact, one game link from
     `markdown/index.html` as written, starting with the base path plus `/markdown/`. It costs one
     `grep` on the downloaded artifact.
3. **non-blocking**: the README's demo paragraph has a second sentence that the change makes wrong.
   - **Where:** `README.md:14-15` follows the demo link with "The same pages are also [browsable on
     GitHub](examples/docs/index.md)."
   - **The problem:** once the root is the library's site, "the same pages" are the ones at
     `/markdown/`, not the live demo.
   - **Why it's worth fixing in the scope:** the README bullet (`ROADMAP.md:744-746`) names only
     "the 'Live demo' line", and "Out of scope" excludes rewriting "beyond the demo line"
     (`ROADMAP.md:788-789`).
   - **Suggested fix:** name that sentence in the README bullet as part of the demo paragraph, to be
     reworded (for example, that the Markdown pages are browsable on GitHub).
4. **non-blocking**: done-when 3's closing line still uses the old defect clause.
   - **Where:** "A failure caused by the workflow or the content goes the defect path"
     (`ROADMAP.md:778`).
   - **The mismatch:** the block widens `CLAUDE.md`'s clause to library code, the manifests and
     `examples/site/analyzed/` (`ROADMAP.md:737-740`), and the triggers now include library changes.
   - **Suggested fix:** refer to the widened clause (for example, "a failure caused by this
     repository, as `CLAUDE.md`'s post-merge check defines it"), so the two can't drift.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged on 2026-09-26 as `dd10a86` (pull request #27) by the owner ("ok merged"). CI on the merge commit: success https://github.com/diegoami/pgn-postmortem/actions/runs/36231997070.

- **F-12's block has every field of the block format,** with the owner's two decisions (the library site from the five classic games; the Markdown demo moved to `/markdown/`), each with its default and reason, and the proposed items marked (the `daily_games` input, the site key `pgn-postmortem-demo`, the Jekyll `baseurl`, the pre-merge `workflow_dispatch` run).
- **Statuses and the iteration table are consistent:** F-12 is iteration 8, and F-1.3 comes after it; F-1's open questions 4 and 7 are annotated.
- **Only `ROADMAP.md` and `PLAN.md` changed,** plus the review records.

Left for F-12's implementation (put in the implementer's brief), round 02's non-blocking findings:
- **Finding 1:** the `workflow_dispatch` run on the branch shares the `pages` concurrency group and its deploy job is refused, leaving the run red; guard the deploy job to `main` or scope the group by branch.
- **Finding 2:** check one rewritten `/markdown/` link in the GitHub run's artifact.
- **Finding 3:** reword README's "The same pages are also browsable on GitHub" sentence too.
- **Finding 4:** done-when 3's closing line refers to `CLAUDE.md`'s widened defect clause.

— Implementer, Claude Opus 5.5 (claude-opus-5-5)
