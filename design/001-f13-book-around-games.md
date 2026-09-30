# F-1.3: the book around the games

Status: agreed (Review 008)

Owner amendment (2026-09-27): after Review 003's third-round BLOCK, the owner
authorized one final design amendment to bind the selection defaults/custom
weights and define empty-feature scoring before another design review.

Owner amendment (2026-09-27): after Review 004's BLOCK, the owner authorized
one additional amendment to define accuracy aggregation and marker-only or
partial-analysis eligibility before another design review.

Owner decision (2026-09-30): because the archived Caissabase page is readable
but its linked 630 MB download returns 404 from Wayback, use PGN Mentor's
Capablanca collection as the demo fallback. Verify and name its free-download
terms; do not claim an open-source license that the source does not publish.

## Problem

The library currently renders one article per game and an index, but it does not
give a reader the book-level context described by F-1: a career article and
featured chapters for the player's best wins, best losses and best draws. F-1.3
must add that book layer without changing the existing Markdown pipeline or
analyzing the owner's archive.

The demo must make the result inspectable by a stranger. It will use a committed
Capablanca subset from the selected public download, with its source and terms
named in the README.

## Findings

- `pgn_postmortem.site.build_site` currently creates the stylesheet, game
  articles, optional quiz and index, then removes only generated stale pages
  (`pgn_postmortem/site.py:1429-1527`). Book pages can use the same generated
  page marker and stale-page rule.
- `Article` already exposes the per-game headers, shown result, analysis status
  and reviewed moves needed by selection (`pgn_postmortem/site.py:743-819`).
- `MoveReview.loss`, `MoveReview.mover`, `MoveReview.critical` and
  `MoveReview.swing` provide the exact winning-chances loss and the F-6 outcome
  information; selection should consume these existing values rather than
  re-analyze games (`pgn_postmortem/site.py:223-263`, `317-365`).
- `Collection` preserves the names used to read the games and passes itself to
  the site builder (`pgn_postmortem/collection.py:278-351`, `393-400`). The
  career page can therefore use the same player and aliases as the quiz.
- The current command exposes only site presentation and history options; it
  has no book-selection options (`pgn_postmortem/cli.py:92-149`). The F-1.3
  defaults need to work from the existing command, while any configurable
  chapter size, minimum length and weights must be represented deliberately in
  the API and CLI rather than hidden in page templates.
- The existing golden site and fixture tests build from committed analyzed
  games and provide DOM/link helpers (`tests/test_site.py:1-67`, `135-149`).
  F-1.3 can add a separate hand-written selection fixture and a career golden
  set without running Stockfish in the tests.
- The Pages demo currently asserts five committed games and their analysis
  metadata in `tests/test_demo.py:1-87`. F-1.3 keeps that contract unchanged
  and adds a separate local book-demo test for the Capablanca data.

## Design

### Book model and selection

Add a small book-selection module that works from the already-read
`CollectedGame` values and the `Article`/`MoveReview` facts. It will expose:

- a selection-weights value with named fields for the documented signals:
  player's accuracy, opponent strength, fight/length, comeback or save, and
  early-blunder penalty;
- a selection function for each outcome class: wins, losses and draws;
- deterministic ranking and a configurable maximum number of games per chapter
  and minimum game length;
- a rule that assigns each game to at most one chapter, after ranking within
  outcome classes, with the chapter assignment and tie-breaking documented and
  tested.

The selection contract is deterministic and uses these normalized features (all
clamped to 0..1). A game is eligible only when it has the analysis marker and
every non-terminal mainline move has an evaluation after it; a marker-only or
partially evaluated game is ineligible. For an eligible game,
`player_accuracy` is `1 - mean(player_move_loss) / 100`, where the mean includes
only `MoveReview` entries whose mover is the player and whose `before` and
`after` values are both present. `opponent_accuracy` is the analogous mean for
the opponent.
`opponent_strength` is `clamp((opponent_rating - 1800) / 600, 0, 1)`, and
`fight` is `clamp((plies - 2 * minimum_length) / (4 * minimum_length), 0, 1)`.
Missing ratings contribute `0.5`; a game with both sides matching the player
uses the mean of both sides' accuracy and neutral opponent values. The
`early_blunder_avoidance` feature is `1 - largest player loss in the first 20
plies / 100`. For every consecutive pair of analyzed positions, `recovery` is
the largest positive change in the player's winning chances, divided by 100,
where the earlier position was below 40%; both player and opponent moves count.
`draw_save` equals `recovery` only when the shown result is a draw, otherwise it
is zero. An eligible game with no player or opponent entries in the respective
mean uses `0.5` for that accuracy; an ineligible game has no score and is never
selected. Missing analysis therefore cannot silently become a neutral featured
game.

The default chapter scores are:

| chapter | score |
|---|---|
| best wins | `0.30 * player_accuracy + 0.15 * opponent_accuracy + 0.20 * opponent_strength + 0.15 * fight + 0.20 * recovery` |
| best losses | `0.35 * player_accuracy + 0.15 * opponent_accuracy + 0.20 * opponent_strength + 0.15 * fight + 0.15 * early_blunder_avoidance` |
| best draws | `0.25 * player_accuracy + 0.15 * opponent_accuracy + 0.15 * opponent_strength + 0.20 * fight + 0.25 * draw_save` |

The public API has a frozen `ChapterWeights` dataclass with exactly the seven
feature fields above (`float` values), and a frozen `SelectionWeights` dataclass
with `wins`, `losses` and `draws` `ChapterWeights` fields. Each value must be
finite and non-negative; each chapter's values must sum to 1 within `1e-9`, or
construction raises `ValueError`. `SelectionOptions` has integer
`chapter_size=5` and integer `minimum_length=20` full moves; both must be at
least 1, or construction raises `ValueError` before anything is written.
`build_site` accepts `selection_options`; the CLI exposes integer
`--chapter-size` and `--minimum-length` flags with the same validation.
`SelectionOptions.weights` is a `SelectionWeights` field defaulting to the
listed defaults; `SelectionOptions()` therefore selects those defaults, and a
caller supplies custom weights with `SelectionOptions(weights=...)`. A
`build_site` call with `selection_options=None` constructs `SelectionOptions()`;
the CLI does the same after parsing its two integer flags. There is no CLI
weight serialization or implicit global state. For an analyzed game with no
player moves or no opponent moves, the corresponding accuracy is `0.5`; a
missing rating is `0.5`, no recovery is `0.0`, and no early loss is an
`early_blunder_avoidance` of `0.5`. Thus every analyzed eligible game has a
defined score, while an unanalyzed game is ineligible. These empty-feature
values are asserted directly in the fixture tests.
Weights are an API option, not a free-form CLI string. The owner chose on
2026-09-27 to tune these defaults only against the hand-written fixtures and
the committed demo. The owner's archive is out of scope and will not be
analyzed. Presumed results from F-5 are used for chapter classification, while
the source PGN remains unchanged.

The selection code ranks only analyzed games whose shown result is the chapter's
outcome, applies the minimum length before ranking, and takes the top
`chapter_size` from each outcome. Tie-breakers after the score are index order,
article file name, then game id. Wins, then losses, then draws claim games in
that order, and a claimed game is excluded from later chapters. It will not use
prose, page order, or engine calls as an implicit signal.

### Generated book pages

Extend the library site with generated pages linked from the index:

- `career.html`: the player's names, active years (the year returned by the
  existing `date_parts` helper; invalid or missing years are omitted), game
  count, shown win/draw/loss/not-recorded counts, yearly totals split into the
  same four result counts, the top ten frequent opponents, peak numeric
  `WhiteElo` and `BlackElo` values, and a repertoire summary by ECO/opening.
  Ratings accept ASCII integer headers only; invalid or missing values are
  omitted. Opponents are counted case-insensitively after `display_name`, with
  ties alphabetical; a game where both sides match the player has no opponent.
  Repertoire rows are counted by ECO then opening, with missing headers omitted,
  ties alphabetical, and a score of `(wins + draws / 2) / games` for the
  player's shown result in that row. The PGN format has no rating-pool field,
  so pool-specific peaks are explicitly out of scope for F-1.3; the two
  side-specific peaks are the available career rating fields. Notable games
  are exactly the selected chapter games, linked with their chapter and score,
  so there is no second hidden selection rule.
- `chapters/best-wins.html`, `chapters/best-losses.html` and
  `chapters/best-draws.html`: chapter introductions and one entry per selected
  game, linking to the existing article;
- the index's book navigation, while preserving its existing game-by-year
  index and quiz/history behaviour.

Use the existing HTML page wrapper, escaping helpers, relative-link convention,
generator marker and deterministic write order. A rebuild removes only book
pages carrying the generator marker; user-authored files are never deleted.
The chapter pages are a view over the same game articles, not duplicate game
content.

Expose the book options through `build_site` and the `site` command with
defaults that produce the book when a player is supplied. A site built without
a player remains a collection site: it has no career article, featured
chapters or quiz. With a player but no analyzed games, the career page is still
written from headers and shown results, while chapter pages and chapter links
are omitted. Mixed collections use every game for the career and only analyzed
games for chapters. Empty collections write the stylesheet and index only.
Rebuilding without a player or without eligible analyzed games removes only
generated career/chapter pages and preserves user-authored files.
`--no-history` removes the script, containers and history `data-*` attributes
from the career and chapter pages too; their links remain relative from their
subdirectories.

### Demo collection

Commit the selected Capablanca PGN subset under
`examples/book_demo/source/`, its depth-22 Stockfish 19 analysis under
`examples/book_demo/analyzed/`, and source metadata in the README. This is a
separate local book demo: it does not replace the validated F-12 root Pages
demo, does not change `.github/workflows/pages.yml` or `tests/test_demo.py`, and
does not feed any file to `scripts/publish_games.py`. The source is PGN Mentor's
Capablanca collection:

`https://www.pgnmentor.com/players/Capablanca.zip`

PGN Mentor's download page lists the collection as Capablanca's 597 games and
states that its PGN files are available for download completely free. It does
not publish a separate open-source license, so the README will not claim one.
It will identify the five-game subset, link the collection and download pages,
state the free-download terms, and label the Stockfish 19 depth-22 files as
derived/analyzed data. The archived Caissabase page and its unavailable download
remain recorded in `ROADMAP.md` as the original source decision and reason for
the fallback.

The README will provide the local command that builds this book from the
committed analyzed data; it will not run Stockfish. The existing five-game
Pages demo and Markdown demo remain unchanged. The owner chose this separate
demo arrangement on 2026-09-27 because F-12 is already landed and its root and
`/markdown/` contracts should remain stable.

## Verification and done-when

- Tests rank hand-made fixture games as specified by F-1.3: a hard-fought loss
  above a loss decided by one early blunder, a draw saved from a lost position,
  deterministic ties, and no game in two chapters.
- Tests cover every selection signal, missing ratings/openings/dates, recorded
  and presumed results, minimum length, chapter limits, both-sides player
  games, and the complete tie key. They assert the component feature values and
  the three default weighted scores, plus invalid weights and option values
  raising `ValueError` before output is written.
- Career fixtures assert the valid-year rule, four result counts, top-ten
  opponent limit and tie order, numeric-rating omission, side-specific peaks,
  repertoire counts and scores, missing-header behavior, and selected-game
  notable links.
- Tests cover empty, no-player, player-with-no-analysis, mixed and stale-page
  rebuilds, including preservation of user-authored pages.
- Golden-file tests cover the career article and all chapter pages from the
  fixture, with link checks proving every selected entry resolves to an
  article. The same tests cover history and `--no-history` output for root and
  chapter pages.
- The separate-demo test proves the committed Capablanca source and analysis
  match, checks Stockfish 19 at depth 22, and checks the generated book pages
  and links without invoking Stockfish. The existing F-12 demo test remains
  unchanged.
- The README acceptance check names the five checked-in games (the 1906
  Raubitschek game and Marshall rounds 1, 2, 5 and 6 from 1909), links both the
  Capablanca collection download and PGN Mentor's downloads page, states that
  the page says the files are available completely free, makes no unsupported
  open-source-license claim, and labels the Stockfish output as
  derived/analyzed data.
- The lint, Python test and JavaScript test gates pass.
- Before merge, the owner reads the book built from the demo collection and
  records whether the chapter picks are right. A negative verdict sends the
  iteration back with the requested changes.

## Open questions

1. The exact public prose wording of career and chapter introductions is an
   implementation detail; the fields and selection rules above are fixed.

— Implementer (DeepSeek V4.1 Flash)

## Review 001

- **Revision covered:** the current worktree design revision: committed `HEAD` `241143e12ef9e81584cfb4ac3d2b700305db0865` plus the uncommitted `design/001-f13-book-around-games.md`. There is no commit containing this design yet.
- **Target proof:** `git rev-parse HEAD` and `git merge-base main HEAD` both gave `241143e12ef9e81584cfb4ac3d2b700305db0865`; `git diff --name-only main...HEAD` was empty; `git status --short --branch` showed the design as untracked. The worktree also contains unrelated `scripts/update_games.sh` and `review-prompt.txt` changes, which are outside this design review.
- **Files checked:** the target design record, `PLAN.md` and `ROADMAP.md` as its shaping context. The current source and verification context checked were `PRINCIPLES.md`, `AGENTS.md`, `CLAUDE.md`, `docs/book-plan.md`, `README.md`, `pgn_postmortem/site.py`, `pgn_postmortem/collection.py`, `pgn_postmortem/cli.py`, `.github/workflows/pages.yml`, `tests/test_site.py` and `tests/test_demo.py`. The target is a worktree rather than a commit because the requested design revision is uncommitted.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context OpenCode reviewer.
- **Mode:** OpenCode, design review.
- **Checks run:** read-only inspection of the cited source, tests, workflow and project records; `git` target-proof commands; and a read-only fetch of the archived Caissabase page at the URL named in the design.

### What holds

- The problem and the proposed pages are grounded in the current library. `Article` carries the game headers, shown result, analysis flag and reviewed moves (`pgn_postmortem/site.py:742-787`); `MoveReview` carries mover, loss, critical and swing facts (`pgn_postmortem/site.py:223-263`); and `Collection` preserves the player and aliases passed to the site (`pgn_postmortem/collection.py:278-351`, `393-400`).
- The design correctly keeps selection on existing analysis facts and explicitly forbids Stockfish calls and tuning on the owner's archive (`design/001-f13-book-around-games.md:50-70`).
- The archived page is reachable and identifies the `2024-04-27` release, links the 630MB download, says chess moves are facts, and links `Attribution-NonCommercial CC BY-NC`. The design correctly does not call this source public domain and requires attribution and the non-commercial term (`design/001-f13-book-around-games.md:97-111`).
- The intended boundary with the Markdown pipeline is stated (`design/001-f13-book-around-games.md:7-11`, `113-116`), and the current Pages workflow keeps the Markdown build under `/markdown/` (`.github/workflows/pages.yml:48-75`).

### Findings

1. **blocking** — The core selection contract is not defined tightly enough to implement or review deterministically.
   - `design/001-f13-book-around-games.md:50-70` names five signals but gives no formula, normalization or missing-header policy for player's accuracy, opponent strength, fight/length, comeback/save or the early-blunder penalty. It also does not say how the player's side is chosen for a game where both sides match, how ratings are compared when one is absent, or how presumed results interact with the score.
   - The current `Article` exposes raw headers and reviews, not these derived measures (`pgn_postmortem/site.py:742-787`), so different implementations can satisfy the prose while selecting different games. The stated tie-breaker is also incomplete for equal date/index and file names.
   - `design/001-f13-book-around-games.md:91-95` requires configurable chapter size, minimum length and weights in both API and CLI, but does not define parameter names, types, validation, serialization of the named weights, or the default values. The open question says to record the defaults only in the implementation review (`design/001-f13-book-around-games.md:136-144`), after the behavior has been implemented.
   - Before implementation, specify the scoring equations and all missing-data rules, the complete tie key and chapter allocation order, the public API/CLI option contract, and the reviewed default values. Extend the fixture assertions so each required signal and option is observable; otherwise the hard-fought-loss and saved-draw assertions can pass while the intended ranking is still wrong.

2. **blocking** — The career article's data contract is incomplete, and one required section has no selection rule.
   - `design/001-f13-book-around-games.md:76-81` requires active years, yearly totals, frequent opponents, a repertoire summary and “notable games”, but defines neither date/header aggregation or missing-date behavior, the opponent counting/tie order, the opening/ECO aggregation and score, nor what makes a game notable. The design's only open questions are URLs and numeric selection defaults, so these are unrecorded behavior rather than deliberate implementation details.
   - `docs/book-plan.md:77-85` also calls for peak ratings per rating pool and repertoire with scores, while the design omits peak-rating handling. The golden test at `design/001-f13-book-around-games.md:125-126` must assert every promised career field, not merely that a page exists.
   - Define the deterministic career aggregations, the notable-game source (and its tie-breakers), and whether peak ratings are in scope for this slice. Add fixture assertions for each field and its missing-data case.

3. **blocking** — The Capablanca demo and F-12 demo contract contradict each other, leaving an unresolved F-12 scope decision.
   - `design/001-f13-book-around-games.md:41-44` says the current five-game Pages test must be updated with the committed source, while `design/001-f13-book-around-games.md:99-116` says the Pages build will use the Capablanca analyzed data but that the existing five-game Pages demo is not changed.
   - The current workflow is hard-coded to `examples/site/analyzed/` and the five-game title (`.github/workflows/pages.yml:48-51`), and `tests/test_demo.py:29-35` hard-codes five games. `ROADMAP.md:24` records F-12's owner decision as the five classic games at the root, with the Markdown demo unchanged at `/markdown/`; its later F-1.3 note says Capablanca *may* replace that demo, not that this design has made that decision.
   - The design must record the owner's choice: either replace the F-12 root demo and name every workflow/test/README change while keeping `examples/docs/**` byte-for-byte unchanged, or keep the five-game root demo and build/test the Capablanca book in a separate, clearly named demo path. It must also state that no Capablanca files are fed to `scripts/publish_games.py` or otherwise alter the Markdown pipeline.

4. **blocking** — The no-analysis and no-player behavior is not specified or covered sufficiently.
   - The project direction says an unanalyzed collection still gets game articles but has no quality-based selection (`docs/book-plan.md:56-63`), while this design says defaults produce the book whenever a player is supplied (`design/001-f13-book-around-games.md:91-95`). It does not say whether `career.html` remains, whether empty chapter pages are written, whether chapter links are omitted, or how a rebuild removes previously generated book pages when analysis is absent or the player is removed.
   - The current builder explicitly supports articles without analysis and has generated-page deletion rules for game pages and `quiz.html` (`pgn_postmortem/site.py:1442-1451`, `1518-1526`). Book pages need an equally precise rule. “Empty/no-player collection” in `design/001-f13-book-around-games.md:123-124` is not an assertion of the expected files or links.
   - Specify and test the matrix for empty, no-player, player-with-no-analyzed-games, and mixed analyzed/unanalyzed collections, including stale generated book pages and preservation of user-authored files.

5. **blocking** — The history promise on generated book pages is not part of the done-when proof.
   - The design requires `--no-history` to remove history data from new pages (`design/001-f13-book-around-games.md:91-95`), but the golden/link test only names career and chapter pages (`design/001-f13-book-around-games.md:125-126`). There is no explicit assertion that those pages have no inline script, history containers or history `data-*` attributes, nor that their relative links work from `career.html` and `chapters/*.html` in both modes.
   - The current wrapper adds the script and generator marker to every page (`pgn_postmortem/site.py:790-817`), and the existing option is implemented at the site level (`pgn_postmortem/site.py:1469-1475`), so a new renderer can easily regress this requirement while all existing article tests remain green.
   - Add history and no-history golden coverage for all new page types, including relative-link checks and the generated-page cleanup rule. Keep the JavaScript gate unchanged; this is Python/site output coverage, not an F-12 or Markdown-pipeline change.

6. **blocking** — The archived-source handling needs one repository-wide documentation correction before the demo can be accepted.
   - The archived page is CC BY-NC, not public domain. `docs/book-plan.md:131-134` still describes the planned Capablanca demo as coming from a “well-known public-domain collection”, which conflicts with the owner decision and this design's correct CC BY-NC treatment.
   - The implementation README requirement should name the exact Caissabase release and subset, link both the archived source and the CC BY-NC license, credit Caissabase, state that the committed source and derived analyzed data are redistributed under the non-commercial term, and identify that the subset/analysis are modifications or derived data where applicable. This is required to make the Pages demo inspectable without falsely implying public-domain rights.
   - Reconcile `docs/book-plan.md` and the implementation design/README contract in this change, or explicitly record why the old “public-domain” sentence is no longer applicable. Do not substitute another source without the owner decision required by `ROADMAP.md:124-129`.

The design is not ready for implementation until the blocking findings are resolved and a new review is requested.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
BLOCK

## Review 002

- **Revision covered:** the current worktree design revision: committed `HEAD` `241143e12ef9e81584cfb4ac3d2b700305db0865` plus the uncommitted design and its shaping-record edits. There is still no commit containing this design.
- **Target proof:** `git rev-parse HEAD` and `git merge-base main HEAD` both give `241143e12ef9e81584cfb4ac3d2b700305db0865`; `git diff --name-only main...HEAD` is empty because the target is uncommitted; `git status --short --branch` shows `PLAN.md`, `ROADMAP.md` and `docs/book-plan.md` modified, `design/001-f13-book-around-games.md` untracked, and an unrelated `scripts/update_games.sh` worktree change. The reviewed design revision consists of the design and the three shaping-record edits; the unrelated script change is outside this review.
- **Files checked:** `design/001-f13-book-around-games.md`, `PLAN.md`, `ROADMAP.md`, `docs/book-plan.md`, `PRINCIPLES.md`, `AGENTS.md`, `CLAUDE.md`, `design/README.md`, `reviews/README.md`, `pgn_postmortem/site.py`, `pgn_postmortem/collection.py`, `pgn_postmortem/cli.py`, `.github/workflows/pages.yml`, `tests/test_site.py`, `tests/test_demo.py`, `README.md` and the archived Caissabase page at the URL named in the design. The tracked files were read from the current worktree and their changes inspected with `git diff`; the untracked design was read directly.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context OpenCode reviewer.
- **Mode:** OpenCode, design re-review.
- **Checks run:** read-only inspection of the revised design, Review 001, governing records, cited source and tests; `git` target-proof and diff checks; and a read-only fetch of the archived Caissabase page. The archive confirms the `2024-04-27` release, the Caissabase download, the statement that chess moves are facts, and the `Attribution-NonCommercial CC BY-NC` link.

### Review 001 findings

1. **Resolved.** The design now gives formulas and normalization for the primary selection measures, missing-rating and both-sides-player behavior, the early-blunder penalty, presumed-result classification, default scores, tie key, and wins-then-losses-then-draws allocation (`design/001-f13-book-around-games.md:62-97`). The remaining precision gaps in that contract are recorded as Finding 1 below.
2. **Partially resolved.** The design now makes notable games exactly the selected chapter games and adds opponent/repertoire tie rules and peak WhiteElo/BlackElo fields (`design/001-f13-book-around-games.md:103-110`). The career aggregation and the promised repertoire scores are still incomplete; see Finding 2.
3. **Resolved.** The owner decision is now explicit: the five-game F-12 root Pages demo and unchanged `/markdown/` demo remain, while Capablanca is a separate local `examples/book_demo/` demo; Capablanca files are not sent through `scripts/publish_games.py` (`design/001-f13-book-around-games.md:136-159`, `ROADMAP.md:124-133`).
4. **Resolved.** The revised matrix states the no-player, no-analysis, mixed, empty, chapter-omission and generated-stale-page behavior, including preservation of user-authored files (`design/001-f13-book-around-games.md:123-131`), and names tests for those cases (`design/001-f13-book-around-games.md:169-170`).
5. **Resolved.** The done-when now requires history and `--no-history` coverage for the new root and chapter pages, including links and relative paths (`design/001-f13-book-around-games.md:132-134`, `171-174`).
6. **Partially resolved.** `docs/book-plan.md` no longer calls the source public domain and the owner record names Caissabase and CC BY-NC (`docs/book-plan.md:131-136`, `ROADMAP.md:124-133`). The implementation README requirement still lacks two exact documentation obligations; see Finding 3.

### What holds

- The F-12 boundary is consistent with the existing workflow and five-game assertions: the workflow still reads `examples/site/analyzed/` and `tests/test_demo.py` still asserts five games (`.github/workflows/pages.yml:48-51`, `tests/test_demo.py:29-35`).
- The stale-page and no-history requirements are grounded in the existing generator marker and wrapper behavior (`pgn_postmortem/site.py:790-817`, `1421-1426`, `1429-1527`), rather than introducing a conflicting cleanup or history model.
- The archived-source treatment is factually correct. The fetched page says `2024-04-27`, describes chess moves as facts, and links the CC BY-NC license; neither the revised design nor `docs/book-plan.md` calls it public domain.

### Findings

1. **blocking** — The selection API and several derived signals are still not an exact, reviewable contract.
   - `design/001-f13-book-around-games.md:52-87` names `SelectionWeights` and `SelectionOptions`, but does not enumerate their public fields, field types, whether weights must be finite/non-negative or sum to one, or the validation and error behavior for `chapter_size` and `minimum_length`. The CLI flags at `design/001-f13-book-around-games.md:82-85` likewise have no type/range contract. A builder can therefore implement different accepted option values while satisfying the design.
   - The contract defines `opponent_accuracy` at `design/001-f13-book-around-games.md:63-65`, but none of the three default equations at `design/001-f13-book-around-games.md:74-80` uses it and no corresponding `SelectionWeights` field is named. That is an unresolved choice between a required signal, a deliberately unused diagnostic, or an omitted measure.
   - `design/001-f13-book-around-games.md:70-72` says comeback and draw-save are the largest improvement after the player was below 40%, but does not state whether winning-chance percentage points are divided by 100, which position transition is sampled, whether opponent moves count, or how the draw-specific value differs from the general comeback value. The statement that all values are clamped to `0..1` does not resolve those cases.
   - Before implementation, specify the dataclass fields and exact option validation, resolve opponent accuracy's role, and define the comeback/draw-save transition and normalization. The fixture assertions at `design/001-f13-book-around-games.md:163-168` should name expected component values or scores, not only ranking outcomes, so a passing test would catch each of these wrong implementations.

2. **blocking** — The career article's aggregation contract still omits required behavior and contradicts the book plan on repertoire scores.
   - `design/001-f13-book-around-games.md:103-108` says “active years (valid years only)” and “yearly totals” but does not state the exact date parser/invalid-year rule for those totals, nor whether each yearly row is total games or is split by shown result. It says “frequent opponents” and gives tie ordering, but does not say whether all opponents or a fixed top set is rendered, or how a game in which both sides match the player is counted.
   - Peak ratings are listed only as “peak WhiteElo/BlackElo values when numeric headers exist” (`design/001-f13-book-around-games.md:105-106`), without specifying numeric parsing, invalid-header handling, or the missing-value output. Repertoire rows are described as counts by ECO/opening (`design/001-f13-book-around-games.md:106-108`), but `docs/book-plan.md:77-85` promises “repertoire with scores”; the design neither defines that score nor explicitly scopes it out with an owner decision.
   - The design must make these aggregation and missing-data rules explicit, including the score promised by the governing book plan or a recorded scope decision. The golden assertions at `design/001-f13-book-around-games.md:171-174` must make every promised field and missing case observable.

3. **blocking** — The CC BY-NC README requirement is not yet precise enough to guarantee stranger-readable attribution.
   - `design/001-f13-book-around-games.md:148-151` requires the README to identify the subset, link the archived snapshot, credit Caissabase and state the non-commercial term, but it does not require a direct link to the `Attribution-NonCommercial CC BY-NC` license itself. It also says only that “the committed data” is redistributed under the term; it does not require labeling the selected source subset and the Stockfish-19 depth-22 files as derived/analyzed data (or otherwise stating their modification/derivation status).
   - The archived source supplies the exact license URL, so this is a documentation-contract omission, not an unresolved source fact. Require both URLs and explicit source/derived-data wording in the implementation README acceptance criteria before implementation.

The F-12 scope, no-analysis/no-player/stale-page matrix, no-history coverage, and repository-wide public-domain correction are otherwise resolved. The design is not ready for implementation until the three blocking findings above are addressed and reviewed again.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
BLOCK

## Review 003

- **Revision covered:** the current worktree design revision: committed `HEAD` `241143e12ef9e81584cfb4ac3d2b700305db0865` plus the uncommitted design and its shaping-record edits. There is still no commit containing this design.
- **Target proof:** `git rev-parse HEAD` and `git merge-base main HEAD` both give `241143e12ef9e81584cfb4ac3d2b700305db0865`; `git diff --name-only main...HEAD` is empty because the target is uncommitted; `git status --short --branch` shows `PLAN.md`, `ROADMAP.md` and `docs/book-plan.md` modified, `design/001-f13-book-around-games.md` untracked, and an unrelated `scripts/update_games.sh` worktree change. The reviewed design revision consists of the design and the three shaping-record edits; the unrelated script change is outside this review.
- **Files checked:** `design/001-f13-book-around-games.md`, `PLAN.md`, `ROADMAP.md`, `docs/book-plan.md`, `PRINCIPLES.md`, `AGENTS.md`, `CLAUDE.md`, `design/README.md`, `reviews/README.md`, `pgn_postmortem/site.py`, `pgn_postmortem/collection.py`, `pgn_postmortem/cli.py`, `.github/workflows/pages.yml`, `tests/test_site.py`, `tests/test_demo.py`, `README.md` and the archived Caissabase page at the URL named in the design. The tracked files were read from the current worktree and their changes inspected with `git diff`; the untracked design was read directly.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context OpenCode reviewer.
- **Mode:** OpenCode, design re-review.
- **Checks run:** read-only inspection of the current design, Reviews 001–002, governing records, cited source and tests; `git` target-proof and diff checks; and a read-only fetch of the archived Caissabase page. The archive again confirms the `2024-04-27` release, the Caissabase download, and the archived `Attribution-NonCommercial CC BY-NC` link.

### What holds

- The career contract now covers valid years through `date_parts`, four shown-result counts at career and yearly levels, top-ten opponent aggregation and tie order, both-sides-player exclusion, ASCII integer rating parsing and omission, side-specific peaks, ECO/opening grouping, the repertoire score, missing headers, and notable games as exactly the selected chapter games (`design/001-f13-book-around-games.md:110-124`). The corresponding assertions are required (`design/001-f13-book-around-games.md:188-191`).
- The README contract now requires the exact `2024-04-27` subset, the archived source URL, the direct CC BY-NC 4.0 URL, Caissabase credit, the non-commercial condition, and explicit source-subset versus Stockfish depth-22 derived/analyzed-data wording (`design/001-f13-book-around-games.md:152-170`, `202-205`). This resolves Review 002 Finding 3 as a design requirement; the implementation has not yet begun.
- The earlier F-12 boundary remains intact: the five-game root Pages demo and `/markdown/` demo stay unchanged, the Capablanca data is a separate local demo, and it is not sent through `scripts/publish_games.py` (`design/001-f13-book-around-games.md:152-176`, `ROADMAP.md:124-133`, `.github/workflows/pages.yml:48-75`, `tests/test_demo.py:29-35`). The no-player/no-analysis/mixed/empty and stale-page matrix remains specified, including user-authored-file preservation (`design/001-f13-book-around-games.md:137-148`), and history/no-history coverage remains required for root and chapter pages (`design/001-f13-book-around-games.md:146-148`, `192-197`). The repository-wide public-domain wording correction also remains present (`docs/book-plan.md:131-136`).

### Findings

1. **blocking** — The selection API and feature contract is still not complete enough to implement and review deterministically.
   - `design/001-f13-book-around-games.md:84-92` gives the seven `ChapterWeights` names indirectly through “the seven feature fields above”, names the three `SelectionWeights` fields, and validates finite non-negative values, per-chapter sums and positive integer options. However, `SelectionOptions` has no stated weights field, and `build_site` is only said to accept `selection_options`; the design never specifies whether `SelectionWeights` is passed through `SelectionOptions`, as a separate builder/selector argument, or via a default object. “Weights are an API option” does not define that public signature or the default `SelectionWeights` construction.
   - `design/001-f13-book-around-games.md:62-74` now includes `opponent_accuracy` in all three default equations, so Review 002's stale “unused opponent accuracy” subfinding is resolved. The remaining feature semantics are not exact: `mean(player_move_loss)` and its opponent analogue do not say whether the mean includes every mainline move with zero loss or only graded/critical `MoveReview` values, and no rule defines the empty/no-transition cases for the means, early-blunder maximum or recovery maximum. These choices change component values and chapter rankings while remaining compatible with the current prose.
   - Add the exact public field/signature contract, including where weights are supplied and their defaults, and specify the missing-data/empty-set behavior for every feature. Keep the required component-value and weighted-score assertions (`design/001-f13-book-around-games.md:180-187`) tied to those rules so a wrong implementation cannot pass on ranking outcomes alone.

The career aggregation, README licensing/derivation wording, F-12 scope, no-analysis/no-player matrix, stale-page cleanup, no-history requirement, and public-domain correction are otherwise resolved. The design is not ready for implementation while Finding 1 remains.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
BLOCK

## Review 004

- **Revision covered:** the current worktree design revision: committed `HEAD` `241143e12ef9e81584cfb4ac3d2b700305db0865` plus the uncommitted design and its shaping-record edits. There is still no commit containing this design.
- **Target proof:** `git rev-parse HEAD` and `git merge-base main HEAD` both give `241143e12ef9e81584cfb4ac3d2b700305db0865`; `git diff --name-only main...HEAD` is empty because the target is uncommitted; `git status --short --branch` shows `PLAN.md`, `ROADMAP.md` and `docs/book-plan.md` modified, `design/001-f13-book-around-games.md` untracked, and an unrelated `scripts/update_games.sh` worktree change. The reviewed design revision consists of the design and the three shaping-record edits; the unrelated script change is outside this review.
- **Files checked:** `design/001-f13-book-around-games.md`, `PLAN.md`, `ROADMAP.md`, `docs/book-plan.md`, `PRINCIPLES.md`, `AGENTS.md`, `CLAUDE.md`, `design/README.md`, `reviews/README.md`, `pgn_postmortem/site.py`, `pgn_postmortem/collection.py`, `pgn_postmortem/cli.py`, `.github/workflows/pages.yml`, `tests/test_site.py`, `tests/test_demo.py` and `README.md`. The tracked files were read from the current worktree and their changes inspected with `git diff`; the untracked design was read directly. An independent fresh-context review was also obtained from `GPT-5.6 Luna (opencode/gpt-5.6-luna#high)` without editing files.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context OpenCode reviewer.
- **Mode:** OpenCode, design re-review.
- **Checks run:** read-only inspection of the amended design, Reviews 001–003, governing records, cited source and tests; `git` target-proof and diff checks; and verification of the option forwarding point in `Collection.build_site` and the existing `MoveReview`/`review_moves` semantics in `pgn_postmortem/site.py`.

### Review 003 finding

1. **Partially resolved.** The owner amendment now binds the public options and defaults: frozen `ChapterWeights`/`SelectionWeights`, frozen `SelectionOptions.weights`, the listed default weights, `SelectionOptions(weights=...)` custom binding, `build_site(selection_options=None)` default construction, CLI integer options, validation, and empty-feature values are explicit (`design/001-f13-book-around-games.md:88-107`). The collection wrapper already forwards keyword options to `build_site` (`pgn_postmortem/collection.py:393-400`). The remaining feature-domain ambiguity is a blocking finding below.

### What holds

- The selection formulas, normalization, missing-rating behavior, both-sides-player behavior, recovery transition rule, presumed-result classification, allocation order, and complete tie key remain explicit (`design/001-f13-book-around-games.md:66-78`, `114-119`).
- The career contract remains complete for valid years, split result counts, opponent aggregation and tie order, numeric side-specific rating peaks, repertoire counts and scores, missing headers, and notable games as exactly the selected games (`design/001-f13-book-around-games.md:125-139`).
- The F-12 boundary remains consistent: the five-game root Pages demo and `/markdown/` demo stay unchanged, while Capablanca is a separate local demo not sent through `scripts/publish_games.py` (`design/001-f13-book-around-games.md:167-191`, `ROADMAP.md:124-133`, `.github/workflows/pages.yml:48-75`).
- The no-player, no-analysis, mixed, empty and stale-page matrix still specifies career/chapter omission and preservation of user-authored files, and `--no-history` coverage and relative links are required (`design/001-f13-book-around-games.md:152-163`, `207-220`).
- The source treatment is correct and stranger-readable: the exact Caissabase release, archived source, direct CC BY-NC 4.0 license, attribution, non-commercial condition, and derived/analyzed Stockfish data are required (`design/001-f13-book-around-games.md:172-185`, `217-220`). The repository-wide plan no longer calls the source public domain (`docs/book-plan.md:131-136`).

### Findings

1. **blocking** — The accuracy feature's aggregation domain and partial-analysis behavior are still unspecified.
   - `design/001-f13-book-around-games.md:66-68` defines `player_accuracy` and `opponent_accuracy` as `1 - mean(..._move_loss) / 100`, but does not state whether the mean includes every mainline `MoveReview.loss` value, including zero-loss moves, or only graded/critical moves. This is material: `review_moves` creates a `MoveReview` for every mainline move (`pgn_postmortem/site.py:317-354`), while `Article.moments` is a critical-move subset, and `MoveReview.loss` returns `0.0` when either evaluation is absent (`pgn_postmortem/site.py:258-263`).
   - `design/001-f13-book-around-games.md:78` and `102-107` distinguish an unanalyzed game from an analyzed eligible game with empty feature inputs, but do not define a marker-only or partially evaluated game. `is_analyzed` currently means only that the analysis marker header exists (`pgn_postmortem/site.py:266-268`); a marked game can therefore have no evaluated transitions while still being treated as analyzed unless the design says whether missing evaluations contribute zero loss, make the game ineligible, or use another rule.
   - Specify the exact iterable/domain for both accuracy means and the treatment of missing evaluations in a marked or partial analysis. Add direct fixture assertions for those cases, as required by the component-feature verification (`design/001-f13-book-around-games.md:198-202`). Without this, the hard-fought-loss and default-score tests can pass while different implementations select different chapters.

The amendment resolves the public option binding and empty-feature portion of Review 003, and all earlier career, licensing, F-12 boundary, collection-state, stale-cleanup, history and public-domain findings remain resolved. The design is not ready for implementation while the accuracy/partial-analysis contract remains open.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
BLOCK

## Review 005

- **Revision covered:** the current worktree design revision: committed `HEAD` `241143e12ef9e81584cfb4ac3d2b700305db0865` plus the uncommitted design and its shaping-record edits. There is still no commit containing this design.
- **Target proof:** `git rev-parse HEAD` and `git merge-base main HEAD` both gave `241143e12ef9e81584cfb4ac3d2b700305db0865`; `git diff --name-only main...HEAD` was empty because the design and shaping edits are uncommitted; `git status --short --branch` showed modified `PLAN.md`, `ROADMAP.md` and `docs/book-plan.md`, untracked `design/001-f13-book-around-games.md`, and unrelated `scripts/update_games.sh`. The unrelated script change is outside this review.
- **Files checked:** `design/001-f13-book-around-games.md`, Reviews 001–004 in this record, `PRINCIPLES.md`, `AGENTS.md`, `CLAUDE.md`, `design/README.md`, `reviews/README.md`, `PLAN.md`, `ROADMAP.md`, `docs/book-plan.md`, `pgn_postmortem/site.py`, `pgn_postmortem/collection.py`, `pgn_postmortem/cli.py`, `.github/workflows/pages.yml`, `tests/test_site.py` and `tests/test_demo.py`. The design and worktree files were read directly; the committed source and test files were checked from the current worktree, and the target was proven with the commands above.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context OpenCode reviewer.
- **Mode:** OpenCode, design re-review.
- **Checks run:** read-only inspection of the amended design, Reviews 001–004, governing records, cited source, tests and workflow; independent fresh-context assessment; and the target-proof `git` commands above. No implementation or engine run was performed.

### Review 004 finding

1. **Resolved.** The amended selection contract now requires the analysis marker and an evaluation after every non-terminal mainline move, explicitly excludes marker-only and partially evaluated games, and states that accuracy means include every `MoveReview` entry for the relevant mover whose `before` and `after` values are present (`design/001-f13-book-around-games.md:70-77`). This includes qualifying zero-loss entries and excludes entries with missing evaluations; an eligible game's empty mover-specific domain has the separately specified `0.5` fallback (`design/001-f13-book-around-games.md:87-89`, `114-119`). The fixture requirements also require direct component-feature assertions (`design/001-f13-book-around-games.md:207-214`).

### What holds

- The selection API, default and custom weight binding, validation, normalized feature formulas, empty-feature values, presumed-result classification, minimum length, chapter limits, complete tie key and wins-then-losses-then-draws allocation remain explicit (`design/001-f13-book-around-games.md:70-131`).
- The career contract remains deterministic and complete for names, valid years, four result counts, yearly splits, opponent aggregation, rating parsing and side-specific peaks, repertoire counts and scores, missing headers, and notable games as exactly the selected chapter games (`design/001-f13-book-around-games.md:133-151`).
- The generated-page contract preserves the existing wrapper and relative links, defines marker-only stale cleanup, and specifies no-player, no-analysis, mixed, empty and user-authored-file behavior plus history and no-history output (`design/001-f13-book-around-games.md:158-175`).
- The separate Capablanca demo remains outside the validated F-12 root and Markdown demos and outside `scripts/publish_games.py`; the source release, archived URL, direct CC BY-NC 4.0 license, attribution, non-commercial condition and derived Stockfish data wording remain required (`design/001-f13-book-around-games.md:177-203`).
- The done-when contract covers the required fixture, career, stale-page, golden/link, history, demo, licensing, lint and test evidence, with the owner's final read of the demo picks explicitly required before merge (`design/001-f13-book-around-games.md:205-236`).

No blocking finding remains.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
AGREE

## Review 006

- **Revision covered:** the current worktree source amendment: committed `HEAD` `3b59488130514d1fe1f11eac722718832d1ebb35` plus the uncommitted `README.md`, `ROADMAP.md` and this design record. No commit contains this amendment. The uncommitted F-1.3 implementation files are outside this design-source review.
- **Target proof:** `git rev-parse HEAD` gave `3b59488130514d1fe1f11eac722718832d1ebb35`; `git merge-base main HEAD` gave `241143e12ef9e81584cfb4ac3d2b700305db0865`; `git diff --name-only HEAD -- README.md ROADMAP.md design/001-f13-book-around-games.md` listed exactly those three amendment files. `git diff --quiet HEAD -- .github/workflows/pages.yml scripts/publish_games.py examples/docs` confirmed no F-12 workflow, Markdown-pipeline script or generated Markdown-output change in the source amendment. The worktree also contains uncommitted implementation files and a mode-only change to `scripts/update_games.sh`; those are outside this review.
- **Files checked:** `design/001-f13-book-around-games.md`, `README.md`, `ROADMAP.md`, `docs/book-plan.md`, `PLAN.md`, `PRINCIPLES.md`, `AGENTS.md`, `CLAUDE.md`, `design/README.md`, `reviews/README.md`, `.github/workflows/pages.yml`, `scripts/update_games.sh`, `scripts/publish_games.py`, `examples/book_demo/source/capablanca.pgn`, `tests/test_demo.py` and `tests/test_publish.py`. The amendment file list was obtained from the local diff from `HEAD`; the remaining files were read as governing and boundary context.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context OpenCode reviewer.
- **Mode:** OpenCode, design re-review.
- **Checks run:** read-only inspection of the current amendment and Reviews 001–005; target-proof and boundary `git` checks; a read-only fetch of PGN Mentor's downloads page, which identifies Capablanca's 597 games and says the PGN files are available completely free; a read-only fetch of the archived Caissabase page, which identifies the `2024-04-27` release and its 630 MB link; and a read-only fetch of that archived download URL, which returned HTTP 404. No implementation, test suite or Stockfish run was performed.

### Owner decision and source verification

- **Verified.** The owner decision is now recorded in `ROADMAP.md:124-135` and at the top of this design: the unavailable archived Caissabase download is not substituted silently; the five-game PGN Mentor Capablanca subset is the fallback, its downloads page says the files are free to download, and no separate open-source license is claimed. The checked-in source contains the five intended games: the 1906 Raubitschek game and the 1909 Marshall rounds 1, 2, 5 and 6 (`examples/book_demo/source/capablanca.pgn:1-64`).

### What holds

- The separate-demo boundary remains explicit in the design (`design/001-f13-book-around-games.md:184-207`) and the owner record (`ROADMAP.md:128-135`). The Pages workflow still builds the five classic games from `examples/site/analyzed/` at the root and stages the unchanged Markdown output at `/markdown/` (`.github/workflows/pages.yml:48-76`); the source amendment does not alter that workflow, `scripts/publish_games.py` or `examples/docs/**`.
- The prior F-1.3 contracts remain materially unchanged in the amendment: the exact selection features, eligibility, defaults, options and allocation rules (`design/001-f13-book-around-games.md:75-136`); career aggregation and notable-game rules (`design/001-f13-book-around-games.md:142-156`); generated-page, stale-cleanup, collection-state and history rules (`design/001-f13-book-around-games.md:163-180`); and the required fixture, golden, link, demo and gate evidence (`design/001-f13-book-around-games.md:211-240`).

### Findings

1. **blocking** — The amended design still carries the superseded Caissabase README acceptance contract and labels the fallback source inconsistently.
   - The new source section correctly names PGN Mentor at `design/001-f13-book-around-games.md:189-200`, but line 189 still says “The source is the archived Caissabase page” immediately before the PGN Mentor URL. More importantly, the done-when at `design/001-f13-book-around-games.md:233-236` still requires the exact `2024-04-27` subset, the archived source, a direct CC BY-NC 4.0 link, Caissabase credit and the non-commercial term. Those requirements contradict the owner decision at `design/001-f13-book-around-games.md:13-16`, the corrected source terms at `design/001-f13-book-around-games.md:194-200`, and the current fallback README at `README.md:172-181`.
   - Replace the acceptance contract with the verified PGN Mentor terms: identify the exact five checked-in games (the 1906 Raubitschek game and Marshall rounds 1, 2, 5 and 6 from 1909), link both the Capablanca collection download and PGN Mentor's downloads page, state that the page says “available for download, completely free,” and state that no separate open-source license is published or claimed. If “non-commercial demo only” remains in the README, label it as this repository's distribution policy rather than as a PGN Mentor source term. The acceptance text must also label the Stockfish 19 depth-22 files as derived/analyzed data, as already required at `design/001-f13-book-around-games.md:197-199`.

2. **blocking** — The repository's shaping document still records the old source and license for F-1.3.
   - `docs/book-plan.md:133-136` says that the F-1.3 demo uses the archived Caissabase 2024-04-27 release, requires attribution under its non-commercial terms, and is changed only by a later owner decision. The owner has now made that decision in `ROADMAP.md:128-135`; the current text therefore contradicts the design amendment and the README's PGN Mentor/no-license contract. Reconcile this source-of-truth sentence before approval, while retaining the separate F-12 five-game site and unchanged `/markdown/` boundary.

The fallback decision, its unavailable Caissabase reason, the F-12 separation, the Markdown-pipeline exclusion and the prior F-1.3 behavioral contracts are otherwise verified. The design is not ready for approval while the stale README acceptance and shaping-record source terms remain.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
BLOCK

## Review 007

- **Revision covered:** the current worktree source amendment: committed `HEAD` `3b59488130514d1fe1f11eac722718832d1ebb35` plus the uncommitted `README.md`, `ROADMAP.md`, `docs/book-plan.md` and this design record. No commit contains this amendment. The uncommitted F-1.3 implementation files are outside this design-source review.
- **Target proof:** `git rev-parse HEAD` gave `3b59488130514d1fe1f11eac722718832d1ebb35`; `git merge-base main HEAD` gave `241143e12ef9e81584cfb4ac3d2b700305db0865`; `git diff --name-only HEAD -- README.md ROADMAP.md docs/book-plan.md design/001-f13-book-around-games.md` listed exactly those four amendment files. `git diff --quiet HEAD -- .github/workflows/pages.yml scripts/publish_games.py examples/docs` exited 0, confirming no F-12 workflow, Markdown-pipeline script or generated Markdown-output change in the source amendment. The worktree also contains uncommitted F-1.3 implementation files and a mode-only `scripts/update_games.sh` change; those are outside this review.
- **Files checked:** `design/001-f13-book-around-games.md`, `README.md`, `ROADMAP.md`, `docs/book-plan.md`, `PRINCIPLES.md`, `AGENTS.md`, `CLAUDE.md`, `design/README.md`, `reviews/README.md`, `.github/workflows/pages.yml`, `scripts/publish_games.py`, `examples/book_demo/source/capablanca.pgn` and `tests/test_demo.py`. The amendment file list was obtained from the local diff from `HEAD`; the remaining files were read as governing and boundary context.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context OpenCode reviewer.
- **Mode:** OpenCode, design re-review.
- **Checks run:** read-only inspection of the current amendment and Reviews 001–006; target-proof and boundary `git` checks; a read-only fetch of PGN Mentor's downloads page, which says “The files below are available for download, completely free” and lists José Raúl Capablanca's collection as 597 games; and inspection of all five checked-in PGN headers. No implementation, test suite or Stockfish run was performed.

### Review 006 findings

1. **Resolved.** The active source amendment no longer uses Caissabase or CC BY-NC as the demo's acceptance terms. Its active F-1.3 source contract names PGN Mentor's Capablanca collection, the collection download, the free-download wording, the absence of a separate open-source license, and Stockfish output as derived/analyzed data (`design/001-f13-book-around-games.md:182-201`). `docs/book-plan.md` now states the same PGN Mentor/no-license terms (`docs/book-plan.md:131-137`). The historical Review 001–006 entries retain prior review evidence and findings as required by the canonical record; they are not active acceptance requirements.
2. **Partially resolved.** The amended design acceptance requirement names the exact intended subset, and the current source contains it: the 1906 Raubitschek game plus Marshall rounds 1, 2, 5 and 6 from 1909 (`design/001-f13-book-around-games.md:229-238`, `examples/book_demo/source/capablanca.pgn:1-64`). The PGN Mentor collection/download links and the free-download/no-license claims in the README are accurate (`README.md:172-181`, `design/001-f13-book-around-games.md:192-198`), but the README itself does not yet spell out the five games or label its non-commercial phrase as repository policy; see the blocking finding below.
3. **Resolved.** The separate-demo boundary remains intact. The F-12 workflow still builds the five classic root games from `examples/site/analyzed/`, the `/markdown/` staging remains unchanged, and Capablanca is not sent through `scripts/publish_games.py` (`.github/workflows/pages.yml:48-76`, `tests/test_demo.py:1-35`). The prior F-1.3 selection, career, generated-page, stale-cleanup, collection-state, history and verification contracts remain unchanged in the active design (`design/001-f13-book-around-games.md:75-180`, `209-242`).

### Finding

1. **blocking** — The actual README still does not satisfy the exact-subset and policy-label requirement that the amended design now makes part of the acceptance contract.
   - `README.md:174-181` calls this a “five-game Capablanca subset” but does not name the 1906 Raubitschek game or Marshall rounds 1, 2, 5 and 6 from 1909. The exact names appear only in the design's future acceptance assertion (`design/001-f13-book-around-games.md:233-238`), so the stranger-readable source documentation is not yet self-verifying.
   - The same README paragraph says the derived files are “included for the non-commercial demo only” (`README.md:178-180`) without identifying that as this repository's distribution policy. After the source-license correction, that phrase must not be readable as a PGN Mentor restriction. State explicitly that it is this repository's demo distribution policy, separately from PGN Mentor's “completely free” statement and absence of a published open-source license.
   - Update the README acceptance text/documentation, then re-review this source amendment. The required wording must retain both PGN Mentor links, the exact five-game list, the free-download statement, the no-license claim, and the derived/analyzed Stockfish 19 depth-22 label.

The stale Caissabase/CC BY-NC acceptance text is removed from the active amendment and `docs/book-plan.md`; the remaining historical references are preserved review history, not current terms. The F-1.3, F-12 and Markdown contracts otherwise remain intact, but the README documentation mismatch is blocking.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
BLOCK

## Review 008

- **Revision covered:** the current worktree source amendment: committed `HEAD` `3b59488130514d1fe1f11eac722718832d1ebb35` plus the uncommitted `README.md`, `ROADMAP.md`, `docs/book-plan.md` and this design record. No commit contains this amendment. The uncommitted F-1.3 implementation files and the mode-only `scripts/update_games.sh` change are outside this design-source review.
- **Target proof:** `git rev-parse HEAD` gave `3b59488130514d1fe1f11eac722718832d1ebb35`; `git merge-base main HEAD` gave `241143e12ef9e81584cfb4ac3d2b700305db0865`; `git diff --name-only HEAD -- README.md ROADMAP.md docs/book-plan.md design/001-f13-book-around-games.md` listed exactly those four amendment files. `git diff --quiet HEAD -- .github/workflows/pages.yml scripts/publish_games.py examples/docs` exited 0, confirming no F-12 workflow, Markdown-pipeline script or generated Markdown-output change in the source amendment.
- **Files checked:** `design/001-f13-book-around-games.md`, `README.md`, `ROADMAP.md`, `docs/book-plan.md`, `PRINCIPLES.md`, `AGENTS.md`, `CLAUDE.md`, `design/README.md`, `reviews/README.md`, `.github/workflows/pages.yml`, `scripts/publish_games.py`, `examples/book_demo/source/capablanca.pgn` and `tests/test_demo.py`. The amendment file list was obtained from the local diff from `HEAD`; the remaining files were read as governing, source and boundary context.
- **Reviewer:** GPT-5.6 Luna (`opencode/gpt-5.6-luna#high`), fresh-context OpenCode reviewer.
- **Mode:** OpenCode, design re-review.
- **Checks run:** read-only inspection of the current amendment and Reviews 001–007; target-proof and boundary `git` checks; a read-only fetch of PGN Mentor's downloads page, which says “The files below are available for download, completely free” and lists José Raúl Capablanca's collection as 597 games; inspection of all five checked-in PGN headers; and a read-only fetch of the Capablanca collection download. No implementation, test suite or Stockfish run was performed.

### Review 007 finding

1. **Resolved.** `README.md:172-182` now names the exact five checked-in games: the 1906 Raubitschek game and Marshall rounds 1, 2, 5 and 6 from 1909. It retains both PGN Mentor links, states the published “available for download completely free” wording, says that PGN Mentor publishes no separate open-source license without claiming one, labels the Stockfish 19 depth-22 files as derived/analyzed data, and explicitly identifies non-commercial use as this repository's distribution policy rather than as a PGN Mentor term. The five PGN headers match that list (`examples/book_demo/source/capablanca.pgn:1-64`).

### What holds

- The active source terms are consistent across the design, README, roadmap and shaping document: PGN Mentor is the fallback source, its published free-download wording is recorded, no unsupported open-source license is claimed, and the unavailable Caissabase source remains historical owner-decision context (`design/001-f13-book-around-games.md:13-16`, `182-207`; `README.md:172-182`; `ROADMAP.md:124-135`; `docs/book-plan.md:131-137`).
- The prior F-1.3 contracts remain unchanged and reviewable: selection features, eligibility, defaults, options and allocation (`design/001-f13-book-around-games.md:75-136`); career aggregation and notable-game rules (`design/001-f13-book-around-games.md:142-156`); generated-page, stale-cleanup, collection-state and history behavior (`design/001-f13-book-around-games.md:163-180`); and the fixture, golden, link, demo and gate evidence (`design/001-f13-book-around-games.md:211-242`).
- The F-12 and Markdown boundaries remain intact. The Pages workflow still builds the five classic root games from `examples/site/analyzed/` and stages `examples/docs/` under `/markdown/` (`.github/workflows/pages.yml:48-76`); `tests/test_demo.py` still checks that root five-game contract (`tests/test_demo.py:1-35`); and the design keeps the Capablanca book in `examples/book_demo/` and excludes it from `scripts/publish_games.py` (`design/001-f13-book-around-games.md:184-207`). The boundary diff is clean, and no Stockfish or implementation run was needed for this source review.

No blocking finding remains.

— GPT-5.6 Luna (opencode/gpt-5.6-luna#high), reviewer
AGREE
