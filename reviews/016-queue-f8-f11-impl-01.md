# Review 016 — queue F-8 to F-11, implementation, round 01

- **Revision covered:** `ec8f14d30870851c87d6dcc577bd288e29d3128a` (branch `queue-f8-f11`, pull
  request #16). After `git fetch origin`, `git rev-parse origin/queue-f8-f11` equals the pull
  request's `headRefOid`.
- **Files checked:** `ROADMAP.md`, the only file. Obtained from the pull request's files
  (`gh pr view 16 --json files`) and checked against the local diff from the merge base
  (`git diff --name-only $(git merge-base origin/main origin/queue-f8-f11)..origin/queue-f8-f11`,
  merge base `aa054d7`). The two lists match. One commit on the branch.
- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh-context Claude Code subagent that
  did not see the change being written.
- **Mode:** Claude Code.
- **Read for context, on `origin/main`:** `CLAUDE.md` (the slot), `ROADMAP.md` (*The queue*,
  *Statuses*, *How to request*, *The agent's job*, F-1's open questions), `reviews/README.md`,
  `pgn_postmortem/site.py`, `README.md` (*The site*), `docs/book-plan.md` (*Output*), and the
  golden articles under `tests/golden/site/games/`.

## What was checked

- **Only the four rows change.** `git diff -U0` shows four added lines in the queue table, after
  F-7, and nothing else. No code, no other rows, no blocks.
- **Row form.** Every row in the table, the new ones included, has five cells, counted by splitting
  on `|`. There is no `|` inside any new cell. The status is `requested` and the iteration cell is
  empty in all four rows.
- **The owner's words.** Each request is quoted with its spelling kept ("worse blunder", "the game
  are yours", "possibilty", "pop up-", "the spoilers you have looked"). No row rewords a request.
  The repository cannot show that the owner said these words; the owner's merge is that check.
- **Not shaped.** None of the rows has an accepted block, a scope, done-when items or a size. Each
  note says "Not shaped yet" and names the choices shaping will face without choosing one. F-10's
  two ways and F-11's survival across rebuilds are marked as owner decisions. "The owner orders it
  against F-1.3" leaves the order to the owner, like F-4's note. Nothing is pre-decided.
- **Consistency with the current site.** `pgn_postmortem/site.py:13` says "There is no JavaScript
  and nothing is loaded from the network", and `README.md:194` says the same. The answers at
  critical moments are `<details class="answer">` elements (`site.py:780`), so F-8's "the
  `<details>` opened" is accurate. Each critical moment has an anchor `id="moment-N"`
  (`site.py:775`; for example `moment-1` in the golden articles), so F-9's "each linking to its
  position" is possible with the site as it is. F-9's order, "most winning chances lost", matches
  the decided grading by win % lost.
- **Consistency with the slot and F-1's licence question.** Question 2 of F-1's open questions is
  the licence decision (default MIT, python-chess being GPL-3.0+). F-10's note sends a GPL
  Stockfish bundle to that question instead of deciding it. None of the notes suggests hosting
  anything for users or maintaining their pages.

## Findings

1. **non-blocking — the notes do not say that F-8, F-11 and F-10's option (b) would bring
   JavaScript into a site that has none by design.** A history kept in the browser, notes typed
   in a pop-up, and Stockfish in WebAssembly all need scripts. Today the site says it has none
   (`site.py:13`: "There is no JavaScript and nothing is loaded from the network"; `README.md:194`:
   "there is no JavaScript"). F-1's EPUB will not carry any of this either, because most EPUB
   readers do not run scripts. That is probably the biggest thing shaping has to weigh, and it is
   the owner's decision, so the notes should name it. F-10's option (a), a plain link to an outside
   analysis board, needs no script, which is a real difference between the two options that the
   note does not show. Suggested: add one clause to F-8, F-10 and F-11 saying that the site
   currently has no JavaScript and that the EPUB would not carry the feature.
2. **non-blocking — for F-8 and F-11, "in the reader's browser" leaves out the `file://` case and
   is loose about rebuilds.** F-1 promises a site that works from `file://` and "from a folder
   copied to a phone" (`site.py:11-13`; F-1's scope). Browsers handle storage for `file://` pages
   in different ways: some give all local files one shared origin, some restrict it, and phone
   browsers often open local HTML poorly. So "per device and per browser" is only safe for a
   served site. In F-11, "keeping them across … rebuilds would need an export/import" is also
   imprecise. Browser storage is tied to the origin, not to the files, so rebuilding at the same
   address keeps it. The real risk is a page whose name changes: articles are named
   `<date>-<id>`, and F-7's own note says a corrected `Date` would change a game's identity.
   Suggested: mention that `file://` support is uncertain, and describe the rebuild risk as a
   renamed page or changed id rather than the rebuild itself.
3. **non-blocking — F-8 cites "the slot's decided *no hosting*", which is not how the slot puts
   it.** The decided item says "The owner hosts nothing and maintains no one else's repository or
   pages; Stockfish runs wherever the user runs the tool". The italics make "no hosting" look like
   a quoted label, but the slot has no such label. The site's lack of a server comes from F-1's
   scope and `docs/book-plan.md` (*Output*: "works offline and from `file://`, no server needed").
   The hosting decision does not give it: a user could serve the site from their own server.
   Suggested: cite F-1's scope, or quote the decided item's own wording.
4. **non-blocking, outside this change — F-6's row still reads `accepted`.** The new notes say
   "after F-6 landed", and `main` has "Land F-6: completion note" (`aa054d7`) and the merge of #15
   (`378dd9c`). But the F-6 row's status cell is still `accepted`, while F-5's row was moved to
   `landed` with its pull request and commit. This pull request does not touch that row and does
   not need to. Recorded so the owner, or the next change, can update the status. The new notes
   are correct.

No other findings. The change is what it claims to be: four `requested` rows, quoted in the
owner's words, with notes that stay notes.

— Claude Opus 5.5 (claude-opus-5-5), reviewer
No blocking finding remains.
