# Review 022: shape F-10 (pull request #22), round 02

- **Revision covered:** `ef24e1836018fe0e254e5fd7143020e4e41958b6` (branch `shape-f10`), on top of
  `origin/main` at `d1b593e5d52e8c4317d3dbfb72417007e5de1d55` (the merge base).
- **Target proof:** after `git fetch origin`, `git rev-parse origin/shape-f10` gives
  `ef24e1836018fe0e254e5fd7143020e4e41958b6`, which equals `headRefOid` from
  `gh pr view 22 --json headRefOid,files`. The branch has three commits: `ef3dde9` (the shaping),
  `5d9fd32` (round 01's record) and `ef24e18` (the answer to round 01).
- **Files checked:** `PLAN.md`, `ROADMAP.md` and `reviews/022-shape-f10-impl-01.md`. The pull
  request's file list (`gh pr view 22 --json files`) equals
  `git diff --name-only $(git merge-base origin/main origin/shape-f10)..origin/shape-f10`. The files
  were read with `git show origin/shape-f10:<path>`. The changes since round 01 were read with
  `git diff 5d9fd32 ef24e18`, which touches only F-10's block in `ROADMAP.md`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that did
  not see the shaping. It also wrote round 01.
- **Mode:** Claude Code.
- **Read against:** the same rules as round 01. From `origin/shape-f10`, also:
  `pgn_postmortem/site.py`, `pgn_postmortem/collection.py`, `tests/test_site.py`,
  `tests/test_quiz.py` and `README.md`. python-chess's SAN output was checked in the local `.venv`.

## The record of round 01

`reviews/022-shape-f10-impl-01.md` at `ef24e18` is byte-identical to the file the reviewer wrote
(`cmp` reports no difference).

## Round-01 findings

1. **Blocking, now resolved.** F-10's block now says:
   - **How the check is narrowed** (`ROADMAP.md:586-597`). `check_links` accepts an absolute link
     only if it meets both conditions:
     - it is a `pgn/` link in an article's infobox, or a non-`pgn/` `analysis/` link inside an answer
       `<details>`;
     - it carries `target="_blank"` and `rel="noopener noreferrer"`.

     Every other `href` and `src` must still be relative and resolve.
   - **That the narrowing fails other links** (done-when 4, `ROADMAP.md:610-615`). The narrowed check
     still fails an absolute link anywhere else, or of any other form, and that failure is shown
     first.
   - **Which files to update:** the covers cell in `CLAUDE.md`, `README.md` and `site.py`'s
     docstring.

   The rule can be tested as written:
   - The tests' `Element` keeps `parent` (`tests/test_site.py:77-80`), so "inside an article's
     infobox" and "inside an answer `<details>`" are checkable.
   - "Not `pgn/`" can't be confused with a FEN, because a FEN's first rank can't start with `pgn`
     (`g` is not a FEN letter).

   A grep for "relative", "network", "loads nothing" and "offline" in `CLAUDE.md`, `README.md`,
   `pgn_postmortem/`, `tests/`, `docs/` and `.claude/skills/` finds these claims:
   - `README.md:194-195`, `site.py:15-17` and the covers cell in `CLAUDE.md:98`. All three are named
     in the block.
   - `check_links`'s own docstring (`tests/test_site.py:153`) and a comment at
     `tests/test_quiz.py:195`. Both change along with `check_links`.
   - `docs/book-plan.md:18` and `:109` ("offline", "works offline"). These stay true: the site still
     works offline, and only the links the reader taps need the network.

   The rest are the history script's "loads nothing" (unchanged) and generated golden pages. See
   finding 6 for one inaccuracy in the new text.
2. **Blocking, now resolved.** Done-when 2 (`ROADMAP.md:603-606`) now requires a new hand-written
   fixture with a set-up game that has at least one critical moment. The test must assert that at
   least one position link in a set-up game was checked, so it can no longer pass without testing
   anything.
3. **Resolved.** The game URL now leaves out `+` and `#` (`ROADMAP.md:565-568`). Its path is decoded
   with `unquote`, and it has no query and no fragment (done-when 1). A fixture game with checks and a
   mate covers the signs, and the owner's check uses a game with checks. The rule is sound for SAN:
   - python-chess writes `+` and `#` only as suffixes. For example, `a8=Q+`, `bxa8=Q+`, `Ra8#`, `O-O`
     and `O-O-O` were checked in `.venv`.
   - So removing a trailing `+` or `#` keeps promotions (`=Q`) and castling intact. Nothing else in
     SAN uses those characters.
   - Round 01 saw lichess carry `a8%3DQ` through as `a8=Q`.
4. **Resolved.** `ROADMAP.md:569-571` now says lichess accepts a `[FEN …]` tag in the path, and that
   it is not verified whether its board then starts from that position.
5. **Resolved in part.** Games with no moves get no game link (`ROADMAP.md:572`, done-when 2). See
   finding 7.

## New findings

6. **non-blocking**: "The escape test's list of allowed attributes gains `target` and `rel`, for
   those links only" (`ROADMAP.md:593-594`) doesn't match the test.
   - `rel` is already in the list (`tests/test_site.py:228`). It is used by
     `<link rel="stylesheet">` and by the article's `rel="prev"`/`rel="next"` links
     (`site.py:1031-1033`, `site.py:754`).
   - The list is one set for the whole page. It can't express "for those links only".
   - Suggested wording: "the list gains `target`; the narrowed `check_links` asserts that `target`
     appears only on the lichess links."

7. **non-blocking**: the reader drops a game with no moves, so the test needs to build one directly.
   - `Collection.read` skips a game with no moves and counts it as "without moves"
     (`pgn_postmortem/collection.py:334-336`). So a fixture file can't bring such a game to the
     builder through `Collection.read` or the `site` command.
   - Only a `CollectedGame` passed directly to `build_site` reaches it, and no current fixture has a
     game with no moves.
   - The block should say the test builds from a directly made `CollectedGame` with no moves.
     Otherwise that part of done-when 2 has nothing to run on, the same gap as finding 2.

8. **non-blocking**: done-when 1 doesn't say whether the game URL includes move numbers.
   - It says the path "is exactly the game's mainline moves in SAN without `+`/`#`, in order". That
     doesn't say whether the path is movetext with numbers (`1.e4 e5 2.Nf3`, the form checked against
     lichess in round 01) or bare SAN (`e4 e5 Nf3`).
   - Fix the form in the block, or say the test compares the SAN tokens after dropping the move
     numbers. That way a correct implementation doesn't fail on a formatting choice the block left
     open.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged on 2026-09-25 as `df721b6` (pull request #22), on the owner's go ("merge it and start implementing F-10", given while round 01 was running and acted on only after the clean round 02, covering `ef24e18`). CI on the merge commit: success https://github.com/diegoami/pgn-postmortem/actions/runs/36162834793.

- **F-10's block has every field of the block format,** with the owner decisions each carrying a default and reason, and the proposed items marked (including the narrowed link check).
- **Statuses and the iteration table are consistent:** F-9 is landed and F-10 is iteration 7.
- **Only `ROADMAP.md` and `PLAN.md` changed,** plus the review records.

Left for F-10's implementation (put in the implementer's brief):
- **Round-02 finding 6:** add only `target` to the escape test's allowed attributes (`rel` is already allowed), and have `check_links` assert `target` appears only on the lichess links.
- **Finding 7:** `Collection.read` skips games without moves, so the "no game link without moves" test builds such a game directly for `build_site`.
- **Finding 8:** fix one form for the game URL (bare SAN or with move numbers) and compare accordingly.

— Implementer, Claude Opus 5.5 (claude-opus-5-5)
