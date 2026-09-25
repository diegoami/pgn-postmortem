# Review 015 — F-6: moves that changed the expected result (implementation, round 02)

- **Revision covered:** `dbb228b9cc9e90c2ff3556a0c3ebce072b134f19` (pull request #15, branch
  `iteration-4-outcome-swings`). After `git fetch origin` and a checkout of
  `origin/iteration-4-outcome-swings`, `git rev-parse HEAD` gives this sha. It equals the PR's
  `headRefOid`.
- **Commits since round 01** (`b96c5f4`):
  - `d595ae0`, which records round 01;
  - `987079c`, which changes the default bands to 40/60 and reworks the tests and fixtures;
  - `4e55a97`, which updates the README and `CLAUDE.md`;
  - `dbb228b`, which updates `ROADMAP.md`.
- **Files checked (17):** these come from `gh pr view 15 --json files`. The list is identical to
  `git diff --name-only $(git merge-base origin/main HEAD)..HEAD`, where the merge base is
  `21530f9`.
  - `CLAUDE.md`
  - `README.md`
  - `ROADMAP.md`
  - `pgn_postmortem/site.py`
  - `reviews/015-f6-outcome-swings-impl-01.md`
  - `tests/fixtures/site/swings/README.md`
  - `tests/fixtures/site/swings/critical-swing.pgn`
  - `tests/fixtures/site/swings/default-band.pgn`
  - `tests/fixtures/site/swings/edges.pgn`
  - `tests/fixtures/site/swings/first-choice.pgn`
  - `tests/fixtures/site/swings/not-swings.pgn`
  - `tests/fixtures/site/swings/two-swings.pgn`
  - `tests/golden/site/games/2020-06-01-9705c13f05.html`
  - `tests/golden/site/games/2021-09-10-a9c90416b2.html`
  - `tests/golden/site/games/2021-12-24-9137b96576.html`
  - `tests/golden/site/games/undated-5ce208cdcb.html`
  - `tests/test_outcome_swings.py`
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. It is
  the same reviewer session as round 01, which `PRINCIPLES.md` allows for a re-review. It had not
  seen the implementation session.
- **Mode:** Claude Code.
- **Rules applied:** the same as round 01, plus the owner's changed decision on the level band
  (40–60%, 2026-09-25) as recorded in F-6's block.

## Gates

All gates pass at this revision.

- **Local run:** a venv in the reviewer's worktree.
  - `.venv/bin/python -m ruff check .` gives "All checks passed!".
  - `.venv/bin/python -m pytest -q` gives 134 passed.
- **CI:** `gh pr checks 15` shows `test (3.11)`, `test (3.13)` and GitGuardian passing. Run
  36124570749 has `headSha` `dbb228b…` and the conclusion `success`.

## What was checked

### Round 01's record

The committed `reviews/015-f6-outcome-swings-impl-01.md` is byte-identical to the file the reviewer
wrote (`cmp` reports no difference).

### The default is 40/60

- **Code:** `pgn_postmortem/site.py:123` has `OUTCOME_BANDS = (40.0, 60.0)`. The module docstring
  and the `build_site` docstring say 60 and 40.
- **Docs:**
  - `README.md` says "60% or more", "40% or less" and `outcome_bands=(40, 60)`.
  - The tests row of the `CLAUDE.md` gates table adds "the default bands at 40/60, not 35/65".
  - F-6's Scope says 60% and 40%.
  - The fixtures' README says 40/60.
- **No stale references:** a grep for 35/65, 35–65, 65% and 35% outside the review records finds
  only the intended ones:
  - the recorded first choice in `ROADMAP.md:296`;
  - the code comment on the change;
  - the invalid and valid pairs in the tests;
  - the not-at-35/65 assertion.

### Fixtures and items under the new default

- **Fixture values:** I recomputed every eval with the library's `win_percent`. Each value matches
  the fixtures' README and the tests' assertions:

  | eval | White's chances |
  |---|---|
  | 0.20 | 51.84 |
  | 1.50 | 63.47 |
  | 0.80 | 57.31 |
  | −1.50 | 36.53 |
  | −3.00 | 24.89 |
  | −1.10 | 40.010 |
  | 1.10 | 59.990 |
  | −1.11 | 39.922 |
  | 1.11 | 60.078 |
  | −0.10 | 49.08 |

  | move | cost (points) |
  |---|---|
  | 7. h3 | −11.63 |
  | 8. Nbd2 | 6.16 |
  | 8... Ba7 | −20.78 |
  | 9. Re1 | 11.65 |
  | `edges.pgn` 7. Re1 | 11.83 |
  | `edges.pgn` 8... Nh5 | 10.91 |
  | `default-band.pgn` 7. Re1 | 11.92 |
  | `default-band.pgn` 8... Nh5 | 11.00 |

- **Unchanged fixtures:** `two-swings.pgn`, `first-choice.pgn` and `critical-swing.pgn` did not
  change. Their moves still fall in the claimed bands at 40/60: 33.2% is Black winning, 46.3% is
  level and 28.5% is Black winning.
- **Items 1–9:** all are still asserted, and `facts()` still checks every condition except the one
  under test from the raw PGN.
  - **Item 4:** 9. Re1 goes from 36.5% to 24.9%, which stays inside Black winning. It costs 11.6
    points, has its own better line 9. Bb3, and is not a moment. Its note has no change words.
  - **Item 7:**
    - `edges.pgn` lands just inside the default edges (40.01% and 59.99%), and `default-band.pgn`
      lands just outside them (39.92% and 60.08%).
    - The exact-edge tests move one edge onto `win_percent(±110)` and keep the other at its
      default.
    - The changed-pair test uses 41/59 (two more moments) and 30/70 (two fewer).
    - The 12 invalid pairs and the 3 valid pairs are unchanged.
  - **Item 8:** the report now counts 5: 2 + 0 + 0 + 1 + 0 + 2.
- **The floor test** still holds at 40/60.
  - With `Thresholds(5, 20, 30)`, 8. Nbd2 (6.2 points, White winning to level) is a swing.
  - With `Thresholds(15, 20, 30)`, only 7. Re1 remains in `two-swings.pgn`.

### Golden files

- The golden files do not change between `b96c5f4` and this head.
- I regenerated the site with the documented command into a scratch directory. `diff -r` against
  `tests/golden/site/` shows no difference, and the build reported 4 critical moments.
- `EXPECTED_MOMENTS` in `tests/test_site.py` is still untouched.

### `ROADMAP.md`

- **The original request** is verbatim: neither the F-6 row nor the block's "Original request" line
  is in the diff.
- **The change is recorded as the owner's:** "Owner decision (2026-09-25): the level band is
  40–60%" (`ROADMAP.md:295`). It keeps:
  - the recommended default (35–65%) and its reason;
  - the owner's first choice;
  - the change on the same day after the preview of this branch's book, with its reason (15. Nxc5,
    47% → 37%);
  - why 45–55% was not chosen (it loses 37… Rg2+).
- **Everything that follows from the new band** was updated:
  - the counts, including 288 candidates;
  - the item-7 wording ("can't hit 60.000%");
  - the owner-verdict check, which now names four moves.

### The new counts

I re-counted read-only on the owner's analyzed book games (148 files), with the library's
`review_moves`, `has_better_move` and `LICHESS_THRESHOLDS`. I read the files in two ways, directly
with `chess.pgn` and through `Collection.read(keep_analysis=True)`, and both give the same numbers.

- **At the default 40/60:**
  - 148 games, all analyzed;
  - 390 moves costing at least 20 points;
  - 285 new questions (swings under 20 points) in 109 games;
  - 675 critical moments in all;
  - 318 swings that are already 20-point moments;
  - 3 exclusions: 45… Qa6 and 47… Qa6 in `2005-09-24-3bd9df323c`, and 18. Qxd4 in
    `2008-01-05-ec4df50311`. They come out of 288 candidates under 20 points (285 + 3).

  Every number matches `ROADMAP.md`.
- **At 35/65:** the same script gives the shaping's numbers: 236 new questions in 96 games, 362
  swings that are already moments and the same 3 exclusions. So the script agrees with the earlier
  record.
- **The example game** (`2008-01-04-4e5d4e182f`) has exactly four critical moments. The
  percentages are the chances of the side that moved.

  | move | chances | expected outcome | swing |
  |---|---|---|---|
  | 15. Nxc5 | 46.9 → 36.8 | level → losing | yes |
  | 31… Qa2 | 96.6 → 68.5 | winning → winning | no, a 20-point moment |
  | 37… Rg2+ | 75.0 → 58.7 | winning → level | yes |
  | 40. Ra4 | 48.8 → 31.8 | level → losing | yes |

### Fail-first, reproduced

- **Method:** a script applied each break to `site.py` and cleared every `__pycache__` outside
  `.venv`. It then ran `.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/` and restored
  the file.
- **After the run:** `git status` was clean.

| break | went red on |
|---|---|
| the default put back to 35/65 | `test_the_default_bands_are_40_and_60`, both exact-edge tests, items 2, 3 and 4, report, floor (8 in all) |
| strict edges (`>`/`<`) | both exact-edge tests |
| direction and the cost's sign dropped together | items 2, 3, 4, 5, the changed pair, report, floor (and errors building the site) |
| the band condition dropped entirely | 18 failed, 3 errors, including items 2, 3, 4, 5 and 7, the non-swing 20-point note, and the CLI |
| the floor fixed at 10 | `test_the_floor_follows_the_inaccuracy_threshold` |
| no floor (`loss > 0`) | items 2–5, the changed pair, report, floor |
| the first choice read as "any line stored" | item 5, report |
| no up-front band check in `build_site` | all 12 invalid-pair cases |
| the `outcome_bands` parameter ignored | the default-band test, both exact-edge tests, the changed pair |

## Findings

Round 01's findings stand as follows:

- Finding 1 is answered by the comment at `site.py:255–256`.
- The owner moved findings 2 and 3 to F-1.3, so this round does not re-raise them.
- Finding 4 is resolved: the counts are recorded and reproduce exactly, as shown above.

1. **non-blocking**: the default is pinned only to within about ±0.08 points.
   - A default of `(39.95, 60.05)` in place of `(40.0, 60.0)` leaves all 134 tests green, because
     it still falls between the fixtures' 39.92/40.01 and 59.99/60.08.
   - A hand-set `[%eval]` cannot do better, since it has whole centipawns.
   - **Suggestion (optional):** one exact assertion in `test_the_default_bands_are_40_and_60` would
     pin the default fully, for example on
     `inspect.signature(build_site).parameters["outcome_bands"].default == (40, 60)`.

2. **non-blocking**: item 2's fixture now uses a line that no analysis would store.
   - In `not-swings.pgn`, the line `( 7. b4 Bb6 8. a4 )` sits before 7. h3. But 6... O-O costs
     nothing, so no analysis would store a refutation there. 7. h3 gains 11.6 points, so it is never
     graded and never gets a line of its own at any threshold.
   - Round 01's version used a realistic shape: 6... Bg4's refutation.
   - The test is still valid, because condition 3 holds and only the direction keeps the move out.
     But `tests/fixtures/site/swings/README.md:33` lists "7. b4" without saying it was set by hand
     for this purpose, while the next row does explain its 8. a4 line.
   - This belongs with round-01 finding 3, which is left for F-1.3.

3. **non-blocking**: a stated reason is inaccurate.
   - Where it appears: the comment at `tests/test_outcome_swings.py:170` and the fixtures' README
     row, which say "the level band is 20 points wide, so the fixture's 10–20-point loss is inside
     Black winning". The PR body says the same.
   - Why it is inaccurate: a 10–20-point loss can stay inside a 20-point level band. From the
     fixtures' own 51.8%, a move to 41% is a 10.8-point level-to-level loss.
   - Item 4 only asks for a loss "inside one band", and the Black-winning case satisfies it, so the
     test is fine.
   - Suggested wording: "item 4's loss is placed inside Black winning".

Nothing else is new. The changes are limited to the band default, the fixtures and tests that
follow from it, the docs and the owner-decision record. `scripts/`, `examples/` and `analysis.py`
are untouched.

The owner's verdict on the rebuilt book is still pending, and it gates the merge. It should now show
four questions: 15. Nxc5, 31… Qa2, 37… Rg2+ and 40. Ra4, which is what I got above.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
