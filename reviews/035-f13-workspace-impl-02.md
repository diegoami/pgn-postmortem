# F-13 Workspace Implementation Review 02

- **Revision covered:** `e7bcb9a390ed558097738863338b554c8b5ddf98`.
- **Target proof:** `git rev-parse --verify 'e7bcb9a^{commit}'` returned
  `e7bcb9a390ed558097738863338b554c8b5ddf98`; `git rev-parse --verify
  'main^{commit}'` returned `2391c4210c6bed5c5c7a08531a9cfa4012400d7e`;
  `git merge-base main e7bcb9a` returned
  `2391c4210c6bed5c5c7a08531a9cfa4012400d7e`; and
  `git diff --name-status
  2391c4210c6bed5c5c7a08531a9cfa4012400d7e..e7bcb9a390ed558097738863338b554c8b5ddf98`
  returned exactly the files listed below. The worktree's unrelated
  modification to `scripts/update_games.sh` is outside this target and was not
  reviewed.
- **Files checked:** `design/002-separate-collections.md`,
  `pgn_postmortem/__init__.py`, `pgn_postmortem/cli.py`,
  `pgn_postmortem/site.py`, `pgn_postmortem/workspace.py`,
  `reviews/033-f13-workspace-impl-01.md`,
  `reviews/034-f13-workspace-impl-02.md`, and `tests/test_workspace.py`.
  This list was obtained from the exact merge-base diff above. I also read
  `AGENTS.md`, `PRINCIPLES.md`, `CLAUDE.md`, `reviews/README.md`,
  `design/README.md`, the complete F-13 design record, and the prior
  implementation reviews.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context
  OpenCode implementation reviewer.
- **Mode:** OpenCode, implementation re-review.
- **Checks run:** `git diff --check` (passed); `.venv/bin/python -m ruff check .`
  (passed); `.venv/bin/python -m pytest -q` (`238 passed`); `node --test
  'tests/js/*.test.mjs'` (`32 passed`); focused workspace tests
  (`7 passed`); and temporary-directory probes for all available workspace
  page links/report paths, authored chapter cleanup, root-marker rejection,
  cache/output path collisions, and complete later-profile rollback. The
  marker probe below reproduced a remaining failure. No implementation or
  test file was modified.

## Prior findings

1. **Resolved:** `_mark_profile` now records only generated `chapters/best-*.html`
   files (`pgn_postmortem/workspace.py:189-193`). A focused rebuild with an
   authored `best-authored.html` preserved that file while removing the
   removed profile's generated index and career pages.
2. **Resolved:** collection-root pages receive `../index.html`, while game and
   chapter pages receive `../../index.html` through the forwarding in
   `pgn_postmortem/site.py:1632-1660`; the available generated pages and their
   local links resolved in the focused probe. The reserved `index.html` slug,
   root HTML/CSS authentication, persisted-slug checks, bidirectional
   cache/output checks and staged rollback are present and their focused cases
   passed.
3. **Partially resolved:** the agreed workspace contract still lacks the
   required complete verification suite; see Finding 2 below.

## Findings

1. **blocking** — Profile-marker cleanup can partially unlink a malformed,
   marker-authenticated file list.
   - `pgn_postmortem/workspace.py:243-263` validates each entry and then
     unlinks entries in sequence, but never rejects duplicate normalized paths.
      With a valid-looking marker whose `files` contains a duplicate
      `index.html` entry, the first unlink succeeds; the second raises
     `FileNotFoundError`, which is swallowed by the handler. The generated
     profile index is therefore gone while cleanup aborts and the marker
     remains.
   - I reproduced this against the target in a temporary workspace after
     removing the profile. This violates the agreed all-or-nothing trust rule:
     an untrusted or malformed marker must cause nothing it lists to be
     removed (`design/002-separate-collections.md:217-231`, `262-274`).
   - Reject duplicate entries (and complete all structural validation) before
     any unlink, retaining the existing authored-file and path/marker checks;
     add a regression that proves the generated files and marker remain
     unchanged for this malformed state.

2. **blocking** — The implementation tests still do not establish the complete
   agreed F-13 workspace contract.
   - `tests/test_workspace.py:14-59` uses different, non-overlapping source
     fixtures for the two profiles (`games.pgn` and `odd.pgn`), so it does not
     prove that the same game is retained once in each profile without
     cross-profile deduplication. It checks article-list lengths and a few
     links, but not profile-specific career/chapter/quiz/index counts or the
     chapter and stylesheet link graph.
   - The seven tests do not cover the design's required no-analysis behavior
     and chapter-link absence, history/no-history output, API/TOML structural
     parity, both cache/output collision directions, the complete invalid-slug
     and path no-write matrix, preservation of every authored/other-profile
     page, or successful report paths for `articles`, `removed` and `quiz`.
     `tests/test_workspace.py:61-153` also checks only one file before and
     after rollback and only a message prefix, not the exact `cause`, message,
     unchanged complete output tree, and staging cleanup required by the
     design.
   - These are the explicit verification obligations in
     `design/002-separate-collections.md:237-272`, not optional regression
     coverage. The current green tests can therefore pass while the required
     isolation, navigation, cleanup, parity and atomic-failure contract is
     wrong. Add the hand-written overlapping/profile-specific fixtures and the
     explicit assertions for each listed obligation.

The nested-link, authored-chapter, path-validation and rollback implementation
probes passed, and the existing one-site gates remain green. The remaining
marker atomicity defect and incomplete contract verification are blocking.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
BLOCK
