# Verification patterns (optional)

> **Nothing here is required.** Test frameworks, UI checks, mutation harnesses
> and CI belong to the project (`PRINCIPLES.md` owns the six disciplines; the
> project's gates table lives in the `CLAUDE.md` project slot). These are the
> patterns the source projects converged on — adopt what fits, cite what you
> borrow, and record your own numbers.

1. **Deterministic unit tests over a DOM-free engine.** Keep the rules in a file
   that touches no `document`, `window`, timers or `Math.random`; Node runs the
   same file as the browser. Randomness arrives as an injected `rng`. Example:
   the three card games' `tools/engine.test.mjs`, run by `npm test`.

2. **A golden fixture.** Freeze a scripted session's output and assert against
   it, so an accidental change is caught and a deliberate one is re-recorded in
   the same commit (`node tools/selfplay.mjs --golden > tools/golden.json` in
   Tressette and Scopetta). The toy's equivalent is a scripted walkthrough
   transcript.

3. **A UI check that renders states, not just screens.** Load the page at real
   viewports and put it in the states a person can reach — including the states
   that exist only mid-action. Each assertion names the defect it was written
   for; an assertion that is never in a position to see its subject is
   decoration. Examples: `tools/check_ui.mjs` and the `ui-check` skill in the
   card games; `test/browser.test.mjs` in balloons-JS.

4. **The mutation harness.** Break the page or the engine on purpose, one
   defect at a time, and require *the assertion written for that defect* to go
   red — not merely that something did. A `QUICK` mode is for proving an
   assertion bites, never for clearing a check; the survivors are the finding,
   because each is an assertion that cannot fail. Example: Scopetta's
   `tools/break_ui.mjs` and `tools/break.mjs` (141 breaks, 126 caught, 15
   survivors — all "the assertion was never in a position to see its subject").
   A **negative result** — a break nothing caught — is re-taken before it is
   reported: confirm the break actually applied (a fresh copy or rebuild), that
   the check ran, and that it ran on the revision under review.

5. **Run counts with a stated failure model.** Say what always runs, what runs
   when its inputs change, how many repeats, and why: 3× for engine determinism
   (Discola), 8× for browser timing (balloons-JS), a measured-input tree for a
   25-minute check (Scopetta). A rebase or a hand-resolved conflict re-runs the
   expensive gate.

6. **The older-revision technique.** Point the check at a revision that had the
   bug — `git show <commit>:public/index.html > .old.html`, run the check against
   it — to prove the assertion catches its own defect.

7. **Run old and new side by side.** A broken harness shows up as both columns
   agreeing when they should differ.

8. **Assert what a person would notice — then play it.** Pixels, contrast,
   timing; and after the checks are green, open the thing and use it.

9. **CI as the merge gate.** Two jobs — the dependency-fast unit job first,
   then the environment-heavy check — on every pull request, with the push
   filter on `main` so a PR does not run twice. A red CI does not merge; nothing
   is quarantined to get to green. Example: `check.yml` in Tressette and
   Scopetta; Discola's `ci.yml` adds the icons check.
