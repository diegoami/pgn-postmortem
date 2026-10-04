"""The documentation's examples run (ROADMAP F-15): every fenced block of the
README and of docs/result-correction.md whose info string says ``tested`` is
executed against the hand-written games in tests/fixtures/site/corrections/,
copied to ``analyzed/`` in a scratch directory (fresh for every block), so the
examples and the output they show cannot rot.

- ``console tested``: lines starting with ``$ `` are commands (``pgn-postmortem``
  runs as ``python -m pgn_postmortem``) that must exit 0; the lines after a
  command are expected output, and each must appear, in order, in its stdout.
- ``python tested``: the snippet is executed in the scratch directory.
- ``toml tested``: a workspace manifest, built into ``site/`` without error.
"""

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from pgn_postmortem import Collection
from pgn_postmortem.collection import format_game
from pgn_postmortem.workspace import Workspace

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "site" / "corrections"
DOCS = [REPO_ROOT / "docs" / "result-correction.md", REPO_ROOT / "README.md"]
FENCE = re.compile(r"^```(\w+) tested\n(.*?)^```$", re.S | re.M)
OPENING = re.compile(r"^```.*tested", re.I | re.M)  # any fence line that mentions "tested"
EXPECTED_BLOCKS = {"result-correction.md": 10, "README.md": 2}  # tested blocks per document, fixed on purpose


def blocks():
    for doc in DOCS:
        for number, match in enumerate(FENCE.finditer(doc.read_text(encoding="utf-8")), start=1):
            yield pytest.param(match.group(1), match.group(2), id=f"{doc.name}-{number}-{match.group(1)}")


def scratch(tmp_path: Path) -> None:
    out = tmp_path / "analyzed"
    out.mkdir()
    for item in Collection.read(FIXTURES, keep_analysis=True):
        (out / item.filename).write_text(format_game(item.game), encoding="utf-8")


def commands(text: str):
    """(command, expected output lines) for each ``$`` line of a console block."""
    current = None
    for line in text.splitlines():
        if line.startswith("$ "):
            if current:
                yield current
            current = (line[2:], [])
        elif current is not None:
            current[1].append(line)
    if current:
        yield current


def test_no_fence_that_says_tested_is_silently_dropped_and_the_counts_are_fixed():
    for doc in DOCS:
        text = doc.read_text(encoding="utf-8")
        assert len(OPENING.findall(text)) == len(FENCE.findall(text)), f"a malformed 'tested' fence in {doc.name}"
        assert len(FENCE.findall(text)) == EXPECTED_BLOCKS[doc.name], doc.name


def test_a_console_block_without_expected_output_is_rejected():
    for kind, text in FENCE.findall(DOCS[0].read_text(encoding="utf-8")):
        if kind == "console":
            assert any(expected for _, expected in commands(text)), text


def test_the_docs_have_tested_examples_of_every_kind():
    kinds = {kind for doc in DOCS for kind, _ in FENCE.findall(doc.read_text(encoding="utf-8"))}
    assert kinds == {"console", "python", "toml"}


@pytest.mark.parametrize(("kind", "text"), list(blocks()))
def test_the_documented_example_runs(tmp_path, monkeypatch, kind, text):
    scratch(tmp_path)
    monkeypatch.chdir(tmp_path)
    if kind == "console":
        env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        for command, expected in commands(text):
            words = shlex.split(command)
            assert words[0] == "pgn-postmortem", command
            run = subprocess.run(
                [sys.executable, "-m", "pgn_postmortem", *words[1:]],
                cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120,
            )  # fmt: skip
            assert run.returncode == 0, (command, run.stderr)
            lines = run.stdout.splitlines()
            position = 0
            for want in expected:
                assert want in lines[position:], (command, want, run.stdout)
                position = lines.index(want, position) + 1
    elif kind == "python":
        exec(compile(text, "<documented example>", "exec"), {})
    else:
        manifest = tmp_path / "collections.toml"
        manifest.write_text(text, encoding="utf-8")
        report = Workspace.from_toml(manifest).build(tmp_path / "workspace")
        assert report.corrections["otb"].policy
