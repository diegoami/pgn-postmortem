# Review 018 — F-8, the reading history: implementation, round 01

- **Revision covered:** `747e7c9447bb60a11179976586a11b3cf689517f`, the head of pull request #18
  (branch `iteration-5-reading-history`). `git rev-parse HEAD` in the reviewer's worktree, after
  `git fetch origin` and a checkout of `origin/iteration-5-reading-history`, equals
  `gh pr view 18 --json headRefOid`.
- **Files checked (28),** from `gh pr view 18 --json files`. They are identical to
  `git diff --name-only 97cf76f..747e7c9`, where `97cf76f` is `git merge-base origin/main HEAD`
  and equals `origin/main`:
  `.github/workflows/ci.yml`, `.gitignore`, `CLAUDE.md`, `README.md`, `pgn_postmortem/cli.py`,
  `pgn_postmortem/site.py`, `pgn_postmortem/static/history.js`, `pyproject.toml`,
  `requirements-dev.txt`, `tests/golden/site-no-history/**` (8 files: `assets/style.css`,
  `index.html` and six `games/*.html`), `tests/golden/site/index.html` and its six
  `games/*.html`, `tests/js/history.test.mjs`, `tests/js/page.mjs`, `tests/test_history.py`,
  `tests/test_site.py`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. It
  had not seen the implementation.
- **Mode:** Claude Code.
- **The rules applied:** `PRINCIPLES.md` (the verdict protocol and the six gates disciplines), the
  project slot of `CLAUDE.md`, F-8's block in `ROADMAP.md` (the scope and done-when are the
  contract), the three points that the completion note of `reviews/017-shape-f8-impl-03.md` left
  for the implementation, iteration 5 of `PLAN.md`, and `reviews/README.md`.

## What I ran

- **The gates,** in a fresh venv in the worktree (`requirements-dev.txt`, then `pip install -e .`,
  with Stockfish present):
  - `ruff check .`: all checks passed.
  - `pytest -q`: 157 passed.
  - `node --test 'tests/js/*.test.mjs'` on Node v24.21.0: 18 tests, 18 passed.
- **CI on the head,** run 36137183258. Both legs are green.
  - The job logs show 157 passed and 0 skipped on 3.11 and on 3.13.
  - On 3.13, the wheel step printed `pgn_postmortem/static/history.js … 8845`.
  - `actions/setup-node` ran with `node-version: 22`, and the script gate reported
    `tests 18 / pass 18 / fail 0`. The Node gate and the wheel step really run, with a nonzero
    count.
- **The first golden set.** I compared `tests/golden/site-no-history/` with `origin/main`'s
  `tests/golden/site/`, extracted with `git archive`, using `diff -r`. The two are identical:
  8 files on each side.
- **Sites built from the fixture** with the documented commands, with and without `--no-history`,
  into a scratch directory. Each matches its golden set under `diff -r`. I read the index, an
  article and the inlined script.
- **Breaks.** I made 20 mutations, one at a time, with `__pycache__` and `.pytest_cache` cleared
  first. For each one I checked that the edit landed exactly once, ran the gate and restored the
  file. `git status` was clean afterwards.

  | break | gate | red test(s) |
  |---|---|---|
  | clear removes every key | script | Clear history removes this site's keys only… |
  | clear matches `pgn-postmortem:` without the site key | script | the same |
  | clear without the confirmation | script | the same |
  | no site key in the stored prefix | script | opening an article…, revealing…, the index lists…, k/m… (6+) |
  | the recent list also shows stored games that are not in the index | script | the index lists the latest 10… only games in its current list |
  | no limit of 10 | script | the same |
  | k counts every revealed key of the game (stale answers) | script | the k/m mark counts only answers of the game's current questions; corrupt stored data… |
  | a corrupt viewed time is trusted | script | corrupt stored data is ignored, not trusted |
  | no try around the storage probe, and no outer try | script | storage that is writes that throw… |
  | a `window.fetch(` in the script | tests | `test_the_script_makes_no_network_use…` (and both golden tests) |
  | an `https://` in a comment of the script | tests | the same |
  | `history=False` keeps `data-move` | tests | the no-history golden test, the strip test, `test_without_the_history_the_pages_carry_none_of_it` |
  | `history=False` keeps a `data-site` | tests | the same three |
  | the history section without `hidden` | tests | `test_the_history_section_is_hidden_in_the_static_html`, the strip test, the golden tests |
  | an extra `data-seen` on the index entries | tests | `test_the_data_attributes_are_the_named_ones_and_only_those`, the strip test, the escape test, the golden tests |
  | a `src` on the script element | tests | `test_every_page_carries_the_script_inline…`, the link test, the golden tests |
  | a history paragraph in the footer | tests | the strip test, the golden tests |
  | `site_key` ignored | tests | `test_the_site_key_follows_the_title…` and every case of the invalid-key test |
  | the package-data line removed | tests | `test_the_package_declares_the_script_as_package_data` |
  | the package-data section removed (wheel) | CI's wheel step, run locally | `pip wheel --no-deps --no-build-isolation` builds the wheel, and `grep -F pgn_postmortem/static/history.js` exits 1. It exits 0 with the section. |

  One more break is worth recording. With the probe outside its `try` but the outer `try` in
  `history.js:267-271` kept, the script gate stays green, and that is correct: the page still
  works and the history stays hidden. Only removing both turns it red. The outer `try` is the
  defence that the "storage that throws" tests cover.
- **A real browser.** I played the site in Chromium (Playwright's build, `--headless=new`, driven
  over the DevTools protocol by a scratch script that is not committed), both from `file://` and
  over `http://127.0.0.1` with `python -m http.server`. The steps: open the index, tap a game,
  open its answer, then go back. The result is finding 1.

## The contract, checked

- **Script inline, byte-identical, no `src`:**
  `test_every_page_carries_the_script_inline_byte_identical_to_the_package_file` checks 7 pages,
  one `<script>` in each, with empty attributes and a body equal to the file.
- **No URL, network or loading call:** the test covers all seven names of the done-when, plus URL
  schemes, `://`, `www.`, protocol-relative links, `src`, `</script`, `<!--` and `*`. I read the
  script too. It calls only `localStorage`, `confirm`, `Date.now` and the DOM, and makes no
  network or loading call.
- **Storage:**
  - Every key is `pgn-postmortem:` + the site key + `:` (`history.js:256`). The site key excludes
    `:`, so `KEY:` is never a prefix of `KEYx:`, and the test covers `${SITE}x`.
  - Clear collects the matching keys first, then removes them (`history.js:214-229`), and only
    after `confirm` (`:238-244`). The test checks that another book's keys, a longer site key's
    keys and `theme` all survive.
  - The only other key the script writes is the probe, `pgn-postmortem:probe`, which it removes
    at once.
- **Recently viewed:**
  - The script iterates the index's own `li[data-game]` entries and never enumerates storage
    for them, so the list is filtered by construction. It then sorts newest first and takes 10
    (`:175-192`).
  - The test places a removed game and another site's game later than all of the index's games.
- **k/m:** `markText` counts only `game.moves` (`:117-129`), so a stored `12w` for a question that
  is no longer asked is ignored. `2/4` is tested too.
- **Answers keyed by move:**
  - `move_key(review.board_before)` sets both `data-move` in the article and `data-moves` in the
    index (`site.py`, `moment_html` and `index_html`).
  - `test_the_data_attributes_are_the_named_ones_and_only_those` checks them against
    `critical_moments()`.
- **Graceful failure and corrupt data:**
  - A missing, `null` or throwing localStorage, and writes or reads that throw, are all tested,
    and the page still works in each case.
  - A bad timestamp or a bad revealed value is ignored (`TIME` and `=== "1"`).
- **The strip test:**
  - It removes the `<script>…</script>\n`, a `section`/`div` carrying `hidden`, and exactly
    `data-site|data-game|data-move|data-moves`. It leaves the board's `data-r` and `data-f` alone.
  - It gets the `--no-history` page byte for byte, and the file sets and `assets/style.css` are
    equal.
  - The styling is a `<style id="history-style">` that the script adds at run time
    (`history.js:38-43, 162-170`), so it goes with the script. The CSS variables it uses
    (`--answer`, `--fg`, `--link`, `--box`, `--rule`) all exist in `style.css`.
  - This is the first option in point 1 of the 017 completion note, in the script instead of the
    markup, and it meets that point.
- **The site key:**
  - `default_site_key` is the ASCII slug of the title (at most 40 characters) plus the first 8
    hex digits of its SHA-256. `check_site_key` and `SITE_KEY` hold the same rule as the script's
    `SITE` regex.
  - An invalid key is rejected before anything is written, even with `history=False` and an
    empty collection.
  - `--site-key` is an argparse type that gives a usage error (exit 2).
  - This names the option, per point 3 of the 017 note.
- **Package data and the wheel:**
  - `[tool.setuptools.package-data] pgn_postmortem = ["static/*.js"]` is in place, and
    `setuptools==84.0.0` is pinned (the build system requires `>=77`).
  - The CI step runs with bash's `-eo pipefail`, so a `grep` miss fails it. I reproduced that
    above.
- **`CLAUDE.md`:**
  - The new "script" row has every column the discipline asks for, and "three gates" replaces
    "two".
  - The second golden directory is in the generated-paths list and has its regeneration command.
  - The tests row covers the history tests.
  - The wheel step is declared in the tests row's "when" column, with its command and the pinned
    `setuptools`, and in its failure model ("builds without the network").
  - Point 3 of the 017 note allowed "record the step in the tests row … or give it its own row",
    so declaring it in the tests row meets discipline 1.
- **`README.md`:** it describes the history, how it can be lost, the site key, `--site-key`,
  `--no-history`, the gate with its quoted glob, and both regeneration commands.
- **Scope:**
  - The change to `tests/test_site.py` adds `script`, `button`, `hidden`, `type` and the four
    `data-` names to the escape test's allow-lists (`tests/test_site.py:222-230`). This is
    needed: that test lists every tag and attribute a page may carry, and the new markup is what
    F-8 adds. It is not scope creep.
  - Running the Node gate and the wheel step only in the 3.13 leg meets the done-when, which
    asks for "CI" and pins Node 22, not a Python matrix. Neither depends on the Python version,
    and `CLAUDE.md` declares it so.
  - Nothing out of scope was built: no sync, notes, quiz, engine link or in-article marks.
- **`ROADMAP.md` left unchanged:**
  - The status is right. F-5 and F-6 were marked `landed` by a later change after their merges,
    and the PR says F-8 "stays accepted until the merge". Setting `in review` would also have
    been allowed ("the agent sets the middle states"), but it was not done for F-5 or F-6 either.
  - The confirmed-items list is finding 3.

## Findings

1. **blocking — after "back", the index shows a stale history on a served site, such as GitHub
   Pages.**
   - `startIndex` renders once, when the script runs (`pgn_postmortem/static/history.js:231-245`).
     Nothing renders again when the browser restores the index from its back/forward cache.
   - In Chromium over `http://`, I opened the index, tapped *Fabio Quick vs. AdaEx*, opened its
     answer (both keys were stored) and pressed back. The DevTools protocol reported
     `BackForwardCacheRestore`: a marker set on the index before leaving was still there. The
     index showed `section hidden = true` and no marks. A reload then showed the section and
     `viewed · 1/1 answer`.
   - From `file://`, Chromium does not use that cache (`SchemeNotHTTPOrHTTPS`), so the history
     was right there. That is why a `file://` run can miss the problem.
   - On a phone, "back" is the usual way to return to the index, and the owner's book is served
     from GitHub Pages. So the reader returns and does not see the game they just read. That is
     the player value of F-8, and the scope says "The index shows: a 'Recently viewed' list … the
     latest 10".
   - I tried a fix in a scratch copy of the page and it works. In `startIndex`, add
     `win.addEventListener("pageshow", function (event) { if (event.persisted) { render(…); } })`.
     With it, the same run showed the section and the mark after back.
   - Needed for this finding: the fix, and a script-gate test in which the stand-in `window`
     dispatches `pageshow` with `persisted: true` after the storage changed, shown failing first.
     An article restored the same way does not refresh its viewed time. The same listener can
     re-stamp it (optional).
   - Discipline 5 applies: "Assert what a person would notice … then play it."

2. **non-blocking — the module docstring still opens with "The site is plain HTML and one
   stylesheet".** See `pgn_postmortem/site.py:4`. The next paragraph corrects it, but the
   opening sentence no longer holds when the history is on. Also, `README.md:195` is one
   unwrapped 165-character line in a file wrapped at about 100. Both are cosmetic.

3. **non-blocking — point 3 of the 017 completion note is met only in the PR body.**
   - The note asked that the CI wheel step and the `setuptools` pin "join the list confirmed by
     the merge" (F-8's block, `ROADMAP.md:439`). The PR instead declares them "confirmed by the
     owner's merge of #17", on the grounds that both are already in F-8's merged done-when.
   - That reasoning holds: done-when 1 names the wheel step, the `pip wheel --no-deps
     --no-build-isolation .` command and the pinned `setuptools`. So nothing new needs the owner's
     confirmation, and the list would only repeat it.
   - Two things are recorded only in the PR body, which is not a record file:
     - the departure from the note;
     - the invented names and choices (`--site-key`, the key's format, the mark's wording, the
       probe key).
   - `README.md` and `CLAUDE.md` do record `--site-key`.
   - This review now records the departure. It would be tidy for the implementer's completion
     note to repeat it and list the *Artistic license* choices. No `ROADMAP.md` edit is required.

No other finding. I checked the scope, the done-when items, `CLAUDE.md`, `README.md`, CI and
the tests, and they are sound: every done-when item has a test that goes red when its behaviour
is broken. The owner's check (done-when 3) is still pending, as the PR says. It must be done after
finding 1 is fixed, and it should include going back to the index on the served site.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
One blocking finding remains (finding 1: the index is not refreshed when restored from the back/forward cache).
