"""F-13 isolated collection workspaces."""

import json
from pathlib import Path

import pytest

from pgn_postmortem.cli import main
from pgn_postmortem.workspace import CollectionProfile, Workspace, WorkspaceConfigError

FIXTURE = Path(__file__).parent / "fixtures" / "site" / "games.pgn"


def manifest(tmp_path: Path, cache: Path | None = None) -> Path:
    cache_line = f'\nanalyzed_dir = "{cache.as_posix()}"' if cache else ""
    path = tmp_path / "collections.toml"
    path.write_text(
        f'''[[collection]]
slug = "otb"
title = "Over-the-board games"
inputs = ["{FIXTURE.as_posix()}"]{cache_line}
player = "Ada Example"
aliases = ["adaex", "Example, Ada"]
description = "OTB"

[[collection]]
slug = "correspondence"
title = "Correspondence games"
inputs = ["{FIXTURE.as_posix()}"]
player = "Ada Example"
aliases = ["adaex", "Example, Ada"]
description = "Correspondence"
''',
        encoding="utf-8",
    )
    return path


def test_workspace_api_and_manifest_cli_build_isolated_sites(tmp_path):
    config = manifest(tmp_path)
    workspace = Workspace.from_toml(config)
    report = workspace.build(tmp_path / "site", history=False)
    assert report.landing == tmp_path / "site" / "index.html"
    assert set(report.profiles) == {"otb", "correspondence"}
    assert all(path.is_relative_to(tmp_path / "site") for path in report.profiles["otb"].articles)
    root = (tmp_path / "site" / "index.html").read_text(encoding="utf-8")
    assert 'href="otb/index.html"' in root and 'href="correspondence/index.html"' in root
    assert (tmp_path / "site" / "otb" / "career.html").is_file()
    assert (tmp_path / "site" / "correspondence" / "career.html").is_file()
    assert 'href="../index.html"' in (tmp_path / "site" / "otb" / "index.html").read_text(encoding="utf-8")
    game = next((tmp_path / "site" / "otb" / "games").glob("*.html"))
    assert 'href="../../index.html"' in game.read_text(encoding="utf-8")
    saved = json.loads((tmp_path / "site" / ".pgn-postmortem-workspace.json").read_text(encoding="utf-8"))
    assert saved == {"format": 1, "generator": "pgn-postmortem workspace", "slugs": ["otb", "correspondence"]}
    assert main(["workspace", str(config), "--out", str(tmp_path / "cli-site"), "--no-history"]) == 0
    assert (tmp_path / "cli-site" / "otb" / "index.html").is_file()


def test_workspace_rejects_duplicate_or_unsafe_profiles_before_writing(tmp_path):
    out = tmp_path / "site"
    with pytest.raises(WorkspaceConfigError):
        Workspace(
            (CollectionProfile("otb", "OTB", (FIXTURE,)), CollectionProfile("otb", "Other", (FIXTURE,)))
        ).build(out)
    assert not out.exists()
    with pytest.raises(WorkspaceConfigError):
        Workspace((CollectionProfile("../outside", "Bad", (FIXTURE,)),)).build(out)
    assert not out.exists()
    with pytest.raises(WorkspaceConfigError):
        Workspace((CollectionProfile("index.html", "Bad", (FIXTURE,)),)).build(out)
    with pytest.raises(WorkspaceConfigError):
        Workspace((CollectionProfile("otb", "Bad", (FIXTURE,), analyzed_dir=out),)).build(out)
    assert not out.exists()


def test_workspace_does_not_modify_read_only_analysis_cache(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    source = cache / "games.pgn"
    source.write_bytes(FIXTURE.read_bytes())
    before = source.read_bytes()
    report = Workspace((CollectionProfile("otb", "OTB", (FIXTURE,), analyzed_dir=cache, player="Ada Example"),)).build(
        tmp_path / "site"
    )
    assert report.landing.is_file()
    assert source.read_bytes() == before


def test_workspace_removes_generated_removed_profile_but_keeps_authored_file(tmp_path):
    config = manifest(tmp_path)
    output = tmp_path / "site"
    Workspace.from_toml(config).build(output)
    authored = output / "correspondence" / "notes.txt"
    authored.write_text("keep", encoding="utf-8")
    one = Workspace((CollectionProfile("otb", "Over-the-board games", (FIXTURE,), player="Ada Example"),))
    one.build(output)
    assert not (output / "correspondence" / "index.html").exists()
    assert authored.read_text(encoding="utf-8") == "keep"


def test_untrusted_profile_marker_cannot_remove_authored_file(tmp_path):
    config = manifest(tmp_path)
    output = tmp_path / "site"
    Workspace.from_toml(config).build(output)
    authored = output / "correspondence" / "notes.txt"
    authored.write_text("keep", encoding="utf-8")
    marker = output / "correspondence" / ".pgn-postmortem-profile.json"
    marker.write_text(
        json.dumps({
            "format": 1,
            "generator": "pgn-postmortem workspace profile",
            "slug": "correspondence",
            "files": ["notes.txt"],
        }),
        encoding="utf-8",
    )
    one = Workspace((CollectionProfile("otb", "Over-the-board games", (FIXTURE,), player="Ada Example"),))
    one.build(output)
    assert authored.read_text(encoding="utf-8") == "keep"
