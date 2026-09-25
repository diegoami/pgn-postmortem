# Review 018 — F-8, the reading history: implementation, round 02

- **Revision covered:** `471b2bff33c2065600c7f0b1ac7bfaabd3b12809`, the head of pull request #18
  (branch `iteration-5-reading-history`). After `git fetch origin` I checked out
  `origin/iteration-5-reading-history` in the reviewer's worktree. `git rev-parse HEAD` there
  equals `gh pr view 18 --json headRefOid`.
- **Files checked (29),** from `gh pr view 18 --json files`. They are identical to
  `git diff --name-only 97cf76f..471b2bf`, where `97cf76f` is `git merge-base origin/main HEAD`
  and equals `origin/main`. The list is round 01's 28 files plus
  `reviews/018-f8-reading-history-impl-01.md`.
- **The changes since round 01** (`747e7c9..471b2bf`), all read in full:
  - `ffadaac` adds `reviews/018-f8-reading-history-impl-01.md`. `cmp` shows it is byte-identical
    to the round-01 file the reviewer wrote.
  - `db97323`:
    - `pgn_postmortem/static/history.js`;
    - `tests/js/history.test.mjs` (two tests);
    - `tests/js/page.mjs` (`addEventListener` and `dispatch` on the stand-in window);
    - `CLAUDE.md` (the script row);
    - the seven pages of `tests/golden/site/`, regenerated.
  - `471b2bf`: `pgn_postmortem/site.py` (the docstring) and `README.md` (a line rewrapped).
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), the fresh-context Claude Code subagent that
  wrote round 01, continued for the re-review (`PRINCIPLES.md`, *Reviewer sessions*). It re-read
  the current revision rather than trusting the PR body.
- **Mode:** Claude Code.

## What I ran

- **The gates** on `471b2bf`, in the worktree's venv, with Stockfish present:
  - `ruff check .`: all checks passed.
  - `pytest -q`: 157 passed.
  - `node --test 'tests/js/*.test.mjs'` on Node v24.21.0: **20 tests**, 20 passed. That is 18
    before plus the two new back/forward-cache tests.
- **CI on the head,** run 36138621189. Both legs are green.
  - The logs show 157 passed on 3.11 and on 3.13.
  - The 3.13 wheel step lists `pgn_postmortem/static/history.js`.
  - `setup-node` ran with `node-version: 22`, and the script gate reported
    `tests 20 / pass 20 / fail 0`.
- **The `--no-history` set.**
  - `diff -r` of `tests/golden/site-no-history/` against `origin/main`'s `tests/golden/site/`
    (extracted with `git archive`) shows them identical.
  - `git diff --quiet 747e7c9 HEAD -- tests/golden/site-no-history` confirms the set is unchanged
    since round 01.
- **The regenerated golden set.**
  - I took each of the seven pages at `747e7c9` and replaced round 01's script bytes with the
    current `history.js`. Every page then equals its page at the head. So nothing but the script
    changed in the pages.
  - A fresh build with the documented command matches `tests/golden/site/` under `diff -r`.
- **The blocking fix, reproduced the way I found the bug.** I used headless Chromium (Playwright's
  build, `--headless=new`, driven over the DevTools protocol by a scratch script of my own that is
  not committed). It ran over `python3 -m http.server` on `127.0.0.1`, on a freshly built copy of
  the site. The steps: open the index, tap *Fabio Quick vs. AdaEx*, open its answer, go back.

  | step | round 01's build (`747e7c9`), the control | this head (`471b2bf`) |
  |---|---|---|
  | back to the index | `BackForwardCacheRestore`; `hidden=true`, no marks, recent list empty | `BackForwardCacheRestore` (a marker set before leaving is still there); `hidden=false`, marks `viewed · 1/1 answer`, one entry in the recent list, **without a reload** |
  | forward to the article, restored from the cache | its viewed time is not refreshed | its viewed time is refreshed |
  | the answer's key removed, then back to the index | still hidden | the mark now reads `viewed · 0/1 answer`: the index shows what is stored now, and a stale mark goes |

- **Breaking the fix.** I made five mutations to `history.js`, one at a time, and restored the
  file after each. `git status` was clean afterwards, and the gate was back to 20 of 20.

  | break | the script gate | red test(s) |
  |---|---|---|
  | no `pageshow` handler (the listener renamed) | exit 1 | both new tests |
  | `persisted` ignored | exit 1 | *an article shown again … is recorded as viewed again* |
  | the index not registered for a refresh | exit 1 | *an index shown again … shows the history as stored now* |
  | the article not registered for a refresh | exit 1 | *an article shown again …* |
  | `startIndex` returning `null` in place of its refresh | exit 1 | *an index shown again …* |

## Round 01's findings

1. **blocking — the stale index after "back": fixed.**
   - `start()` registers one `pageshow` listener on the window (`history.js:278-292`). It acts
     only when `event.persisted` is set, and it calls the refreshes that `startArticle` and
     `startIndex` return (`history.js:103-118, 236-254`). Each refresh is inside its own `try`.
   - The listener is registered only when the site key is valid and storage works. So with no
     storage, the page still gets nothing, as before.
   - The two tests went red when I broke the fix, and the fix works in a real browser (both
     above).
   - `CLAUDE.md`'s script row now names this coverage.
2. **non-blocking: fixed.**
   - `pgn_postmortem/site.py:4-6` now reads "The site is HTML and one stylesheet, with a small
     script inlined in every page for the optional reading history".
   - `README.md:195-197` is rewrapped. Its text is unchanged apart from the line breaks.
3. **non-blocking: answered.**
   - The PR body now has a section *Design choices under artistic license*: the CSS inside the
     script, the site key's format and `--site-key`, the index wording, no `*` in the script, the
     escape test's allow-lists, CI on 3.13 only, and the storage layout with its probe key.
   - The body also keeps the declaration that the wheel step and the `setuptools` pin were
     confirmed by the merge of #17, and the implementer undertakes to repeat both in the
     completion note.
   - That is what round 01 suggested. No `ROADMAP.md` edit is needed.

## Findings

1. **non-blocking — only the article test notices that `persisted` is ignored.**
   - With the `persisted` check removed, the index test stays green. That test dispatches only
     `persisted: true` to the index.
   - This does no harm. An index that re-renders on the first `pageshow` would only redraw what it
     just drew. The article test, which dispatches `persisted: false` first, catches the mutation.
   - I mention it only so that the claim "each break turns a test red" is read per mutation, not
     per page. No change is needed.

Nothing else is new. The fix stays within F-8's scope: no network use, no URL, no `*`, and no
other storage keys. The static markup is unchanged, and so is the `--no-history` output. Every
done-when item that the gates can check is met, with a test that goes red when its behaviour is
broken. One item is still open: the owner's check (done-when 3), which is to be recorded on the
PR before the merge. As round 01 asked, it should include going back to the index on the served
site.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
