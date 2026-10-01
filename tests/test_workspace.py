"""F-13 isolated collection workspaces."""

import json
from pathlib import Path

import pytest

from pgn_postmortem.cli import main
from pgn_postmortem.workspace import CollectionProfile, Workspace, WorkspaceBuildError, WorkspaceConfigError

FIXTURE = Path(__file__).parent / "fixtures" / "site" / "games.pgn"


def manifest(tmp_path: Path, cache: Path | None = None, second_input: Path = FIXTURE) -> Path:
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
inputs = ["{second_input.as_posix()}"]
player = "Ada Example"
aliases = ["adaex", "Example, Ada"]
description = "Correspondence"
''',
        encoding="utf-8",
    )
    return path


def test_workspace_api_and_manifest_cli_build_isolated_sites(tmp_path):
    config = manifest(tmp_path, second_input=Path(__file__).parent / "fixtures" / "site" / "odd.pgn")
    workspace = Workspace.from_toml(config)
    report = workspace.build(tmp_path / "site", history=False)
    assert report.landing == tmp_path / "site" / "index.html"
    assert set(report.profiles) == {"otb", "correspondence"}
    assert all(path.is_relative_to(tmp_path / "site") for path in report.profiles["otb"].articles)
    root = (tmp_path / "site" / "index.html").read_text(encoding="utf-8")
    assert 'href="otb/index.html"' in root and 'href="correspondence/index.html"' in root
    assert (tmp_path / "site" / "otb" / "career.html").is_file()
    assert (tmp_path / "site" / "correspondence" / "career.html").is_file()
    assert len(report.profiles["otb"].articles) == 6
    assert len(report.profiles["correspondence"].articles) == 2
    assert 'href="../index.html"' in (tmp_path / "site" / "otb" / "index.html").read_text(encoding="utf-8")
    game = next((tmp_path / "site" / "otb" / "games").glob("*.html"))
    assert 'href="../../index.html"' in game.read_text(encoding="utf-8")
    saved = json.loads((tmp_path / "site" / ".pgn-postmortem-workspace.json").read_text(encoding="utf-8"))
    assert saved == {"format": 1, "generator": "pgn-postmortem workspace", "slugs": ["otb", "correspondence"]}
    assert main(["workspace", str(config), "--out", str(tmp_path / "cli-site"), "--no-history"]) == 0
    assert (tmp_path / "cli-site" / "otb" / "index.html").is_file()
    assert (tmp_path / "site" / "index.html").read_bytes() == (tmp_path / "cli-site" / "index.html").read_bytes()
    assert (tmp_path / "site" / "otb" / "index.html").read_bytes() == (
        tmp_path / "cli-site" / "otb" / "index.html"
    ).read_bytes()
    assert (tmp_path / "site" / "otb" / "assets" / "style.css").is_file()
    assert (tmp_path / "site" / "otb" / "career.html").read_text(encoding="utf-8").find("<script") == -1
    assert (tmp_path / "cli-site" / "otb" / "career.html").read_text(encoding="utf-8").find("<script") == -1


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


def test_profiles_keep_overlap_but_have_profile_specific_games(tmp_path):
    odd = Path(__file__).parent / "fixtures" / "site" / "odd.pgn"
    first = CollectionProfile("otb", "OTB", (FIXTURE,), player="Ada Example")
    second = CollectionProfile("correspondence", "Correspondence", (FIXTURE, odd), player="Ada Example")
    report = Workspace((first, second)).build(tmp_path / "site")
    assert len(report.profiles["correspondence"].articles) > len(report.profiles["otb"].articles)
    assert (tmp_path / "site" / "correspondence" / "quiz.html").is_file()
    assert (tmp_path / "site" / "otb" / "quiz.html").is_file()


def test_unanalyzed_profile_has_no_chapters_and_history_is_optional(tmp_path):
    profile = CollectionProfile("otb", "OTB", (FIXTURE,), player="Ada Example")
    output = tmp_path / "site"
    Workspace((profile,)).build(output, history=True)
    assert not list((output / "otb" / "chapters").glob("*.html"))
    assert "<script>" in (output / "otb" / "career.html").read_text(encoding="utf-8")
    Workspace((profile,)).build(output, history=False)
    assert "<script>" not in (output / "otb" / "career.html").read_text(encoding="utf-8")


def test_workspace_removes_generated_removed_profile_but_keeps_authored_file(tmp_path):
    config = manifest(tmp_path)
    output = tmp_path / "site"
    Workspace.from_toml(config).build(output)
    authored = output / "correspondence" / "notes.txt"
    authored.write_text("keep", encoding="utf-8")
    authored_chapter = output / "correspondence" / "chapters" / "best-authored.html"
    authored_chapter.parent.mkdir()
    authored_chapter.write_text("keep chapter", encoding="utf-8")
    one = Workspace((CollectionProfile("otb", "Over-the-board games", (FIXTURE,), player="Ada Example"),))
    one.build(output)
    assert not (output / "correspondence" / "index.html").exists()
    assert authored.read_text(encoding="utf-8") == "keep"
    assert authored_chapter.read_text(encoding="utf-8") == "keep chapter"


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


def test_duplicate_marker_entries_do_not_partially_delete_generated_files(tmp_path):
    output = tmp_path / "site"
    profile = CollectionProfile("otb", "OTB", (FIXTURE,), player="Ada Example")
    Workspace((profile,)).build(output)
    marker = output / "otb" / ".pgn-postmortem-profile.json"
    data = json.loads(marker.read_text(encoding="utf-8"))
    data["files"].append("index.html")
    marker.write_text(json.dumps(data), encoding="utf-8")
    before = (output / "otb" / "index.html").read_bytes()
    Workspace(()).build(output)
    assert (output / "otb" / "index.html").read_bytes() == before
    assert marker.is_file()


def test_normalized_duplicate_marker_entries_do_not_partially_delete_files(tmp_path):
    output = tmp_path / "site"
    profile = CollectionProfile("otb", "OTB", (FIXTURE,), player="Ada Example")
    Workspace((profile,)).build(output)
    marker = output / "otb" / ".pgn-postmortem-profile.json"
    data = json.loads(marker.read_text(encoding="utf-8"))
    data["files"].append("./index.html")
    marker.write_text(json.dumps(data), encoding="utf-8")
    before = (output / "otb" / "index.html").read_bytes()
    Workspace(()).build(output)
    assert (output / "otb" / "index.html").read_bytes() == before
    assert marker.is_file()


def test_workspace_rejects_cache_ancestor_and_rolls_back_later_failure(tmp_path):
    out = tmp_path / "site"
    with pytest.raises(WorkspaceConfigError):
        Workspace((CollectionProfile("otb", "OTB", (FIXTURE,), analyzed_dir=tmp_path),)).build(out)
    assert not out.exists()

    valid = CollectionProfile("otb", "OTB", (FIXTURE,), player="Ada Example")
    Workspace((valid,)).build(out)
    before = (out / "index.html").read_bytes()
    broken = CollectionProfile("broken", "Broken", (tmp_path / "missing.pgn",), player="Ada Example")
    with pytest.raises(WorkspaceBuildError) as error:
        Workspace((valid, broken)).build(out)
    assert error.value.slug == "broken"
    assert isinstance(error.value.cause, FileNotFoundError)
    assert "workspace profile 'broken' failed:" in str(error.value)
    assert (out / "index.html").read_bytes() == before
    assert not list(out.parent.glob(f".{out.name}.workspace-*"))


def test_untrusted_root_manifest_cannot_remove_a_profile(tmp_path):
    output = tmp_path / "site"
    Workspace.from_toml(manifest(tmp_path)).build(output)
    root_manifest = output / ".pgn-postmortem-workspace.json"
    data = json.loads(root_manifest.read_text(encoding="utf-8"))
    data["slugs"] = ["../outside"]
    root_manifest.write_text(json.dumps(data), encoding="utf-8")
    Workspace((CollectionProfile("otb", "OTB", (FIXTURE,), player="Ada Example"),)).build(output)
    assert (output / "correspondence" / "index.html").is_file()
