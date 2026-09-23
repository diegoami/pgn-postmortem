"""Golden-file test: regenerating the bundled examples must reproduce the
committed examples/docs/ byte for byte. If an intentional output change
breaks this, regenerate with:

    .venv/bin/python scripts/publish_games.py --player '*' --data-dir examples --source analyzed_games
"""

import filecmp
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "examples"


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
