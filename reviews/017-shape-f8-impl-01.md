# Review 017 — shape F-8, implementation, round 01

- **Revision covered:** `cf2a8ecd98d2d235528dbe5113ab04d853fd8dd1` (branch `shape-f8`, pull
  request #17, one commit on top of `main` at `971b42d`). After `git fetch origin`,
  `git rev-parse origin/shape-f8` equals the pull request's `headRefOid`.
- **Files checked:** `PLAN.md`, `ROADMAP.md`. Obtained from the pull request's files
  (`gh pr view 17 --json headRefOid,files`) and checked against the local diff from the merge base
  (`git diff --name-only $(git merge-base origin/main origin/shape-f8)..origin/shape-f8`, merge base
  `971b42d`). The two lists match. Files were read with `git show origin/shape-f8:<path>`. For the
  context, `pgn_postmortem/site.py`, `pgn_postmortem/collection.py`, `README.md`, the CI workflow,
  `pyproject.toml`, `CLAUDE.md` and `PRINCIPLES.md` were read on `main`. Nothing was run except
  `node --version` (v24.21.0) and `node --help`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that
  did not see the change being written.
- **Mode:** Claude Code.

## What was checked

- **The original wording is verbatim.** F-8's request cell on `main`, its cell on the branch, the
  block's *Original request* and PLAN.md's row 5 are the same string: "A local history reminding
  what games have you been watching and ideally the spoilers you have looked".
- **The block has every field** of *The block* (ROADMAP.md): original request, player value, scope,
  done when, out of scope, depends on, open questions.
- **Owner decisions.** The three decisions each carry a recommended default, a reason and the
  owner's choice. The alternatives not chosen (marks inside articles, export/import) also appear
  in *Out of scope*. The items "proposed with this shaping, confirmed by the owner's merge" are in
  their own bullet, apart from the decisions. The repository cannot show that the owner made these
  decisions; the owner's merge is that check.
- **Consistency with the site.** Every answer is a `<details class="answer">` inside
  `<div class="moment" id="moment-N">` (`site.py`, `moment_html`). The index lists the games by
  year, with "N questions" in each entry's meta (`index_html`). `PostmortemId` is the content id
  (`collection.py`, `game_id`: start position, result, date, moves), and every article's PGN
  carries it. "No JavaScript" is stated at `site.py:13` and `README.md:194`, and the scope says
  both will change. Nothing conflicts with the decided items: there is no server, no hosting, and
  every game still gets its own article.
- **Review 016's leftover findings are resolved.** Finding 1: F-8's row now credits "no server" to
  F-1's scope and "no JavaScript" to `README.md` and `pgn_postmortem/site.py`. Finding 2: PLAN.md's
  F-1.3 and F-1.4 rows now read "after F-8 to F-11" and "after F-1.3". F-1's iteration cell reads
  "1 and 2 (F-1.1, F-1.2); F-1.3 and F-1.4 come after F-8 to F-11 and are numbered when they
  start (… 5 is F-8)". The table, F-1's row and the recorded order agree.
- **Nothing else changed.** The diff touches F-1's iteration cell and F-8's row in the queue, adds
  F-8's block, and changes PLAN.md's rows 5 to 7+. The commit message lists all of these.

## Findings

1. **blocking — the done-when doesn't make the history stay within its own site. A wrong
   implementation could erase other data or show games that aren't in the book.**
   `ROADMAP.md:336` and `:356` say "Clear history" "removes all the history" and "removes
   everything". `localStorage` is shared by origin, not by site. All GitHub Pages project sites
   of one user share one origin, for example `diegoami.github.io/chessgamescollection` and
   `diegoami.github.io/pgn-postmortem`. Some browsers also give every page opened as `file://` the
   same storage (Chrome does). So:
   - an implementation that calls `localStorage.clear()` passes the listed test, and erases the
     data of every other page on that origin;
   - a history written by another book on the same origin, or by an earlier build that had
     other games, would show in "Recently viewed" with links that go nowhere, and no listed test
     would catch it. The same happens if the list stores titles or links rather than looking the
     ids up in the index it is on.

   Suggested: the scope says that the history lives under the tool's own key prefix, and that the
   index shows only games present in its own list, with titles and links taken from that list.
   The Node tests then cover: Clear leaves a key that the history didn't write untouched; a
   stored id that isn't in the index is not shown, and nothing breaks.

2. **blocking — done-when item 1 forbids the markup that the scope needs.** `ROADMAP.md:346-347`:
   "nothing else in the page changes except the script and the (hidden) history containers". The
   script has to know three things:
   - the game's id on an article;
   - which move each `<details class="answer">` is about (answers are keyed by move, not by
     `moment-N`);
   - on the index, each game's id, and the move keys of its current questions, to count "k/m"
     against "questions the game still has" (`:355`).

   The pages carry none of these as data today (`moment_html`, `index_html`). The index has only
   the prose count "four questions", and the article's move appears only in the caption's prose.
   As written, the contract can be met only by scraping prose. Another way to meet it is to keep
   the question list stored at the last visit, and then after a rebuild the count is no longer
   the current one. Suggested: name the data the pages gain, for example `data-` attributes for
   the game id on the article and on each index entry, the move key on each answer, and the
   current question keys on each index entry. Allow those in item 1, and have a Python test assert
   that they match the moments the site computes.

3. **blocking — the new gate isn't specified enough for the gates table.** Gates discipline 1 in
   `PRINCIPLES.md` asks for the command, the coverage, when it runs, the repeats and the failure
   model. `ROADMAP.md:349` and `:360-361` give only `node --test` and "CI installs Node (pinned)",
   and ask the table for "its command, coverage and failure model". Missing:
   - **the exact command with its path.** A bare `node --test` searches the whole working tree
     for test files, skipping only `node_modules`. The slot says `.claude/worktrees/` holds full
     copies of the repository (it exists in this checkout). Bare `node --test` would also run the
     copies of the tests in other worktrees, and could fail or pass because of another branch.
     Name the directory, for example `node --test tests/js/`.
   - **when and repeats** (for example: every change locally, CI on every push and pull request;
     1 repeat; deterministic, with an injected clock);
   - **the Node version**, which "pinned" leaves unnamed, and **what happens locally without
     Node**: fail, or skip as the Stockfish tests do. A skip lets a local run pass without the
     gate having run, which is acceptable only if CI always runs it;
   - **the tie between the tested script and the inlined one.** The Node tests test the script's
     source, and the pages carry a copy of it. No listed test checks that the copy is that source,
     so the two can drift apart with every gate still passing. Suggested: a Python assertion that
     the inline script is exactly the canonical source file. Also say where that file lives. If it
     is a `.js` file under `pgn_postmortem/`, it needs package data in `pyproject.toml`. CI installs
     with `-e .`, so it would not notice if the file were missing from the package;
   - the slot sentence "Only the two gates above decide a merge" (`CLAUDE.md:99`), which the new
     row makes wrong. It should be listed with the table change.

4. **non-blocking — the check that the script contacts no network looks only for URLs.** Item 1
   checks "no `src` attribute and no URL in it". A script can send data with no URL literal in it,
   for example `fetch(location.href)`, `navigator.sendBeacon`, `new Image().src = …` or `import()`.
   The scope promises the history is "never sent anywhere" (`:325`). Suggested: also assert that
   the script uses no network API (`fetch`, `XMLHttpRequest`, `sendBeacon`, `WebSocket`,
   `EventSource`, `import(`, `.src =`), and that the page has no other `<script>`.

5. **non-blocking — "the same article as before" has no stated reference.** Item 1 says the
   golden files are regenerated in the same change, so the pages from before the change are no
   longer in the tree. Suggested: say what the test compares with, for example this build with
   the script, the containers and the new data attributes stripped, compared byte for byte with
   the rendering at the parent commit. Also have a Python test that the history containers carry
   `hidden` in the static HTML. Otherwise "hidden without the script" is only asserted on the Node
   stand-in page (`:357`).

6. **non-blocking — the owner's check doesn't name `file://`, where the stand-in storage can't
   stand for a real browser.** `ROADMAP.md:362-365` says "on a phone and on a desktop browser".
   F-1 supports `file://`, the F-8 row itself says storage there differs between browsers, and
   F-1.2's check named `file://`. In a browser where each local file is its own origin, the
   article's writes don't reach the index. Only a person can see that. Suggested: the check
   covers the site served over HTTP and opened from `file://`, and the scope says what the index
   shows when it sees no history (nothing, with no false marks).

7. **non-blocking — the scope doesn't say when the history is lost.** Two cases are not recorded:
   - Safari deletes storage that scripts wrote for a site after 7 days without a visit (its
     tracking prevention). A reader "on the road" who comes back after a week sees an empty
     history.
   - A game whose id changes (a corrected `Date` or `Result`, see F-7) loses its history.

   F-11's note records the second risk for notes. Suggested: one line in the scope, so that the
   feature doesn't promise more than it keeps.

8. **non-blocking — the EPUB constraint is recorded only in F-8.** "The EPUB (F-1.4) carries no
   script" (`:340`) binds an iteration that has not been shaped yet. F-1.4's row in F-1's split
   table doesn't mention it, and whoever shapes F-1.4 reads that row. Suggested: add it to F-1.4's
   row, or to its done-when (the EPUB contains no `<script>`).

9. **non-blocking — small record inconsistencies.**
   - F-8's queue row (`ROADMAP.md:20`) still says "Not shaped yet." and, a few sentences later,
     "Shaped below." F-5's and F-6's rows dropped the first when they were shaped.
   - PLAN.md row 5 gives the mode as "Claude Code (owner, 2026-09-24)". F-8 was requested on
     2026-09-25 (its row), so that date cannot be the owner's choice of mode for F-8. The date
     looks copied from row 4.
   - The "proposed, confirmed by the owner's merge" items give no reason for the limit of 10.

Nothing else changed beyond what the commit message lists.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
Blocking findings remain: 1, 2 and 3.
