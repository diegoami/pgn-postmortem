# Review 024, defect fix "The final position looks skewed" (board squares), implementation round 01

- **Revision covered:** `c96537d4458b2af6bfc07bcc3d89f43a50ee059a`, the head of pull request #24
  (branch `fix-board-squares`). The checked-out `HEAD` (detached at `origin/fix-board-squares`)
  equals the PR's `headRefOid`.
- **Base:** `9fe7e1d385c08c843dc0c6fe30718df40e290615` (`git merge-base origin/main HEAD`, equal to
  `origin/main`).
- **File list and how it was obtained:** `gh pr view 24 --json files` and
  `git diff --name-only <merge-base>..HEAD` give the same 17 files:
  - `CLAUDE.md`, `pgn_postmortem/site.py`;
  - `tests/golden/site/assets/style.css` and `tests/golden/site/games/{2019-03-14-bf58e2afa0,
    2019-04-02-5d1415e1ac, 2020-06-01-9705c13f05, 2021-09-10-a9c90416b2, 2021-12-24-9137b96576,
    undated-5ce208cdcb}.html`;
  - the same seven files under `tests/golden/site-no-history/`;
  - `tests/test_boards.py` (new).
- **Commits:** `e792826` (the fix, the test, both golden sets) and `c96537d` (the gates table's
  "covers" cell).
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that did
  not see the implementation.
- **Mode:** Claude Code. The change is a defect fix under the defect path of `PRINCIPLES.md`
  (Claude mode: no design stage; reviewed like any change).
- **Contract:** the defect as reported by the owner ("The final position looks skewed"), the defect
  path in `PRINCIPLES.md`, and `CLAUDE.md`'s slot (the gates, the two golden sets and their
  commands, nothing hand-edited in generated output).

## What was checked

- **Gates, in a fresh venv in the reviewer's worktree** (`pip install -r requirements-dev.txt &&
  pip install -e .`, Stockfish on PATH, Node v24):
  - `ruff check .`: all checks passed;
  - `pytest -q`: 209 passed, none skipped;
  - `node --test 'tests/js/*.test.mjs'`: 32 passed.
- **CI:** run 36180583377 (`pull_request`, head `c96537d`): `test (3.11)` and `test (3.13)`
  success; the 3.13 job also runs the script gate and the wheel check.
- **The assertion fails on `main`'s code, for the right reason.** With `origin/main`'s
  `pgn_postmortem/site.py` swapped in (caches cleared), all four tests of `tests/test_boards.py`
  fail: the two single-board tests and the every-board test on `a8: ['bR']` / `h1: ['wR']` (a
  cell with no square colour of its own), the stylesheet test on "a gradient draws squares that the
  cells do not share". File restored; `git status` clean.
- **The fix.** `pgn_postmortem/site.py:635` gives every cell `l` or `d` from
  `chess.BB_LIGHT_SQUARES`; `:641` now always writes a `class` attribute (every cell has at least
  its colour). The stylesheet drops the `repeating-conic-gradient` from `.board` and colours
  `.board i.l`, `.board i.d`, `.board i.l.hl`, `.board i.d.hl` with `background-color` only
  (`site.py:1359-1365`), so the piece's `background-image` (the `.wK{background-image:…}` rules)
  is still drawn over the colour. Specificity: `.board i.l.hl` beats `.board i.l`; the piece rules
  set no colour.
- **The pre-blended highlight colours**, worked out by hand from the old translucent overlay
  (`rgba(255, 213, 0, a)` over the square, rounded): light mode, a = .45, over `#f0d9b5` →
  `#f7d764`, over `#b58863` → `#d6ab36`; dark mode, a = .4, over `#d8c3a0` → `#e8ca60`, over
  `#9c7453` → `#c49b32`. All four equal the committed values. In the screenshots below, `main`'s
  highlight pixels are (247, 215, 99) light and (231, 202, 96) dark; the head's are (247, 215, 100)
  and (232, 202, 96): within 1 per channel, the head's exactly the rounded blend.
- **Nothing else changed in the look:** `--light`/`--dark` in both schemes, the dark-mode block,
  the rank and file labels (`::before`/`::after`, colour, position), the piece set, `.board`'s
  size rules and `.infobox .board`, all unchanged in the diff. No JavaScript is involved in the
  boards; the stylesheet's only `http` strings are the SVG `xmlns` inside `data:` URIs (no
  network). No other code emits a board (`board_html` is called only at `site.py:914` and
  `:943`); `static/history.js` builds no board.
- **Both golden sets regenerated, and only as claimed.** Running both documented commands on the
  head leaves `git status` clean (the committed goldens are exactly what the code writes). Against
  a `git archive` of `main`: `assets/style.css` differs in both sets; the 12 article pages differ in
  160 lines, all of them board rows (`<i …>` lines), 8 per board, 10 boards per set; with
  `class="l"`/`class="d"` removed and the `l `/`d ` prefix stripped from the other class lists,
  every changed page is byte-identical to `main`'s. `index.html`, `quiz.html`, `history.js`,
  `examples/**` and `scripts/**` are identical to `main`'s.
- **`CLAUDE.md`:** the word diff of the tests gate's "covers" cell is a single insertion naming
  `tests/test_boards.py` and what it checks; nothing removed.
- **The test (`tests/test_boards.py`).** The single-board test covers both orientations, the four
  corners by hand, and the two highlighted squares with their exact class lists (`d hl`,
  `l wN hl`). The every-board test reads each board's squares from its own `data-r`/`data-f`
  labels, requires one of the two orientations and that no other cell carries a coordinate, checks
  for all 64 cells the colour, the piece (exactly one class, or none), the highlight (on the last
  move's two squares only) and no unknown class, and ties the infobox board to the article PGN's
  final position and each moment's board to its lichess FEN; it asserts both orientations were
  seen and at least 50 boards / 100 highlighted squares (55 / 110 today). The stylesheet test
  checks no gradient, no `background*` on any `.board` rule, no `background`/`background-image` on
  any cell rule, the four colour rules, and solid, distinct highlight colours in both schemes.
- **Mutations (each applied to `site.py`, `__pycache__` and `.pytest_cache` removed, only
  `tests/test_boards.py` run, then restored; `git status` clean afterwards).** All 12 went red in
  the intended test:
  1. the gradient back on `.board` → the stylesheet test ("a gradient draws squares…");
  2. a plain `background-color` on `.board` (no gradient) → the stylesheet test (`.board: …
     assert not ['background-color']`);
  3. `l`/`d` swapped in `board_html` → all three board tests (`a8: ['d', 'bR']`);
  4. `l`/`d` colours swapped in the CSS rules → the stylesheet test;
  5. the highlight moved one square (`square - 1`) → the three board tests (`f3: ['l', 'wN']`);
  6. the infobox highlighting only the to-square → the every-board test (`f8: ['d']`);
  7. a moment highlighting the move played instead of the move that led to it → the every-board
     test (`d1: ['l']`);
  8. the colour class dropped on one cell (e4) → the board tests (`e4: ['wP']`);
  9. `.board i.d.hl` written with the `background` shorthand → the stylesheet test;
  10. `--hl-light` equal to `--light` → the stylesheet test;
  11. a flipped board with files not reversed → the black-below and every-board tests ("the labels
      are neither orientation");
  12. a wrong piece class on e1 → the board tests (`e1: ['d', 'bK']`).
- **Visual, headless Chromium 1243**, the fixture site built from `main` (a `git archive` of
  `9fe7e1d`) and from this head, articles `2020-06-01-9705c13f05` (infobox, and a flipped moment)
  and `2021-12-24-9137b96576`, at 390 px DPR 1, 1280 px DPR 1, 412 px DPR 2.625 and 390 px DPR 3,
  light and dark (`--blink-settings=preferredColorScheme=0`; the page background read back as
  `#101418`). For each shot two more were taken with an injected style painting the cells' own
  boxes as column stripes and as row stripes, which gives each cell's device-pixel box. Then a
  scanline near the top of every rank (above the pieces) and one down every file, classifying
  pixels as light, dark, highlighted light, highlighted dark:

  | | square-colour edges not on a cell-box edge (or blurred over ≥ 1 px) | highlighted cells with another colour inside |
  |---|---|---|
  | `main` | 16 to 112 per page, in every configuration (up to 2 px off) | 2 of 4 on `2020-06-01` at 390 px DPR 1 and DPR 3 |
  | this head | 0 in every configuration (one hit at 390 px DPR 1 light was a rank-label glyph pixel, not a square edge) | 0 |

  On `main` at 390 px DPR 1 the infobox board (338 px inside, 42.25 px squares) has an
  anti-aliased pixel at nearly every square edge and the highlighted f7 cell holds 82 highlight
  pixels on the scanline against 85 on the head. A side-by-side of the infobox board, both
  schemes, shows the same position, colours, labels and highlight, with the queen drawn over the
  highlighted f7 on both.

## Findings

1. **non-blocking** — The test's square colour is not independent of the code under test.
   `tests/test_boards.py:58` computes the expected colour with
   `chess.BB_LIGHT_SQUARES & chess.BB_SQUARES[square]`, the same expression as
   `pgn_postmortem/site.py:635`, while the module docstring, the commit message and the new
   `CLAUDE.md` text say "by file and rank parity". The hand-worked corners of the single-board test
   (`tests/test_boards.py:88-92`) and the known correctness of python-chess's constant make a wrong
   colour very unlikely to slip through, so this is wording rather than a gap; computing
   `(file + rank) % 2 == 1` in the test would make the claim literal.
2. **non-blocking** — The stylesheet test pins more than the defect needs.
   `tests/test_boards.py:157` (`assert "gradient(" not in css`) forbids any gradient anywhere in
   the site's stylesheet, not only on boards; a later, unrelated gradient (say an evaluation bar)
   would fail with a message about squares. `:165-166` pin the exact selectors and variable names,
   which the golden `style.css` already pins byte for byte. The invariants that matter — no
   `background*` on a `.board` rule, colour per cell, no `background`/`background-image` on a cell
   rule — are checked separately at `:158-163`. Narrowing the gradient check to the `.board` and
   `.board i…` rules would keep the defect caught (mutations 1 and 2 above are caught by `:161` as
   well) without the over-reach. Judgement: acceptable as it is; the owner may prefer the narrower
   form.
3. **non-blocking** — The highlight colours are checked to be solid and different from the
   squares (`tests/test_boards.py:170-173`) but not to be the blend they claim to be (the CSS
   comment at `pgn_postmortem/site.py:1359-1361`). A wrong hex value would pass this test and be
   caught only by the golden files, which are regenerated in the same commit as any change. I
   verified the four values by hand and in pixels (above); no action needed unless the owner wants
   the comment's arithmetic asserted.
4. **non-blocking** — Where the defect is recorded. `PRINCIPLES.md` asks that a defect found after
   a change landed be "recorded and fixed". This change records it in the commit message, the test
   module's docstring (`tests/test_boards.py:1-11`), the `CLAUDE.md` covers cell and the PR, and
   deliberately adds no row to `ROADMAP.md` or `PLAN.md` (the PR's "Left out"). The precedent in
   `ROADMAP.md` ("The same change fixes a defect found in the owner's book: … "inaccuracys"") put a
   defect in a roadmap block, but that one rode inside a feature's change. Recording it in this
   review file, once committed, satisfies the rule as written; the owner decides whether a line in
   `ROADMAP.md` or `PLAN.md` is wanted.
5. **non-blocking** — The PR's done-when list leaves "The owner's phone check" unchecked. It is not
   a gate and not required by the defect path, but it is the only check on the device where the
   owner saw the defect; the owner records it before merging, as the PR says.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged on 2026-09-25 as `3adc85a` (pull request #24), on the owner's go ("Check on the live book after merge"). The clean round, 01, covers `c96537d`. CI on the merge commit passed on Python 3.11 and 3.13: https://github.com/diegoami/pgn-postmortem/actions/runs/36190901762.

**The defect** (recorded here, as the defect path asks): the owner reported "The final position looks skewed". Board diagrams drew square colours with one board-level background pattern (from F-1.2), while pieces and the highlight were drawn in the grid cells. At fractional square sizes the two rounded apart: squares alternated between 37 and 38 px, and the highlight was 1–2 px off its square.

- **The fix:** each cell draws its own square's colour, and the board-level pattern is gone. The highlight is pre-blended solid colours, within 1 per channel of the old look.
- **The assertion that would have caught it:** `tests/test_boards.py` fails on the pre-fix code, for the right reasons. It checks every cell of every fixture board, in both orientations, for colour, piece and highlight, and that no board-level pattern remains.
- **Visual check in headless Chromium:** colour edges off the cell boxes went from 1,049 to 0, and highlight edges off their square from 24 of 168 to 0. The reviewer reproduced this.
- **The gates:** `ruff check .` is clean, `pytest -q` gives 209 passed, and the script gate gives 32 passed. Both golden sets are regenerated; with the `l`/`d` classes stripped, the articles are identical to main's.
- **The owner's phone check** is deferred to the live book by the owner's choice.

Left as non-blocking: the review's findings 1–4:
- the test's "parity" wording;
- the stylesheet test rejecting gradients site-wide;
- the highlight blend asserted only by the golden files;
- no roadmap line for the defect, which this record covers.

— Implementer, Claude Opus 5.5 (claude-opus-5-5)

**Owner's phone check (addendum, 2026-09-25):** on the live book, after the fix was published, the owner reported: "everythink ok". Transcribed by the orchestrator.
