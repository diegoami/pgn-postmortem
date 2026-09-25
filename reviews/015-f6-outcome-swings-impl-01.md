# Review 015 — F-6: moves that changed the expected result (implementation, round 01)

- **Revision covered:** `b96c5f475b1e71db4cc49bf04267f0974a4916c3` (pull request #15, branch
  `iteration-4-outcome-swings`). After `git fetch origin` and a checkout of
  `origin/iteration-4-outcome-swings`, `git rev-parse HEAD` gives this sha. It equals the PR's
  `headRefOid` (`gh pr view 15 --json headRefOid,files`).
- **Files checked (14):** these come from `gh pr view 15 --json files`. The list is identical to
  `git diff --name-only $(git merge-base origin/main HEAD)..HEAD`, where the merge base is
  `21530f9`.
  - `CLAUDE.md`
  - `README.md`
  - `pgn_postmortem/site.py`
  - `tests/fixtures/site/swings/README.md`
  - `tests/fixtures/site/swings/critical-swing.pgn`
  - `tests/fixtures/site/swings/edges.pgn`
  - `tests/fixtures/site/swings/first-choice.pgn`
  - `tests/fixtures/site/swings/not-swings.pgn`
  - `tests/fixtures/site/swings/two-swings.pgn`
  - `tests/golden/site/games/2020-06-01-9705c13f05.html`
  - `tests/golden/site/games/2021-09-10-a9c90416b2.html`
  - `tests/golden/site/games/2021-12-24-9137b96576.html`
  - `tests/golden/site/games/undated-5ce208cdcb.html`
  - `tests/test_outcome_swings.py`
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. It had
  not seen the implementation session.
- **Mode:** Claude Code.
- **Rules applied:**
  - `PRINCIPLES.md`: the six gates disciplines and the verdict protocol;
  - `CLAUDE.md` and its project slot: the gates, the conventions, the decided items, and which paths
    are generated and which are canonical;
  - F-6's block in `ROADMAP.md`: its Scope, 9 done-when items, Out of scope and owner decisions;
  - the completion note of `reviews/014-shape-f6-impl-03.md`;
  - `PLAN.md` iteration 4;
  - `reviews/README.md`.

## Gates

All gates pass at this revision.

- **Local run:** a fresh venv in the reviewer's worktree (`pip install -r requirements-dev.txt`,
  `pip install -e .`, Stockfish present).
  - `.venv/bin/python -m ruff check .` gives "All checks passed!".
  - `.venv/bin/python -m pytest -q` gives 133 passed.
- **CI:** `gh pr checks 15` shows `test (3.11)` and `test (3.13)` passing, plus GitGuardian. Run
  36121768566 has `headSha` `b96c5f4…`, so CI ran on the revision under review.

## What was checked

### The rule (`pgn_postmortem/site.py`)

- **Expected outcome:** `expected_outcome` reads the bands from White's chances as computed. The
  edges are inclusive (`white >= upper`, `white <= lower`), and the result is turned to the mover's
  point of view.
- **Condition 1:** the outcome worsened for the mover (`OUTCOMES.index(after) < index(before)`).
- **Condition 2:** `loss >= thresholds.inaccuracy`. The floor follows the thresholds in use, and no
  new parameter was added.
- **Condition 3:** `has_better_move` requires at least one stored line at the position before the
  move, and none of them may start with the move played.
  - I checked this against `analysis.analyze_game`. It attaches the move's own better line off
    `node.parent`. It attaches the previous move's refutation off the previous node, which is the
    same position. Both therefore land in `node.parent.variations[1:]`.
  - The refutation-only shape is handled. python-chess adds a second child even when its move
    matches the mainline child's, so a refutation that starts with the move played shows up as a
    variation with that move. The check then excludes the move played.
  - "A line is stored" is not used as the test.
- **Unchanged decided items:** the 20-point line (`critical = loss >= thresholds.mistake or swing`)
  and the grading (`classify` in `analysis.py`, which is not in the diff) are unchanged.
  `EXPECTED_MOMENTS` in `tests/test_site.py` is unchanged too.
- **Moment count:** a move that is both a 20-point moment and a swing is one `MoveReview` with
  `critical=True`, so it is shown once. Everything that counts moments goes through
  `review.critical`: `Article.moments`, the infobox, the lead, the index and `SiteReport`.
- **Band validation:**
  - `check_outcome_bands` rejects non-numbers, bools, NaN, infinities and any pair outside
    `0 < lower < 50 < upper < 100`.
  - `build_site` calls it before anything is written, next to `check_presume_threshold`.
  - `review_moves`, and so `critical_moments`, also calls it.
- **Wording point from the shaping** (the completion note of review 014, round 03): the module
  docstring now separates two cases.
  - With the analysis's own thresholds, no stored line means the engine's first choice was the move
    played.
  - With a lower inaccuracy threshold, nothing is known about a better move.

  That resolves the note.

### Fixtures and tests

- **Fixture values:** I recomputed every eval in the fixtures' README with the library's own
  `win_percent`. Each value matches the README and the tests:

  | eval | White's chances |
  |---|---|
  | 0.20 | 51.84 |
  | −1.90 | 33.19 |
  | −0.40 | 46.32 |
  | 1.40 | 62.61 |
  | 3.00 | 75.11 |
  | 2.50 | 71.51 |
  | 1.50 | 63.47 |
  | −2.50 | 28.49 |
  | −1.50 | 36.53 |

  | move | cost (points) |
  |---|---|
  | 7. Re1 | 18.65 |
  | 8... Nh5 | 13.13 |
  | 6... Bg4 | 10.77 |
  | 7. h3 | −12.50 |
  | 8. Nbd2 | 8.05 |
  | 7. Re1 (critical-swing) | 23.36 |
  | 7. Re1 (edges) | 15.31 |
  | 8... Nh5 (edges) | 11.63 |

- **The `facts()` helper:** each test first uses `facts()` to confirm, from the raw PGN, that
  every condition except the one under test holds. So a green test is not a vacuous one.
- **Done-when coverage:** items 1–9 are each asserted as the PR describes. This includes:
  - the refutation-only shape (7... Ng4 in `first-choice.pgn`);
  - the exact-edge tests, which set a band to `win_percent(±150)`;
  - the 12 invalid pairs, rejected by `build_site([])` with nothing written, by a build of the
    fixtures, and by `critical_moments`;
  - the infobox "1, 2" with its anchors, the lead's new wording, "two questions" in the index, and
    the report count of 3.
- **The fixture directory:** `tests/fixtures/site/swings/` is a sibling of `synthetic/`, which the
  block allows. It is documented as hand-written.
  - The reason given is true: `tests/test_presumed_results.py:231` requires `synthetic/` to hold
    only F-5's games.
- **The fabricated 8. g4 line** in `not-swings.pgn` is documented, and it is needed. Without a line
  there, item 3's move would also fail condition 3, and the test could not isolate the floor.
- **Golden pages:** a word diff shows exactly the changes the PR claims.
  - All four analyzed pages change the lead's wording.
  - Three moments gain "that turned a level game into a losing one":
    - 3... Nf6 in `2020-06-01`;
    - 5. Nxf7 in `2021-12-24`;
    - 2... Ke7 in `undated`.

    Each has a stored better line with another first move.
  - 5... Bxd1 in `2021-09-10` goes from losing to losing, so it does not gain those words.
  - The index and the two games with no moment do not change.
- **Out of scope:** `scripts/`, `examples/`, `analysis.py` and `ROADMAP.md` are not in the diff.
  There is no command-line flag for the bands, which the block does not ask for. No scope creep.
- **The lead for a game with no moment** is unchanged. It still says "The engine found no critical
  moment: no single move cost either side 20 points". That remains true, because any 20-point loss
  is a moment, and the block only requires that the description stay true. I accept the PR's
  reasoning.

### Fail-first, reproduced

- **Method:** a script applied each break to `site.py` and cleared every `__pycache__` outside
  `.venv`. It then ran `.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/` and restored
  the file.
- **After the run:** `git status` was clean, and the full suite passed again (133).

| break | went red on |
|---|---|
| direction dropped **and** the cost's sign dropped (`!=`, `abs`) | `test_a_band_change_in_favour_of_the_side_that_moved_is_not_a_moment` (+6) |
| the floor fixed at 10 | `test_the_floor_follows_the_inaccuracy_threshold` |
| no floor (`loss > 0`) | items 2, 3, 4, 5, 7 (changed pair), the report and the floor tests |
| the first choice read as "any line stored" | `test_a_band_change_that_was_the_engines_first_choice_is_not_a_moment`, report |
| no line counted as a better move | the same two |
| a 20-point swing counted twice | `test_a_critical_moment_that_is_also_a_swing_is_shown_once`, report, golden, links, CLI |
| no up-front band check in `build_site` | all 12 invalid-pair cases |
| the halves not enforced (`0 < lower < upper < 100`) | `(50, 65)`, `(35, 50)` |
| NaN let through | `(nan, 65)`, `(35, nan)` |
| strict edges (`>`/`<`) | both exact-edge tests |
| the `outcome_bands` parameter ignored | both edge tests and the changed-pair test |
| outcomes read from White's side only | item 1, the upper edge, the changed pair, item 8, report, golden |
| no change words in notes and answers | items 1 and 6, golden |
| the lead's old wording | item 8, golden |
| the 20-point line dropped (`critical = swing`) | `test_site` expected moments, question and answer, golden, CLI, and the non-swing note |

## Findings

1. **non-blocking**: condition 1's direction has no test of its own, because no test can catch it
   alone.
   - The break `OUTCOMES.index(outcomes[1]) < OUTCOMES.index(outcomes[0])` → `!=` at
     `pgn_postmortem/site.py:255` leaves all 133 tests green.
   - This is not a gap in the tests. `loss = max(before - after, 0.0)` together with
     `loss >= thresholds.inaccuracy` already means the mover's chances fell. Because the bands are
     monotone in the chances, a fall can only keep the band or worsen it.
   - Item 2's test goes red only when the direction and the cost's sign are broken together. The
     PR's fail-first table says so honestly ("band compared without direction, cost without
     sign").
   - **Suggestion (optional):** a one-line comment at the swing condition saying the two conditions
     overlap, so that a future reader does not "simplify" the clamp in `loss`.

2. **non-blocking**: `README.md:208–213` has a wording and reflow slip.
   - Line 209 is 146 characters long ("…Its note says how the expected result changed, for example
     "an inaccuracy that turned a"), and line 213 ("Games that have not been analyzed, or whose
     only") is a short leftover. The rest of the section wraps at about 100 characters.
   - "an engine line that `analyze` stored at that position starts with another move" is looser
     than the rule in `has_better_move` (`site.py:219–224`), which requires that *no* stored line
     starts with the move played.
   - The two readings agree on real analysis output, because every line stored at one position
     comes from the same search. Still, "the engine lines … start with another move" would state
     the rule exactly.

3. **non-blocking**: `tests/fixtures/site/swings/README.md:34` says 8. g4 is stored "as an analysis
   with a lower inaccuracy threshold would store it". Such an analysis would also give 8. Nbd2 a
   `$6`, and `not-swings.pgn` has none.
   - This is harmless, because the site grades from the `[%eval]`s and not from the NAGs.
   - The README could say the line is set by hand to isolate the floor, or the fixture could carry
     the `$6`.

4. **non-blocking**: the Scope says the implementer re-checks the owner's counts: 236 new questions
   in 96 games, 3 exclusions and 362 swings that are already moments. The PR defers that to the
   owner's rebuild.
   - This is not a done-when item, and the owner's rebuild already comes before the merge, so
     deferring it is acceptable.
   - The rebuild's note on the PR should record those numbers next to the owner's verdict, so that
     the claim in the Scope is closed and does not simply lapse.

The owner's verdict on the rebuilt book, which should show 31… Qa2, 37… Rg2+ and 40. Ra4, is still
pending. The PR marks it unchecked, and it gates the merge. It is outside this review.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
