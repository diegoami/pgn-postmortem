# The iteration overlay (optional)

> Delete this file if the project does not slice work into iterations. It adds
> *when work is sliced* and the owner's part; it adds no review process — the
> modes and [`PRINCIPLES.md`](PRINCIPLES.md) own that.

## One iteration per session

Work comes from [`ROADMAP.md`](ROADMAP.md). An **iteration** is one shaped
request: one session, one branch (`iteration-N-<slug>`), one review, one merge.
Do not start the next iteration in the same session; do not grow an iteration
while it is in flight.

## The iteration's shape

Every iteration states, before it starts:

- **the request it lands** — the roadmap id, with the owner's original wording;
- **done when** — the runnable checks that make it complete (the gates it runs,
  and any assertion the change adds);
- **out of scope** — what is deliberately deferred, recorded so it is not lost;
- **the mode** — OpenCode or Claude, and for OpenCode the design record it
  starts from.

## The iteration table

Fill this table as the plan becomes clear; it is a plan, not a contract. Every
column is required: the request with the roadmap id and the owner's wording, the
done-when, what is out of scope, the mode, the design record the iteration
starts from, the effort, and the reviewer.

An iteration may be a **build-order step** with no roadmap request — a step the
project's own plan fixes (a scaffold, an engine, a check). Its request cell says
so; the exception is recorded, never improvised.

| iteration | request | done when | out of scope | mode | design record | effort | reviewer |
|---|---|---|---|---|---|---|---|
| 1 | F-1.1 of F-1, "first publishing a pip / python library that creates a wikipedia / epub from a pgn collection" | F-1.1 in F-1's block in `ROADMAP.md` | F-1.2 to F-1.4, F-2, F-3 | Claude Code (owner, 2026-09-24; it replaces the OpenCode choice made earlier the same day) | none: Claude mode has no design stage (`CLAUDE.md`); the plan is F-1.1 in F-1's block in `ROADMAP.md` | medium | a fresh-context session (`CLAUDE.md`) |
| 2 | F-1.2 of F-1, "first publishing a pip / python library that creates a wikipedia / epub from a pgn collection" | F-1.2 in F-1's block in `ROADMAP.md` | F-1.3, F-1.4, F-2, F-3 | Claude Code (owner, 2026-09-24) | none: Claude mode has no design stage (`CLAUDE.md`); the plan is F-1.2 in F-1's block in `ROADMAP.md` | large | a fresh-context session (`CLAUDE.md`) |
| 3 | F-5, "There are a few where the results is not recorded, default to victory for the one with much higher winning chances, or draw if unclear." | F-5's block in `ROADMAP.md` | F-1.3, F-1.4, F-2, F-3, F-4 | Claude Code (owner, 2026-09-24) | none: Claude mode has no design stage (`CLAUDE.md`); the plan is F-5's block in `ROADMAP.md` | small | a fresh-context session (`CLAUDE.md`) |
| 4 | F-6, "I am looking at the games and I think there should be more diagrams, for instance in this game https://diegoami.github.io/chessgamescollection/games/2008-01-04-4e5d4e182f.html just an error is shown that did not affect the end result. It was move 40 that was deciding, not 31" | F-6's block in `ROADMAP.md` | F-1.3, F-1.4, F-2, F-3, F-4, F-7 | Claude Code (owner, 2026-09-24) | none: Claude mode has no design stage (`CLAUDE.md`); the plan is F-6's block in `ROADMAP.md` | small | a fresh-context session (`CLAUDE.md`) |
| 5 | F-8, "A local history reminding what games have you been watching and ideally the spoilers you have looked" | F-8's block in `ROADMAP.md` | F-9, F-10, F-11, F-1.3, F-1.4, F-2, F-3, F-4, F-7 | Claude Code (the owner's standing choice of 2026-09-24, applied 2026-09-25) | none: Claude mode has no design stage (`CLAUDE.md`); the plan is F-8's block in `ROADMAP.md` | medium | a fresh-context session (`CLAUDE.md`) |
| 6 | F-9, "A list of proposed quiz, starting from your worse blunder, assuming the game are yours." | F-9's block in `ROADMAP.md` | F-10, F-11, F-1.3, F-1.4, F-2, F-3, F-4, F-7 | Claude Code (the owner's standing choice of 2026-09-24, applied 2026-09-25) | none: Claude mode has no design stage (`CLAUDE.md`); the plan is F-9's block in `ROADMAP.md` | medium | a fresh-context session (`CLAUDE.md`) |
| after F-8 to F-11 | F-1.3 of F-1, "first publishing a pip / python library that creates a wikipedia / epub from a pgn collection" | F-1.3 in F-1's block | F-1.4, F-2, F-3 | chosen by the owner | written when the iteration starts (OpenCode mode) | large | the assignment table (OpenCode) or a fresh-context session (Claude) |
| after F-1.3 | F-1.4 of F-1, "first publishing a pip / python library that creates a wikipedia / epub from a pgn collection" | F-1.4 in F-1's block | F-2, F-3 | chosen by the owner | written when the iteration starts (OpenCode mode) | medium | the assignment table (OpenCode) or a fresh-context session (Claude) |
| next | the first unblocked roadmap request, in the owner's order | that request's block in `ROADMAP.md` | the other requests | chosen by the owner | written when the request is shaped (OpenCode mode) | per request | as above |

The owner decided on 2026-09-25 that F-8 to F-11 come before F-1.3. Each gets its iteration number when it is shaped, and F-1.3 and F-1.4 then move after them.

F-1 was split into F-1.1 to F-1.4 when it was shaped (`ROADMAP.md`, *Size it
to one iteration*).

## The owner's part

- **Start each iteration** and stop the session at its end.
- **Answer owner decisions** when they are raised, with the recommended default
  in hand.
- **Play the result** after an iteration that changes what a person sees. The
  checks measure what they measure; only a player measures whether it is fun.
- **File what you find** — the defect path is in `PRINCIPLES.md`.

## Fork provenance

When this project forks from another, record it — a sibling is a moving
reference, not a fixed one, and anything forked is a snapshot with a date.

| forked | from | at | by |
|---|---|---|---|
| — | nothing forked | — | — |

## What outlives a session

- a **decision** → the design record that made it, or the project slot in
  `CLAUDE.md`;
- a **rule a builder must follow** → `PRINCIPLES.md`, `AGENTS.md` or
  `CLAUDE.md`, via the bootstrap;
- **everything a stranger needs** → the project's `README.md` and docs.

If a session ends with something only it knows, that is a defect in the
handoff.
