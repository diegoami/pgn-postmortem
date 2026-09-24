# Roadmap — requests and iterations

> How the project grows. The owner writes requests; the agent shapes them; an
> accepted request is one iteration, one session and one review
> ([`PLAN.md`](PLAN.md), when the overlay is used).

## The queue

The owner confirmed on 2026-09-24 that the quoted wording of F-1 to F-3 is the owner's own.

| id | request | status | iteration | notes |
|---|---|---|---|---|
| F-1 | "first publishing a pip / python library that creates a wikipedia / epub from a pgn collection" | requested | | The direction is in [`docs/book-plan.md`](docs/book-plan.md), *Layer 1*. Also in the owner's words: "I would like to read a book about me and my best and worst games like I was Fischer or Capablanca"; ""worst games" is kind of a bad idea, "best games that I lost", not just blunders.  But all games must be there, wikipedia style."; "in English, German comments are from old engines, strip comments and variants from games". Spike code on the branch `book-poc`. |
| F-2 | "Yes, LLM, but of course Claude with API key would be too expensive, Deepseek is the realistic option, BYOK for other users" | requested | | The book's prose. Depends on F-1. `docs/book-plan.md`, *Prose*. |
| F-3 | "then wire that into a pipeline that may fetch games from somewhere on the input or put the published files somewhere on the output" | requested | | Depends on F-1. Also in the owner's words: "as sources it must be able to parse a collection of games"; "if it has to be reusable we have to think about people who do not have a github, so output must be pluggable somehow"; "I am not maintaining their repository or web pages". `docs/book-plan.md`, *Layer 2*; the chess.com, lichess and git sources exist as spike code on `book-poc`. |

## Statuses

`requested` → `accepted` → `in design` → `in review` → `landed`; plus `parked`
and `refused`. The agent sets the middle states. **Only the owner parks or
refuses**, and the reason is recorded.

## How to request

Add one row to the table, in your own words — or say it in a session ("add to
the roadmap: …") and the agent appends the row and stops. **A request is not a
request to implement**: the shaping and the design stage still happen, and the
original wording is quoted verbatim in the block and never silently reworded.

## The block, written when a request is accepted

```
### F-N — <title>
- **Original request:** "<verbatim>"
- **Player value:** why this matters
- **Scope:** what will exist after it lands
- **Done when:** the runnable checks
- **Out of scope:** the temptations deferred, so they are recorded not lost
- **Depends on:** other requests, or none
- **Open questions:** owner decisions marked as such
```

## The agent's job

- **Shape** a request when it is picked up: player value, scope, done-when,
  out-of-scope, dependencies, open questions. The shaping *is* the design
  stage — in OpenCode mode it becomes the design record, in Claude mode the
  brief.
- **Size it to one iteration.** Split before starting if it does not fit; never
  let a task grow while in flight.
- Take the **first unblocked** request when told "do the next roadmap item",
  and stop after it.
- Never implement an unshaped request; never mark an owner status; never edit
  the original wording.

## Artistic license

In this project the product is the deliverable, so the license is narrower than
in a process testbed. The agent has **artistic license inside a request**:

- invent the names, the template prose, the layout and styling, the small
  mechanics;
- implement the thing that reads best, not the thing that follows the request
  word for word;
- record what was invented, so the choice is visible and reversible;
- do not ask the owner about wording, names, or flavour.

What the license does not cover: **the intent of the request**, **scope**, **the
done-when and the gates** (extendable with the reason recorded, never
weakened), and **owner decisions**.

The request is a direction; the done-when is the contract.

## How it plugs into the rest

- **Iterations after the scaffold are the landed requests**, in order.
- **When GitHub exists**, each row becomes an issue, with the block as its body
  and the status as a label; the posting rule is in `PRINCIPLES.md`.
- **A comparison run copies a frozen subset** as its task list: same text, same
  base commit, same gates for every arm.
- The design and review records refer to the request id.
