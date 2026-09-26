"""Golden-file test: regenerating the bundled examples must reproduce the
committed examples/docs/ byte for byte. If an intentional output change
breaks this, regenerate with:

    .venv/bin/python scripts/publish_games.py --player '*' --data-dir examples --source analyzed_games

Also the defect "The HTML is broken" on the Markdown demo (2026-09-26): the
Pages workflow renders examples/docs/ with Jekyll's kramdown and
parse_block_html, which reads a one-line <summary>...</summary> as a block,
misses its closing tag and prints "</summary>" and "</details>" on the page.
Every <summary> the generator writes must carry markdown="span". The gates
have no Ruby, so kramdown itself is not run here; the golden-file test ties
the committed pages to the generator, and the pages are checked directly.
"""

import filecmp
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "examples"

SPAN_SUMMARY_LINE = re.compile(r'<summary markdown="span">(.*)</summary>')


def assert_summaries_are_spans(docs: Path) -> int:
    """Every line of docs/**/*.md with a <summary> is exactly one element,
    opened with markdown="span" and closed on the same line. Returns how many
    there were."""
    found = 0
    for md in sorted(docs.rglob("*.md")):
        for number, line in enumerate(md.read_text(encoding="utf-8").splitlines(), start=1):
            if "<summary" not in line.lower():
                continue
            found += 1
            match = SPAN_SUMMARY_LINE.fullmatch(line)
            assert match and "summary" not in match.group(1).lower(), (
                f"{md.relative_to(docs)}:{number}: {line!r} is not a one-line "
                '<summary markdown="span">; kramdown would print its closing tags'
            )
    return found


def assert_same_tree(expected: Path, actual: Path) -> None:
    cmp = filecmp.dircmp(expected, actual)
    assert not cmp.left_only, f"missing in output: {cmp.left_only}"
    assert not cmp.right_only, f"unexpected in output: {cmp.right_only}"
    _, mismatch, errors = filecmp.cmpfiles(expected, actual, cmp.common_files, shallow=False)
    assert not mismatch and not errors, f"differs from committed examples: {mismatch or errors}"
    for sub in cmp.common_dirs:
        assert_same_tree(expected / sub, actual / sub)


def test_examples_regenerate_identically(tmp_path):
    shutil.copytree(EXAMPLES / "analyzed_games", tmp_path / "analyzed_games")
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "publish_games.py"),
            "--player",
            "*",
            "--data-dir",
            str(tmp_path),
            "--source",
            "analyzed_games",
        ],
        check=True,
        capture_output=True,
    )
    assert_same_tree(EXAMPLES / "docs", tmp_path / "docs")


def test_single_player_filter(tmp_path):
    shutil.copytree(EXAMPLES / "analyzed_games", tmp_path / "analyzed_games")
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "publish_games.py"),
            "--player",
            "magnus carlsen",
            "--data-dir",
            str(tmp_path),
            "--source",
            "analyzed_games",
        ],
        check=True,
        capture_output=True,
    )
    index = (tmp_path / "docs" / "index.md").read_text()
    assert index.startswith("# magnus carlsen's Games")
    # game 5: Carlsen (White) blundered on move 26, Anand (Black) on 26 and 32 - only White's are reported
    diagrams = sorted(p.name for p in (tmp_path / "docs" / "games" / "5").glob("*_move*.svg"))
    assert diagrams == ["blunder_1_move26w.svg"]
    assert "is not a player in this game" in (tmp_path / "docs" / "games" / "1.md").read_text()
    assert assert_summaries_are_spans(tmp_path / "docs") > 0


def test_every_summary_in_the_committed_examples_is_a_span():
    docs = EXAMPLES / "docs"
    assert assert_summaries_are_spans(docs) > 0
    # each game page folds its PGN under one, so none can be skipped silently
    for page in sorted((docs / "games").glob("*.md")):
        assert "<summary" in page.read_text(encoding="utf-8"), page.name


def test_summary_line_is_one_span_element():
    from publish_games import summary_line

    assert summary_line("Show movetext") == '<summary markdown="span">Show movetext</summary>'
    assert SPAN_SUMMARY_LINE.fullmatch(summary_line("Move 22... h4 by Wilhelm Steinitz (Inaccuracy)"))
