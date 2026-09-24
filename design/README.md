# Design records

- **Naming:** `NNN-<slug>.md`, numbered in order (`001-...`), one per change.
- **Owner:** the implementer, in OpenCode mode. Claude mode has no design stage
  and writes no design records (`CLAUDE.md`).
- **Sections:** the problem; findings grounded in the code with `file:line`; the
  design; explicit open questions, with the owner's decisions marked as such.

## Status

The `Status:` field belongs to the implementer — one writer — and every
transition is recorded in the same commit as the event it describes:

| event | the field becomes |
|---|---|
| the record is written | `proposed` |
| a verdict is requested (first submission, or a re-review after fixes) | `in review` |
| a verdict is recorded | `agreed` or `blocked`, naming the revision the verdict covers |
| a material edit after `agreed`, with the re-review requested | `in review` |
| the change has merged and the completion note is written | `landed` |

`landed` requires the latest verdict to be `agreed`; a `blocked` record cannot
land without an intervening `agreed`.

## The verdict

- **The reviewer appends a verdict section.** Its format and signature are in
  [`reviews/README.md`](../reviews/README.md) — the target proof included — and
  the meaning of a verdict is in [`PRINCIPLES.md`](../PRINCIPLES.md). Each
  appended verdict is one round, counted for the ceiling there.
- **Earlier verdicts stay in place as history**; materiality is in
  `PRINCIPLES.md`.

## Completion

When the change lands, the implementer appends a `## Completion` section —
each done-when item and the evidence that closed it (the CI run, the gate
output) — signed by the implementer. The note is non-material and may only
transcribe the already-agreed items; its boundary is in `PRINCIPLES.md`.

**With a remote**, the protocol's posting rule applies (`PRINCIPLES.md`).
