# F-13 Implementation Review 02

- **Revision covered:** `5760cb3c0ea6a7d8aa72f2dae991ea7b5861f302`.
- **Target proof:** `git rev-parse --verify '5760cb3^{commit}'` returned
  `5760cb3c0ea6a7d8aa72f2dae991ea7b5861f302`; `git rev-parse --verify
  'main^{commit}'` returned `2391c4210c6bed5c5c7a08531a9cfa4012400d7e`;
  `git merge-base main 5760cb3` returned
  `2391c4210c6bed5c5c7a08531a9cfa4012400d7e`; and
  `git diff --name-status 2391c4210c6bed5c5c7a08531a9cfa4012400d7e..5760cb3`
  returned exactly the files listed below. The worktree's unrelated modification
  to `scripts/update_games.sh` is outside this target diff and was not reviewed.
- **Files checked:** `design/002-separate-collections.md`,
  `pgn_postmortem/__init__.py`, `pgn_postmortem/cli.py`,
  `pgn_postmortem/site.py`, `pgn_postmortem/workspace.py`,
  `reviews/033-f13-workspace-impl-01.md`, and `tests/test_workspace.py`.
  The list was obtained from the exact local merge-base diff above. I also read
  `PRINCIPLES.md`, `CLAUDE.md`, `AGENTS.md`, and `reviews/README.md`.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context
  OpenCode implementation reviewer.
- **Mode:** OpenCode, implementation review.
- **Checks run:** `git diff --check 2391c421..5760cb3` (passed);
  `.venv/bin/python -m ruff check .` (passed);
  `.venv/bin/python -m pytest -q` (`236 passed`);
  `node --test 'tests/js/*.test.mjs'` (`32 passed`); and focused workspace
  tests (`5 passed`). Temporary-directory probes verified the nested
  workspace-home hrefs, reserved `index.html` rejection, root CSS marker
  authentication, career tracking, and the authored `chapters/best-*.html`
  cleanup case. No implementation or test file was modified.

## Prior findings

1. **Resolved:** game and chapter pages now use `../../index.html`, while
   collection-root pages use `../index.html` (`pgn_postmortem/site.py:1632-1660`;
   `pgn_postmortem/workspace.py:134-142`). The focused probe checked generated
   index, career, quiz, chapter and game pages.
2. **Partially resolved:** root HTML and CSS authentication, persisted slug
   validation, complete validation-before-unlink for each profile marker, and
   generated `career.html` tracking are now present
   (`pgn_postmortem/workspace.py:183-186`, `201-230`, `243-260`). The remaining
   cleanup defect is recorded below.
3. **Resolved:** `index.html` is rejected with the other reserved slugs before
   output staging (`pgn_postmortem/workspace.py:96-97`), and the test covers it
   (`tests/test_workspace.py:69-73`).
4. **Unresolved:** the workspace tests still do not establish the complete
   agreed F-13 contract. The remaining verification gap is recorded below.

## Findings

1. **blocking** — An authored chapter file matching `chapters/best-*.html`
   prevents cleanup of the rest of a removed profile.
   - `_mark_profile` adds every regular matching chapter path to the persisted
     `files` list without checking `is_generated`
     (`pgn_postmortem/workspace.py:189-193`). On a rebuild with an authored
     `chapters/best-authored.html`, that authored file is therefore recorded as
     managed state.
   - `_clean_profile` correctly rejects that entry because it lacks the HTML
     generator marker (`pgn_postmortem/workspace.py:255-260`), but it rejects
     the whole marker before unlinking anything. Consequently the generated
     profile index, career page and other generated files remain when the
     profile is removed. A focused probe reproduced
     `authored_chapter_cleanup True True True`: the authored file survived, but
     generated `index.html` and `career.html` also survived.
   - Record only generated chapter files, as is already done for `career.html`,
     and add the authored `chapters/best-*.html` regression. The required
     contract is removal of generated pages while preserving authored content
     (`design/002-separate-collections.md:251-263`).

2. **blocking** — The implementation tests do not close the complete workspace
   contract required by the design.
   - `tests/test_workspace.py` has only five tests. Its shared fixture gives
     both profiles the same source collection (`tests/test_workspace.py:14-36`)
     and the assertions only check that two sites exist, one game link depth,
     one manifest, one cache snapshot, one reserved slug, and one authored text
     file (`tests/test_workspace.py:39-119`). It does not prove profile-specific
     game/career/chapter/quiz isolation, overlapping-game retention, no-analysis
     behavior, all link depths and stylesheet links, or API/TOML structural
     parity.
   - It also lacks the agreed tests for both cache/output collision directions,
     complete invalid-slug/path no-write behavior, a later-profile failure with
     exact `WorkspaceBuildError` fields/message and unchanged output, final
     report paths, malformed authenticated root/profile state, generated-career
     cleanup, and preservation of every authored profile/other-profile page
     (`design/002-separate-collections.md:239-272`). The focused authored
     chapter probe demonstrates that the current five-test suite is green while
     this required safety case is broken.
   - Add the hand-written two-profile fixtures and the explicit assertions
     listed in the agreed test contract; these are necessary verification for
     the F-13 isolation and cleanup behavior, not unrelated coverage.

The target is correct and all declared gates are green, but the authored chapter
cleanup defect and the incomplete contract verification remain blocking.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
BLOCK
