# F-13 Workspace Implementation Review 03

- **Revision covered:** `7633c8032d687a1f098457dd2b3a1f9f33b7604e`.
- **Target proof:** `git rev-parse --verify '7633c80^{commit}'` returned
  `7633c8032d687a1f098457dd2b3a1f9f33b7604e`; `git rev-parse --verify
  'main^{commit}'` returned `2391c4210c6bed5c5c7a08531a9cfa4012400d7e`;
  `git merge-base main 7633c80` returned
  `2391c4210c6bed5c5c7a08531a9cfa4012400d7e`; and
  `git diff --name-status 2391c4210c6bed5c5c7a08531a9cfa4012400d7e..7633c8032d687a1f098457dd2b3a1f9f33b7604e`
  returned exactly the files listed below. The worktree's unrelated
  modification to `scripts/update_games.sh` is outside that target diff and
  was not reviewed.
- **Files checked:** `design/002-separate-collections.md`,
  `pgn_postmortem/__init__.py`, `pgn_postmortem/cli.py`,
  `pgn_postmortem/site.py`, `pgn_postmortem/workspace.py`,
  `reviews/033-f13-workspace-impl-01.md`,
  `reviews/034-f13-workspace-impl-02.md`,
  `reviews/035-f13-workspace-impl-02.md`, and `tests/test_workspace.py`.
  This list was obtained from the exact local merge-base diff above. I also
  read the governing process files and the complete F-13 design record.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context
  OpenCode implementation re-reviewer.
- **Mode:** OpenCode, implementation re-review.
- **Checks run:** `git diff --check` (passed); Ubuntu
  `.venv/bin/python -m ruff check .` (passed); Ubuntu
  `.venv/bin/python -m pytest -q` (`241 passed`); focused workspace tests
  (`10 passed`); and `node --test 'tests/js/*.test.mjs'` (`32 passed`). A
  temporary-directory probe also checked normalized duplicate marker entries;
  it reproduced partial deletion. No implementation or test file was
  modified.

## Prior findings

1. **Resolved:** workspace-home links now use `../index.html` from
   collection-root pages and `../../index.html` from game and chapter pages
   (`pgn_postmortem/site.py:1632-1660`, `pgn_postmortem/workspace.py:134-142`).
2. **Resolved:** root HTML/CSS authentication, persisted-slug validation,
   generated-career tracking and authored matching chapter preservation are
   present (`pgn_postmortem/workspace.py:183-193`, `201-230`, `243-265`).
   The duplicate-path atomicity part of Review 035 is not resolved; see
   Finding 1.
3. **Resolved:** the reserved `index.html` slug is rejected before staging
   (`pgn_postmortem/workspace.py:96-97`).
4. **Unresolved:** the complete workspace contract test suite required by
   Review 035 is still absent; see Finding 2.

## Findings

1. **blocking** — Profile-marker cleanup still partially deletes a malformed
   file list when duplicate entries differ only by path spelling.
   - `pgn_postmortem/workspace.py:243-264` checks
     `len(set(files))`, but compares the raw JSON strings rather than their
     normalized `Path` values. `index.html` and `./index.html` therefore pass
     the duplicate check, resolve to the same target, and are both appended to
     `validated`.
   - Cleanup unlinks the first target, then the second unlink raises
     `FileNotFoundError`; the handler at lines 266-267 swallows it. A focused
     temporary-directory probe against this exact revision reproduced the
     generated profile index disappearing while
     `.pgn-postmortem-profile.json` remained. The same failure occurs for
     `assets/style.css` and `assets/./style.css`.
   - This violates the all-or-nothing trust rule in
     `design/002-separate-collections.md:217-230` and is the normalized form
     of Review 035's duplicate-marker finding. Canonicalize and reject
     duplicate normalized relative paths before any unlink, and add the
     normalized-path regression. The current test at
     `tests/test_workspace.py:155-167` covers only two identical raw strings,
     so it passes while this defect remains.

2. **blocking** — The implementation tests still do not establish the
   complete agreed F-13 workspace contract.
   - `tests/test_workspace.py:39-66` checks only one collection-root link and
     one game link, not the career, quiz, chapter, root stylesheet and full
     link-resolution graph. Its API/CLI comparison checks only selected bytes,
     not the complete landing/profile structure.
   - `tests/test_workspace.py:98-115` checks that one profile has more
     articles and that quiz files exist, but does not prove that the
     overlapping game is retained once in each profile, or that each
     profile's career, chapter, quiz and index counts contain only its own
     games. The no-analysis case does not assert the complete expected link
     and output contract.
   - `tests/test_workspace.py:68-83` covers only a subset of the required
     invalid-slug/path no-write matrix. It omits the reserved `assets` case,
     empty/non-ASCII/overlong slugs, overlapping profile outputs, cache-under-
     output collisions and the other input/cache collision directions.
   - `tests/test_workspace.py:118-153` preserves one authored text file and
     one authored chapter, but does not assert removal of every generated
     page, stylesheet and marker while preserving all other-profile pages.
     It also lacks the malformed authenticated root/profile marker cases
     required by the design.
   - `tests/test_workspace.py:85-96` snapshots one cache file rather than
     the complete input/analyzed cache tree. The later-profile failure test at
     lines 169-185 checks one output file and a message prefix, not the exact
     message, complete unchanged output tree, staging cleanup and all final
     `WorkspaceReport` paths (`articles`, `removed` and `quiz`) rebased to the
     committed output.
   - These are the explicit verification obligations at
     `design/002-separate-collections.md:237-272`, not optional extra
     coverage. The green ten-test focused suite can therefore pass while the
     required isolation, navigation, cleanup, persisted-state trust and
     atomic-failure contract remains unverified. Complete the hand-written
     fixture and assertion matrix before approval.

The nested-link, authored-chapter, reserved-path, root-marker and
bidirectional-path implementation probes passed, and the existing one-site
regressions and all declared gates remain green. The normalized marker
atomicity defect and the incomplete required contract verification remain
blocking in this third implementation-review round.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
BLOCK

## Owner Waiver

- **Date:** 2026-10-01.
- **Owner decision:** waive the remaining breadth-of-workspace-contract-test
  coverage finding at implementation stage. The normalized marker-path cleanup
  defect was fixed in commit `57aab31` and is not waived.
- The waiver does not waive the three gates, profile isolation behavior,
  persisted-state safety, or the owner's required OTB/correspondence landing
  page inspection.
- **Owner:** Diego

This is an implementation-stage waiver, not an `AGREE` verdict.

— Implementer (DeepSeek V4.1 Flash)
WAIVED
