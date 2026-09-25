# Review 017 — shape F-8, implementation, round 02

- **Revision covered:** `aadeb49cb1cb0320c8091af5c3be984e8360a485` (branch `shape-f8`, pull
  request #17). After `git fetch origin`, `git rev-parse origin/shape-f8` equals the pull request's
  `headRefOid`. The commits since round 01 are `c9b4cc7` (the round-01 record) and `aadeb49` (the
  answer to it).
- **Files checked:** `PLAN.md`, `ROADMAP.md`, `reviews/017-shape-f8-impl-01.md`. Obtained from the
  pull request's files (`gh pr view 17 --json headRefOid,files`) and checked against the local diff
  from the merge base (`git diff --name-only $(git merge-base origin/main origin/shape-f8)..origin/shape-f8`,
  merge base `971b42d`). The two lists match. The changes since round 01 were read with
  `git diff cf2a8ec aadeb49`. For the context, `pgn_postmortem/cli.py`, `pgn_postmortem/site.py`,
  `pyproject.toml` and `requirements*.txt` were read on `main`. Nothing was run except
  `node --version`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that
  did not see the change being written. It is the same reviewer as round 01.
- **Mode:** Claude Code.

## What was checked

- **The round-01 record is committed unchanged.** `reviews/017-shape-f8-impl-01.md` at `aadeb49`
  is byte-identical to the file the reviewer wrote (checked with `cmp`).
- **The original wording is still verbatim** in F-8's row, the block and PLAN.md's row 5. The only
  other edits are the ones the commit message lists:
  - F-8's row loses "Not shaped yet.";
  - F-1.4's slice cell gains "(carrying no script: F-8's history is for the site only)";
  - PLAN.md row 5's mode cell;
  - F-8's block.
- **The "proposed, confirmed by the owner's merge" items are clearly marked.** They are in their
  own bullet, apart from the three owner decisions: the limit of 10 (now with a reason), keys by
  move and the `data-` attributes, the site key and the scoped clear, the `history=False` switch,
  and the "script" gate with Node 22.
- **The statements about browsers are accurate enough for a scope:**
  - Project sites on `<user>.github.io` share one origin. A custom domain doesn't, so "all of a
    user's GitHub Pages sites" is slightly broad.
  - Chrome gives local `file://` pages one shared storage.
  - Some browsers give `file://` pages or private windows no usable storage.
  - Safari's tracking prevention caps script-written storage at 7 days. Strictly, it is 7 days of
    Safari use without interacting with the site, and it doesn't apply to web apps added to the
    home screen. "After 7 days without a visit" is a fair short form.
- **PLAN.md row 5.** "The owner's standing choice of 2026-09-24, applied 2026-09-25" reads the
  slot's "the owner's usual way of working is Claude Code mode". The owner's merge confirms it.

## The round-01 findings

1. **The history stays within its own site: resolved.** Stored keys carry the tool's prefix and a
   site key. Clear removes only that prefix plus site key. "Recently viewed" and the marks show
   only games in the index's current list. The Node tests now cover all three, including "another
   site key's data and unrelated keys survive". The site key itself has two loose ends (findings 1
   and 2 below).
2. **The data in the pages: resolved for the article and the index.** The scope names them: the
   article's game id, each answer's move (`31b`), and each index entry's id and current question
   moves. With the links and titles already in the index's list, that covers:
   - recording a view and a revealed answer;
   - "Recently viewed", looked up in the index's own list;
   - "k/m" against the current questions.

   The site key is the one thing missing from the list (finding 1).
3. **The gate: resolved.** The block now gives:
   - the command, `node --test tests/js/`;
   - the coverage, the seven cases;
   - when it runs: every change, locally and in CI;
   - 1 repeat, and a deterministic failure model;
   - Node 22 pinned with `actions/setup-node`;
   - the local rule: Node 22 or newer, and without Node the builder says so and CI's run decides;
   - the byte-identity tie between the page and `pgn_postmortem/static/history.js`, declared as
     package data;
   - the "three gates" edit to `CLAUDE.md`.

   That is every column of the table and fits gates discipline 1. Two points about how the
   command runs are in finding 3.
4. **Network calls: resolved.** They are rejected by name. `.src =` and "no other `<script>`" from
   the suggestion are not in the list. "No URL" and "no `src` attribute" cover most of that.
5. **The reference for "same as before": resolved in intent.** Now `history=False` is compared
   with the pre-F-8 golden pages. The `hidden` attribute is checked in the static HTML. How this
   check is kept and what it proves is finding 4.
6. **`file://` in the owner's check: resolved** ("both online and from `file://` on the desktop").
7. **When the history is lost: resolved:** the browser's data cleared, Safari's 7-day cap, and a
   changed id.
8. **The EPUB in F-1.4's row: resolved.**
9. **The record fixes: resolved.** "Not shaped yet" is gone, the date is reworded, and the limit
   of 10 has a reason.

## Findings

1. **non-blocking — the site key has no place in the pages the done-when allows.** The scope says
   the site key "is written into the pages at build time" (`ROADMAP.md:332-333`). But:
   - the `data-` attributes are "a few … and only these" (`:338-342`), and the site key is not
     among them;
   - the script must be "byte-identical to `pgn_postmortem/static/history.js`" (`:370-371`), so the
     key can't be written into the script either.

   An article needs the key as much as the index does, since it writes under it. Suggested: add
   "each page: the site key" (for example on `<html>` or `<body>`) to the list. The intent is plain,
   so this doesn't block, but the implementation review should expect the key there.

2. **non-blocking — say what the site key comes from, and record that same-title books share one
   history.** "From the site's player (or title)" (`:333`) leaves the choice open, and
   `build_site` has no player: it receives only `title` (`site.py`, `build_site`).
   `cli.py:81` builds the title as `"Games of <player>"`, or `"Games"` without a player. So:
   - in practice the key comes from the title;
   - two books with the same title on one origin share one history. Two books of the same player
     built with the default title do, and so does every site built through the API with the
     default `"Games"`;
   - Clear on one of them clears the other.

   The filter on the index's current list keeps them from showing each other's games. So the cost
   is small, if the limit of 10 is applied *after* that filter. Renaming a book orphans its old
   history, which no Clear will reach. Suggested: name the source (the title, as `build_site` has
   it, or a new optional `site_key` argument and `--site-key` option). Record the shared-title
   consequence, and add a Node case: 12 stored games, 3 of them not in the list, still shows 9.

3. **non-blocking (not verified here) — show that the gate command runs the tests and cannot pass
   with none.** Since Node 21, `node --test`'s positional arguments are glob patterns. To my
   knowledge a bare directory like `tests/js/` is no longer searched for test files as it was in
   Node 20, and gives a "Could not find" error. I couldn't reproduce this: only `node --version`
   was allowed in this review. If it is right, the failure is loud, not a false green, and a glob
   such as `node --test "tests/js/*.test.mjs"` fixes it. Separately, a pattern that matches no
   file could report 0 tests and pass. Suggested: the implementation shows the gate's output with
   its test count, and the command is spelled as a glob if the directory form fails.

4. **non-blocking — the pre-F-8 golden pages need a path, a regeneration command, and a check
   that goes the other way too.** `:374-375`: "`build_site(..., history=False)` is byte-identical
   to the golden pages from before F-8, which are kept as they are, so nothing else in the pages
   changed."
   - **Path.** The documented command writes `tests/golden/site`, and "the new golden pages with
     the history are generated with the documented command" (`:376`). So one of the two sets has
     to move to a second directory. Neither the block nor the slot's list of generated paths
     names it.
   - **Regeneration.** F-9 to F-11 are next, and they will change the pages. A set "kept as it
     is" then has to be regenerated, and the switch exists only on `build_site`. Unless there is
     a command for it (for example a `--no-history` option on `site`), it can only be hand-edited,
     which the slot forbids. In F-8's own PR the set has to stay equal to `main`'s, or the
     comparison is circular. That is checkable in the PR's diff, and worth saying.
   - **What it proves.** The check proves the pages without the history are unchanged. It
     doesn't prove that the pages *with* the history differ only by the script, the containers
     and the attributes. The golden diff in F-8's PR shows that once, for a reviewer. A test that
     strips those three from the `history=True` pages and compares with the `history=False` pages
     would keep it true.

5. **non-blocking — "an installed (not editable) build includes the script file" doesn't say how
   it runs without the network.** `:377`. Building a wheel inside the tests gate needs
   `setuptools>=77` (`pyproject.toml`, `[build-system]`). It isn't in `requirements-dev.txt`, and
   venvs on Python 3.12 and later don't bring it. With pip's default build isolation, the build
   downloads it. That would give the tests gate, declared "deterministic", a dependency on the
   network. Suggested: pin `setuptools` in `requirements-dev.txt` and build with
   `--no-build-isolation`, then list the wheel's contents. Alternatively, make it a CI step
   (`pip wheel . --no-deps` and a listing), declared where the gates table can see it.

Nothing else changed beyond what the commit message lists.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
