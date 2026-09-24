# Review 010 — Queue F-4 (name matching) and tidy the book-workspace wording, implementation round 01

- **Revision covered:** `9c3b9e5e4ec0a9f08f4190124b0994e86ef835d5` (branch `queue-name-matching`,
  pull request #10). It is one commit on top of `main` at `0e4c6de320c333bf43b05768f65fbf4e8dc7842b`.
- **Target proof:** after `git fetch -q origin`, `git rev-parse origin/queue-name-matching` gives
  `9c3b9e5…`, which equals `gh pr view 10 --json headRefOid`. The merge base with `origin/main` is
  `0e4c6de`, which is also the tip of `origin/main`.
- **Files checked:** `CLAUDE.md`, `ROADMAP.md`, `docs/book-plan.md`.
  - Obtained from `gh pr view 10 --json files` and from
    `git diff --name-only $(git merge-base origin/main origin/queue-name-matching)..origin/queue-name-matching`.
    The two lists are equal.
  - Read at the revision with `git show origin/queue-name-matching:<path>`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. I have
  not seen the implementation session.
- **Mode:** Claude Code.

## What I checked, and how

- **The diff, read in full** (`git diff origin/main..origin/queue-name-matching`): 10 lines added
  and 6 removed, across the three files above. No code, test, generated file or process rule
  changes.
- **The rules on `main`:** `PRINCIPLES.md` (*Owner decisions*, the target proof), the `CLAUDE.md`
  project slot, `ROADMAP.md` (*The queue*, *Statuses*, *How to request*, *The agent's job*),
  `reviews/README.md`, and the *Completion* section of
  `reviews/009-record-book-workspace-impl-01.md`.
- **F-4 against `ROADMAP.md`'s rules** (`ROADMAP.md:16`):
  - The request cell is a quote: "yes, queue the name matching improvement".
  - The status is `requested`, and the iteration cell is empty.
  - No `### F-4` block exists, so the request is not shaped. The notes say the proposal is "The
    implementer's proposal, to be shaped when picked up", so they do not present the proposal as
    the owner's or as agreed.
  - The notes keep the owner's second quote ("Why are there games that are not mine, they might be
    mislabeled") apart from the implementer's words. This follows the "in the owner's words"
    pattern of F-1 and F-3.
  - The order of F-4 and F-1.3 is left to the owner at shaping. The change does not decide it.
  - Nothing is parked or refused.
  - Whether the owner said these words cannot be checked from the repository. The owner's merge is
    that check. `ROADMAP.md:9`'s confirmation covers F-1 to F-3 only, which is correct as it
    stands.
- **The table still renders:** every row from the header to F-4 (`ROADMAP.md:11-16`) splits into 5
  cells (`awk -F'|'`). The F-4 notes contain no `|`.
- **F-4's factual claims:**
  - *How names match:* the code does what the row says, with one addition covered in finding 2.
    `pgn_postmortem/collection.py:275` builds the name set with `name.strip().casefold()`, and
    `:317-318` compares `White`/`Black` the same way. So a spelling that differs by more than case
    (or surrounding spaces) needs its own alias. The PR changes no code, so `main` and the PR
    agree here.
  - *The counts, from the source file:* I read `otb/allotb.pgn` in the owner's `DA_chessgames`
    checkout with python-chess, reading headers only. It holds 149 games, and the owner is on one
    side of every game. The owner's spellings, counted per game side, are:

    | spelling | games |
    |---|---|
    | `Diego Amicabile` | 94 |
    | `Amicabile, Diego` | 33 |
    | `Amicabile` | 12 |
    | `Amicabile Diego` | 7 |
    | `Diego , Amicabile` | 1 |
    | `amicabile, diego` | 1 |
    | `amicabile` | 1 |

  - *The counts, from the library:* I ran `Collection.read` in memory on that file, with no output
    directory and no analysis. The player was `Diego Amicabile`, with the aliases
    `Amicabile, Diego` and `Amicabile`. The report was `read=149, not_player=8, duplicates=1,
    kept=140`. The 8 left-out games are exactly the 7 `Amicabile Diego` games and the 1
    `Diego , Amicabile` game. That matches the row's "kept 140 and left out 8 of the owner's own,
    spelled `Amicabile Diego` and `Diego , Amicabile`". See finding 1 for the ninth game.
  - *The proposal:* ignoring spacing, commas and word order would match both missed spellings to
    `Diego Amicabile`, so it addresses the reported case. Its risks, such as merging two different
    players, are for shaping.
  - *Personal data:* the owner's name was already in committed files (`LICENSE:3`,
    `docs/book-plan.md:45`, `:75`, `:118`). The row names no local path. So the row adds no new kind
    of personal data, and it does not break the slot's *never read or echo* rule.
- **Review 009's finding 1** (the licence missing from the list of open decisions): the list at
  `CLAUDE.md:140-143` now reads "(the licence, whether the pipeline is a separate package, the
  Markdown pages, the selection weights)". This matches the four items that are still open in
  `docs/book-plan.md`:
  - whether the pipeline is a separate package (`:178-179`)
  - the licence (`:180-181`)
  - the Markdown pages (`:188`)
  - the selection weights (`:189`)

  The list is now what it says it is. Resolved.
- **Review 009's finding 2** (a settled decision under *open work*): the sentence moved to the
  *product* entry (`CLAUDE.md:47-49`), next to the owner's archive, as review 009 suggested. It
  now points to `docs/book-plan.md`. "the owner's workspace that uses the library" agrees with
  `docs/book-plan.md:184` ("installs the library like any other user would"). The *open work* entry
  no longer holds a closed item. Resolved.
- **Review 009's finding 3** (the status paragraph did not name all the owner decisions): the
  paragraph at `docs/book-plan.md:4-9` now names three places.
  - *The slot's decided list:* this is `CLAUDE.md:121-139`, and it is unchanged.
  - *"the answered open questions of F-1 in `ROADMAP.md`":* questions 1, 3, 5 and 6 each carry
    "Decided by the owner on 2026-09-24" (`ROADMAP.md:85`, `:95`, `:102`, `:106`).
  - *"the entries marked 'Decided by the owner' in *Open decisions* below (the package name, where
    the owner's book lives)":* these are `docs/book-plan.md:177` and `:182`. A grep for "Decided"
    in that file finds only these two entries, so the list is complete.

  Every place the paragraph names really holds owner decisions. Resolved.
- **Nothing else changed:** the diff is limited to the lines above. `git grep` at the revision
  finds no other place that describes the book's location as open, and no other mention of F-4.
- **Gates:** not re-run. The PR changes three Markdown files, and neither `ruff` nor `pytest`
  reads them. The PR body reports `ruff` clean.

## Findings

1. **non-blocking** — `ROADMAP.md:16`: "Reading the owner's 149 OTB games kept 140 and left out 8
   of the owner's own". 140 + 8 is 148, so a reader is left looking for the 149th game. The
   library's own report explains it: it is one duplicate (`duplicates=1`), not a ninth missed
   game. The claim is accurate, but the arithmetic does not close. Suggestion: "kept 140 (one more
   was a duplicate) and left out 8 …".

2. **non-blocking** — `ROADMAP.md:16`: "because player names match exactly except for letter case".
   The code also ignores leading and trailing spaces (`pgn_postmortem/collection.py:275`,
   `:317-318`, and the docstring "compared without regard to case or surrounding spaces"). This
   matters a little because the proposal says "ignoring spacing": surrounding spaces are already
   ignored, and what is new is spacing *inside* a name (`Diego , Amicabile`). Suggestion: "except
   for letter case and surrounding spaces", or leave the detail to shaping.

3. **non-blocking** — `docs/book-plan.md:10-11`, in the paragraph this change edits, though not in
   the edited sentence: "Nothing below is implemented yet, except what the 'Existing spike'
   section lists (on the `book-poc` branch)." This is stale on `main` already. F-1.1 (reading and
   analysis, `pgn_postmortem/collection.py`, `analysis.py`) and F-1.2 (the site,
   `pgn_postmortem/site.py`) have landed (`bd1ff17` "Land F-1.2: completion note"). The change
   did not introduce this. It is recorded here because this change's purpose was to make that
   paragraph accurate. Suggestion, for this change or a later record change: "… except F-1.1 and
   F-1.2, which have landed in `pgn_postmortem/`, and the spike on `book-poc`".

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
