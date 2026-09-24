# Review 009 — Record where the owner's book lives, implementation round 01

- **Revision covered:** `73b87b2037438150d64e60241e03116791affefe` (branch `record-book-workspace`,
  pull request #9), one commit on top of `main` at `bd1ff174b6fa84b29a30cde90aeddff788ab121e`.
- **Target proof:** after `git fetch -q origin`, `git rev-parse origin/record-book-workspace` gives
  `73b87b2…`, which equals `gh pr view 9 --json headRefOid`. The merge base with `origin/main` is
  `bd1ff17`, which is also the tip of `origin/main`.
- **Files checked:** `CLAUDE.md`, `docs/book-plan.md`.
  - Obtained from `gh pr view 9 --json files` and from
    `git diff --name-only $(git merge-base origin/main origin/record-book-workspace)..origin/record-book-workspace`;
    the two lists are equal.
  - Read at the revision with `git show origin/record-book-workspace:<path>`.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent. I have
  not seen the implementation session.
- **Mode:** Claude Code.

## What I checked, and how

- **The diff, read in full** (`git diff origin/main..origin/record-book-workspace`): 10 lines added,
  2 removed, in the two files above. No code, test, generated file or process rule changes.
- **Against the rules on `main`:** `PRINCIPLES.md` (*Owner decisions*, the target proof), the
  `CLAUDE.md` project slot, `reviews/README.md`, and the completion note of
  `reviews/004-record-f1-decisions-impl-02.md`.
- **The decision record** (`docs/book-plan.md:180-185`): it is marked as the owner's ("Decided by the
  owner on 2026-09-24"), dated, and names the recommended default and the reason ("Recommended
  default, chosen by the owner. Reason: the repository already exists and already holds the owner's
  games."). That satisfies *Owner decisions* in `PRINCIPLES.md`, and it follows the form of the
  *Package name* entry just above it (`docs/book-plan.md:175-177`). I checked that the reason is
  true as far as the outside world shows it: `gh repo view diegoami/chessgamescollection` finds a
  public, unarchived repository whose top level holds `analyzed_games/`, `daily_games/` and `docs/`.
  Whether the owner took this decision cannot be checked from the repository; the owner's merge is
  that check.
- **Against the slot's *decided, and not to be re-opened* items** (`CLAUDE.md:119-137`):
  - *The deliverable is the tool; the owner hosts nothing and maintains no one else's repository*:
    the workspace is the owner's own repository and "installs the library like any other user
    would", so the owner is a user of the tool, not a host for others. Consistent.
  - *Library before pipeline*: the decision says where the owner's output lives. It sets up no
    pipeline and no fetching. Consistent. The PR body leaves setting up the workspace, and any run
    on the owner's games, to when the owner asks, which matches *Planning is not building*
    (`CLAUDE.md:114-118`).
  - "This repository stays generic tooling with no personal data": true today. `examples/` holds
    classic games (for example Chigorin–Steinitz, `examples/daily_games/1.pgn`). The only matches
    for the owner's name or handle in `README.md`, `examples/` and `tests/` are the repository's own
    URLs in `README.md`. The slot's *never read or echo* rule is about local paths; a public GitHub
    repository name is not one.
  - "`DA_chessgames` stays a read-only source": consistent with the slot's product line
    (`CLAUDE.md:44-46`) and with `docs/book-plan.md:157` and `:187`.
- **The open-work line against `docs/book-plan.md`'s *Open decisions*:** still open there are the
  pipeline as a separate package (`:176-177`), the licence (`:178-179`), the Markdown pages
  (`:186`) and the selection weights (`:187`). The new line (`CLAUDE.md:138-142`) names the licence
  under `ROADMAP.md` and the other three under `docs/book-plan.md`, so all four are reachable from
  it. The licence, the Markdown pipeline and the weights are also open questions 2, 4 and 9 in
  `ROADMAP.md`, which still agree with `docs/book-plan.md`. See finding 1.
- **Review 004's deferred finding:** the completion note asks the open-work line to "point to the
  two decisions still open in `docs/book-plan.md` (whether the pipeline is a separate package, and
  where the owner's own book lives)" in "the change that settles either one". This change settles
  the second and names the first ("whether the pipeline is a separate package"), and it states where
  the book lives. Resolved.
- **Nothing else:** no other file mentions `chessgamescollection` or lists the book's location as
  open (`git grep` at the revision; the only other hits are review 004's historical text).
- **Gates:** not re-run. The diff touches two Markdown files that neither `ruff` nor `pytest`
  reads, so they cannot change a gate's result. The PR body reports `ruff` clean and `75 passed`.

## Findings

1. **non-blocking** — `CLAUDE.md:139-141`: "the decisions still open there (whether the pipeline is
   a separate package, the Markdown pages, the selection weights)". The words "still open there"
   read as the full list for `docs/book-plan.md`, but that file also lists the licence as open
   (`docs/book-plan.md:178-179`). The line names the licence one clause earlier, under `ROADMAP.md`,
   so a reader still finds it. Nothing is missing, but the list is not what it says it is. Suggestion:
   "(besides the licence: whether the pipeline …)", or add the licence to the list.

2. **non-blocking** — `CLAUDE.md:141-142`: "The owner's own book lives in
   `diegoami/chessgamescollection` (decided 2026-09-24)." This is a settled decision, placed in the
   *open work* entry. It is not on the *decided, and not to be re-opened* list, and that seems right,
   since it is a workspace choice and not a product rule. But a reader scanning *open work* now finds
   one closed item in it. This is a matter of placement and the owner's call: leave it, or move the
   sentence to the *product* entry, which already names the owner's archive (`CLAUDE.md:44-46`).

3. **non-blocking** — `docs/book-plan.md:4-7` against `:180-185`. The status paragraph says the
   owner's settled choices "are the ones listed under *decided, and not to be re-opened* in the
   `CLAUDE.md` project slot", and that "everything else here is direction, not agreed for
   implementation". The file now holds two owner decisions that are not on that list: the package
   name (from #4) and, with this change, the book's location. The package name already had this
   problem, so this change repeats it and did not start it. Suggestion, for this change or a later
   one: "… in the `CLAUDE.md` project slot, plus the decisions marked as the owner's under *Open
   decisions* below".

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.

## Completion

Merged by the owner on 2026-09-24 as `126caf5` (pull request #9); the clean round, 01, covers `73b87b2`. CI on the merge commit passed: https://github.com/diegoami/pgn-postmortem/actions/runs/36039791390.

- **The decision is recorded as the owner's, dated, with its default and reason:** `docs/book-plan.md`, "Where Diego's own book lives".
- **The open-work pointer names what is still open,** and review 004's deferred round-02 finding 1 is resolved.
- **Only `docs/book-plan.md` and `CLAUDE.md` change,** plus this review record.

Left for a later record change, as the owner accepted: findings 1–3. These are the licence missing from the open-work line's list, a settled decision placed under "open work", and the plan's status paragraph not mentioning the owner decisions it now holds.

— Implementer, Claude Opus 5.5 (claude-opus-5-5)
