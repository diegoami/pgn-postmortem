# F-13 Implementation Review 01

- **Revision covered:** `b5016808e32e87c060960144c2cc78760eaff428`.
- **Target proof:** `git rev-parse --verify 'b501680^{commit}'` returned
  `b5016808e32e87c060960144c2cc78760eaff428`; `git rev-parse --verify
  'main^{commit}'` returned `2391c4210c6bed5c5c7a08531a9cfa4012400d7e`;
  `git merge-base main b501680` returned
  `2391c4210c6bed5c5c7a08531a9cfa4012400d7e`; and
  `git diff --name-only 2391c4210c6bed5c5c7a08531a9cfa4012400d7e
  b5016808e32e87c060960144c2cc78760eaff428` returned exactly the files listed
  below. The worktree's unrelated modification to `scripts/update_games.sh` is
  outside that target diff and was not reviewed.
- **Files checked:** `design/002-separate-collections.md`,
  `pgn_postmortem/__init__.py`, `pgn_postmortem/cli.py`,
  `pgn_postmortem/site.py`, `pgn_postmortem/workspace.py`, and
  `tests/test_workspace.py`. The list was obtained from the exact local
  merge-base diff above. I also read `AGENTS.md`, `PRINCIPLES.md`,
  `CLAUDE.md`, `reviews/README.md`, and the complete design record including
  Review 006's AGREE; existing one-site regressions were inspected in
  `tests/test_site.py`.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context
  OpenCode implementation reviewer.
- **Mode:** OpenCode, implementation review.
- **Checks run:** `git diff --check`; Ubuntu
  `.venv/bin/python -m ruff check .` (passed); Ubuntu
  `.venv/bin/python -m pytest -q` (`235 passed`); and
  `node --test 'tests/js/*.test.mjs'` (`32 passed`). I also ran focused
  temporary-directory probes for workspace-home href depth, marker cleanup,
  root-marker trust, and the reserved `index.html` slug. No implementation or
  test file was modified.

## Findings

1. **blocking** — Workspace-home links from game and chapter pages point to
   the collection index, not the workspace landing page.
   - `pgn_postmortem/workspace.py:134-142` passes the same
     `workspace_home="../index.html"` to every generated page. The forwarding
     in `pgn_postmortem/site.py:1091-1113` and `1228-1244` therefore emits
     `../index.html` from both `slug/games/*.html` and `slug/chapters/*.html`.
   - The agreed contract requires `../index.html` only from collection-root
     pages, and `../../index.html` from `games/*.html` and `chapters/*.html`
     (`design/002-separate-collections.md:181-189`). From either nested
     directory the current href resolves to `slug/index.html`, so it does not
     provide the required “All collections” navigation. A focused build probe
     reproduced `wrong=True, correct=False` for a generated game page.
   - Pass a depth-appropriate value to the page builders and add exact href
     assertions for all four page classes. Keep the default `None` path, which
     is why the existing one-site golden regression remains unchanged.

2. **blocking** — Persisted cleanup is not actually authenticated and does not
   track the complete generated profile output.
   - `pgn_postmortem/workspace.py:199-217` authenticates a root manifest using
     the JSON shape and a root HTML meta substring, but never checks the
     required root CSS marker. A focused rebuild with the root CSS marker
     removed still deleted a removed profile, contrary to the trust rule in
     `design/002-separate-collections.md:217-231`.
   - `pgn_postmortem/workspace.py:220-237` validates only path syntax and the
     broad generated-name pattern. It never requires each listed regular file
     to carry the exact HTML generator marker or exact profile CSS marker. A
     marker listing an authored `games/authored.html` therefore deletes that
     file; the focused probe reproduced its disappearance. Validation also
     deletes earlier entries before discovering a later invalid entry, so a
     malformed list is not the required “nothing it lists is removed” case.
     Persisted slugs are not checked with the same resolved-path-under-output
     rule either.
   - `_mark_profile` at `pgn_postmortem/workspace.py:180-196` omits the
     generated `career.html` from `files`, and includes every existing
     `chapters/best-*.html`, including an authored file with that name. Thus a
     normal removed-profile rebuild leaves generated career output behind and
     can later delete authored chapter content. Implement the complete
     marker/trust contract atomically: validate the whole state before any
     unlink, verify every listed file and marker, require the root HTML *and*
     CSS markers, revalidate persisted slugs/paths, and record only files the
     builder generated. Add the malformed-state and authored-file regressions
     required by `design/002-separate-collections.md:262-274`.

3. **blocking** — The reserved `index.html` profile slug is not rejected
   during configuration validation.
   - `pgn_postmortem/workspace.py:95-117` rejects only `assets`; the agreed
     reserved-name rule includes both `assets` and `index.html`
     (`design/002-separate-collections.md:123-127`, `191-193`).
   - With `CollectionProfile("index.html", ...)`, the builder creates a
     directory at the root landing path and later fails while writing the
     landing page. The observed exception is
     `WorkspaceBuildError("workspace")`, not the required pre-write
     `WorkspaceConfigError`. Reject this collision alongside `assets` and
     assert the output remains untouched.

4. **blocking** — The new tests do not establish the agreed F-13 safety and
   isolation contract.
   - `tests/test_workspace.py:39-54` feeds the same six-game fixture to both
     profiles and checks only that two directories/cards exist; it does not
     prove profile-specific games, per-profile counts/career/chapter/quiz
     isolation, overlapping-game retention, or API/TOML structural parity.
   - `tests/test_workspace.py:57-91` covers only duplicate/traversal slugs, one
     source-file byte snapshot, and one authored `notes.txt`. It has no
     reserved-name or either cache/output collision direction, later-profile
     rollback and exact `WorkspaceBuildError` fields/message, final report
     path assertions, complete link resolution/depth checks, no-analysis
     profile behavior, root/profile marker trust cases, or generated-career
     cleanup. The existing `tests/test_site.py` golden suite does pass and
     protects the unchanged one-site command, but it cannot close these new
     workspace obligations.
   - Add the hand-written two-profile fixtures and the exact no-write,
     read-only-cache, atomic-failure, marker-trust, API/CLI parity, and link
     assertions listed in `design/002-separate-collections.md:237-274`.

The existing one-collection golden output and all current gates are green, but
the workspace navigation, persisted cleanup safety, reserved-path validation,
and required verification remain blocking.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
BLOCK
