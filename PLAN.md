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
| 2 | F-1.2 of F-1, "first publishing a pip / python library that creates a wikipedia / epub from a pgn collection" | F-1.2 in F-1's block | F-1.3, F-1.4, F-2, F-3 | chosen by the owner | written when the iteration starts (OpenCode mode) | large | the assignment table (OpenCode) or a fresh-context session (Claude) |
| 3 | F-1.3 of F-1, "first publishing a pip / python library that creates a wikipedia / epub from a pgn collection" | F-1.3 in F-1's block | F-1.4, F-2, F-3 | chosen by the owner | written when the iteration starts (OpenCode mode) | large | the assignment table (OpenCode) or a fresh-context session (Claude) |
| 4 | F-1.4 of F-1, "first publishing a pip / python library that creates a wikipedia / epub from a pgn collection" | F-1.4 in F-1's block | F-2, F-3 | chosen by the owner | written when the iteration starts (OpenCode mode) | medium | the assignment table (OpenCode) or a fresh-context session (Claude) |
| 5+ | the first unblocked roadmap request, in the owner's order | that request's block in `ROADMAP.md` | the other requests | chosen by the owner | written when the request is shaped (OpenCode mode) | per request | as above |

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
