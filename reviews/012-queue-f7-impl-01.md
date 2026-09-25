# Review 012 — queue F-7, implementation, round 01

- **Revision covered:** `3a48e4bd13dad76c4bce2ffcd0f4407e704831c2` (branch `queue-f7`, pull request #12).
  `git rev-parse origin/queue-f7` after `git fetch origin` equals the pull request's `headRefOid`.
- **Files checked:** `ROADMAP.md` (one line added). Obtained from `gh pr view 12 --json files` and
  confirmed equal to `git diff --name-only $(git merge-base origin/main origin/queue-f7)..origin/queue-f7`;
  the merge base is `origin/main` (`d1fb5d8`), and the branch has one commit.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that had not
  seen the change being written.
- **Mode:** Claude Code.

## What was checked

- **The queue's rules** (`ROADMAP.md`, *The queue*, *How to request*, *The agent's job*): the F-7 row
  has five cells (id, request, status, iteration, notes), and none of its text contains a `|`. The
  request is quoted ("queue the library feature"), its status is `requested`, the iteration cell is
  empty, no *Accepted requests* block was added, and the notes say "Not shaped yet". This is the same
  pattern as F-4: a short owner answer, with the question it answers quoted in the notes. The owner
  is the only check that the words are the owner's, and that check is the merge.
- **The behaviour the row describes** (`pgn_postmortem/collection.py` on `main`): `Collection.write`
  skips every game whose id is in `analyzed_ids(out_dir)`, meaning a file with the
  `PostmortemAnalysis` marker and the same `PostmortemId`. Its docstring says: "A game already
  analyzed into `out_dir` is not written". `analyze_games` (`pgn_postmortem/analysis.py`) skips the
  same ids, so an analyzed file is never rewritten, and its headers aren't either. The claim holds.
- **Game identity:** `game_id` hashes the normalized start position, `Result`, `Date` and the UCI
  mainline. The players' names and all other headers are not in the hash. The row's "moves, result,
  date, start position" is correct, and so is the statement that a corrected `Date` or `Result`
  would change a game's id.
- **The cited commits:**
  - DA_chessgames `9e7c939` changes `otb/allotb.pgn`. Its diff replaces 23 `Site` lines and 2 `Event`
    lines, and nothing else changes. `691eba6` sets `Site "Worms"` on the 7 Nibelungen Open IV games.
  - chessgamescollection `a4a7d09` edits the same header lines in `book/analyzed/` (23 files) and
    `book/games/`, and rebuilds `book/site/`. `9be2978` does the same for the 7 Worms games. Both
    commit messages say the analyzed files' headers were updated by hand, with the analysis left
    untouched.
- **Nothing else changed:** one file changed, with one insertion and no deletions.

## Findings

1. **non-blocking.** The row says the stale headers come from reading ("Reading again leaves an
   analyzed game's file alone"). In the owner's workspace, a different mechanism kept them.
   - `book/games/` and `book/analyzed/` are separate directories (chessgamescollection `README.md`,
     *book/*). Re-reading did refresh `book/games/`: `a4a7d09` says "the games re-read".
   - `analyze_games` then skipped the games already analyzed.
   - The site is read with `keep_analysis=True`, and `Collection.read` then prefers the analyzed copy
     over the stripped one ("the analyzed copy is the one kept"). The book therefore showed the stale
     headers, even though the stripped copies were corrected.

   The row's sentence is true of `Collection.write` into an analysis directory, so it is not wrong.
   But shaping should know that the fix may belong in the analysis step, or in how the site merges
   the two copies, not only in `read`/`write`. No change to the row is needed now; this is a note for
   whoever shapes F-7.
2. **non-blocking.** The parenthesis "23 'Saxonia Systems AG' placeholder Sites and 2 Events
   replaced" is slightly compressed. Only one of the 2 `Event` headers was the placeholder: the
   other was `"?"`, set to "Nibelungen Open IV" in `9e7c939`. The row cites `691eba6` but doesn't
   say what it did: it replaced 7 `Site "?"` with "Worms", values that `9e7c939` itself had written.
   Evidence: `git show 9e7c939 | grep '^-\[Event'` gives `[Event "?"]` and
   `[Event "Saxonia Systems AG"]`. The row's facts are otherwise accurate, and the wording is
   optional to change.
3. **non-blocking.** "Header changes don't change a game's identity (moves, result, date, start
   position)": the start position also comes from a header, `FEN`. A corrected `FEN`, though
   unlikely in practice, would change the id just as `Date` and `Result` would (`game_id`:
   `start = game.board().fen()`). This is worth noting at shaping, alongside the `Date`/`Result`
   caveat the row already records.

No blocking findings. The one-line change matches its description, follows the queue's rules, and
its checkable claims hold.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged by the owner on 2026-09-25 as `c4f6afc` (pull request #12); the clean round, 01, covers `3a48e4b`. CI on the merge commit passed: https://github.com/diegoami/pgn-postmortem/actions/runs/36114811733.

- **F-7 is queued** with the owner's verbatim wording and status `requested`, and is not shaped.
- **Only `ROADMAP.md` changed,** plus this record.

Left for F-7's shaping, recorded here so it isn't lost:
- **Finding 1:** the stale headers come from analysis skipping already-analyzed games and from the site preferring the analyzed copy, not from reading, which does refresh the plain copies. The fix may belong there.
- **Finding 2:** of the 2 Events replaced, one was the placeholder and the other "?"; `691eba6` set Site "Worms" on 7 games.
- **Finding 3:** a corrected `FEN` changes a game's identity too.

— Implementer, Claude Opus 5.5 (claude-opus-5-5)
