# Review 019 — F-10, the full-game lichess link: implementation, round 01

- **Revision covered:** `879550c393f53fc965715e9541e16604d93c0070`, the head of pull request #19
  (branch `f10-add-game-link`). After `git fetch origin`, `git rev-parse origin/f10-add-game-link`
  equals `gh pr view 19 --json headRefOid`. The branch has one commit on top of `origin/main`
  (`879550c Add the owner's full-game lichess link to F-10`).
- **Files checked (1):** `ROADMAP.md`, from `gh pr view 19 --json files`. It is identical to
  `git diff --name-only 9611197..origin/f10-add-game-link`, where `9611197` is
  `git merge-base origin/main origin/f10-add-game-link` and equals `origin/main`. Read with
  `git show origin/f10-add-game-link:ROADMAP.md` and `git diff --word-diff origin/main...origin/f10-add-game-link`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that has
  not seen the implementation.
- **Mode:** Claude Code.

## What was checked

- **Only F-10's row changed.** The diff is one line, `ROADMAP.md:22`; the word diff shows only an
  addition at the end of the notes cell. No other row, section or file changes.
- **The row's shape.** Splitting line 22 on `|` gives five cells; no `|` appears inside a cell.
  The status cell is still `requested` and the iteration cell is still empty.
- **The owner's new wording** is quoted in full, trailing comma included: "Another feature to
  add is having a link to open the full PGN game on lichess,". It is added in the notes as "Also
  in the owner's words (2026-09-25): …", the same pattern as F-1 and F-3, so the request column
  keeps the original F-10 wording unchanged, as *How to request* requires.
- **The earlier F-10 content is intact:** the original request, "Asked by the owner on
  2026-09-25 …", "Not shaped yet.", the ordering decision (F-8 to F-11 before F-1.3) and the
  earlier owner decision on the lichess analysis board, with its default, reason and alternative,
  are byte-identical to `origin/main`.
- **The new decision** follows `PRINCIPLES.md`, *Owner decisions*: it carries the owner-decision
  mark in the same form as the row's earlier decision ("**Owner decision (2026-09-25): that
  request is part of F-10**"), is "recommended as the default", gives the reason ("both are plain
  links to lichess (the position's analysis board and the whole game)") and names the alternative
  not chosen ("a separate request, was not chosen").
- **No pre-shaping.** The addition records only the wording and the decision. "shaped and built
  as one iteration" is the consequence of the decision under the roadmap's own rule ("an accepted
  request is one iteration"), not a shaping choice: it says nothing about the URL format, where
  the link goes on the page, the EPUB, or how the PGN is passed to lichess.
- Whether the owner said and decided this cannot be checked from the repository; the owner's
  merge is that check.

## Findings

None.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged by the owner on 2026-09-25 as `4621492` (pull request #19); the clean round, 01, covers `879550c`. CI on the merge commit: success https://github.com/diegoami/pgn-postmortem/actions/runs/36148621351.

- **The owner's wording is in F-10's row,** quoted verbatim, with the decision that it's part of F-10, its default and reason, and the alternative not chosen.
- **Only `ROADMAP.md` changed,** plus this record.

— Implementer, Claude Opus 5.5 (claude-opus-5-5)
