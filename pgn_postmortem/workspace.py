"""Build isolated collection sites under one generated workspace landing page."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from html import escape
from pathlib import Path
from tempfile import mkdtemp

from pgn_postmortem.collection import Collection
from pgn_postmortem.site import GENERATOR, SiteReport, build_site, is_generated, write_text

SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
ROOT_MANIFEST = ".pgn-postmortem-workspace.json"
PROFILE_MANIFEST = ".pgn-postmortem-profile.json"
ROOT_GENERATOR = "pgn-postmortem workspace"
PROFILE_GENERATOR = "pgn-postmortem workspace profile"
ROOT_CSS_MARKER = "/* pgn-postmortem workspace */"
PROFILE_CSS_MARKER = "/* pgn-postmortem workspace profile: {slug} */"
GENERATED_NAMES = {"index.html", "career.html", "quiz.html"}


class WorkspaceConfigError(ValueError):
    """The workspace configuration is unsafe or invalid."""


class WorkspaceBuildError(RuntimeError):
    """One profile failed while a workspace was being built."""

    def __init__(self, slug: str, cause: Exception):
        self.slug = slug
        self.cause = cause
        super().__init__(f"workspace profile '{slug}' failed: {cause}")


@dataclass(frozen=True)
class CollectionProfile:
    slug: str
    title: str
    inputs: tuple[str | Path, ...]
    analyzed_dir: str | Path | None = None
    player: str | None = None
    aliases: tuple[str, ...] = ()
    description: str = ""
    source_label: str = ""


@dataclass(frozen=True)
class WorkspaceReport:
    landing: Path
    profiles: dict[str, SiteReport]


@dataclass(frozen=True)
class Workspace:
    profiles: tuple[CollectionProfile, ...]

    @classmethod
    def from_toml(cls, manifest: str | Path) -> Workspace:
        import tomllib

        path = Path(manifest).resolve()
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as error:
            raise WorkspaceConfigError(f"cannot read workspace manifest: {error}") from error
        profiles = []
        for raw in data.get("collection", []):
            if not isinstance(raw, dict):
                raise WorkspaceConfigError("each collection must be a table")
            inputs = raw.get("inputs", [])
            if not isinstance(inputs, list) or not all(isinstance(value, str) for value in inputs):
                raise WorkspaceConfigError("collection inputs must be a list of strings")
            analyzed = raw.get("analyzed_dir")
            profiles.append(
                CollectionProfile(
                    slug=raw.get("slug", ""),
                    title=raw.get("title", ""),
                    inputs=tuple(path.parent / value for value in inputs),
                    analyzed_dir=path.parent / analyzed if analyzed else None,
                    player=raw.get("player"),
                    aliases=tuple(raw.get("aliases", [])),
                    description=raw.get("description", ""),
                    source_label=raw.get("source_label", ""),
                )
            )
        return cls(tuple(profiles))

    def validate(self, out_dir: Path) -> None:
        slugs = set()
        outputs = []
        for profile in self.profiles:
            if not SLUG.fullmatch(profile.slug) or profile.slug in {"assets", "index.html"}:
                raise WorkspaceConfigError(f"invalid collection slug: {profile.slug!r}")
            if profile.slug in slugs:
                raise WorkspaceConfigError(f"duplicate collection slug: {profile.slug!r}")
            slugs.add(profile.slug)
            if not profile.title:
                raise WorkspaceConfigError(f"collection '{profile.slug}' has no title")
            outputs.append((profile.slug, (out_dir / profile.slug).resolve()))
        for slug, output in outputs:
            if output == out_dir or out_dir not in output.parents:
                raise WorkspaceConfigError(f"collection '{slug}' escapes workspace output")
            for other_slug, other in outputs:
                if slug != other_slug and (output == other or output in other.parents or other in output.parents):
                    raise WorkspaceConfigError(f"collection outputs overlap: {slug} and {other_slug}")
            for profile in self.profiles:
                paths = [Path(value).resolve() for value in profile.inputs]
                if profile.analyzed_dir:
                    paths.append(Path(profile.analyzed_dir).resolve())
                if any(path == output or path in output.parents or output in path.parents for path in paths):
                    raise WorkspaceConfigError(
                        f"collection '{profile.slug}' input/cache overlaps managed output '{slug}'"
                    )

    def build(self, out_dir: str | Path, *, history: bool = True) -> WorkspaceReport:
        out_dir = Path(out_dir).resolve()
        self.validate(out_dir)
        out_dir.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(mkdtemp(prefix=f".{out_dir.name}.workspace-", dir=out_dir.parent))
        try:
            if out_dir.is_dir():
                shutil.rmtree(staging)
                shutil.copytree(out_dir, staging)
            _clean_removed_profiles(staging, {profile.slug for profile in self.profiles})
            reports: dict[str, SiteReport] = {}
            for profile in self.profiles:
                inputs = [*profile.inputs, profile.analyzed_dir] if profile.analyzed_dir else list(profile.inputs)
                try:
                    games = Collection.read(inputs, player=profile.player, aliases=profile.aliases, keep_analysis=True)
                    report = build_site(
                        games,
                        staging / profile.slug,
                        title=profile.title,
                        history=history,
                        player=profile.player,
                        aliases=profile.aliases,
                        workspace_home="../index.html",
                    )
                    _mark_profile(staging / profile.slug, profile.slug, report)
                    reports[profile.slug] = report
                except Exception as error:
                    raise WorkspaceBuildError(profile.slug, error) from error
            _write_workspace_landing(staging, self.profiles, reports)
            backup = out_dir.with_name(f".{out_dir.name}.workspace-old")
            if backup.exists():
                shutil.rmtree(backup)
            if out_dir.exists():
                out_dir.rename(backup)
            staging.rename(out_dir)
            if backup.exists():
                shutil.rmtree(backup)
            return WorkspaceReport(
                out_dir / "index.html",
                {slug: _rebase(report, staging, out_dir) for slug, report in reports.items()},
            )
        except WorkspaceBuildError:
            if staging.exists():
                shutil.rmtree(staging)
            raise
        except Exception as error:
            if staging.exists():
                shutil.rmtree(staging)
            raise WorkspaceBuildError("workspace", error) from error


def _rebase(report: SiteReport, old: Path, new: Path) -> SiteReport:
    def path(value: Path) -> Path:
        return new / value.relative_to(old)

    report.articles = [path(value) for value in report.articles]
    report.removed = [path(value) for value in report.removed]
    report.quiz = path(report.quiz) if report.quiz else None
    return report


def _mark_profile(directory: Path, slug: str, report: SiteReport) -> None:
    css = directory / "assets" / "style.css"
    css.write_text(PROFILE_CSS_MARKER.format(slug=slug) + "\n" + css.read_text(encoding="utf-8"), encoding="utf-8")
    files = {"assets/style.css", "index.html"}
    if (directory / "career.html").is_file() and is_generated(directory / "career.html"):
        files.add("career.html")
    files.update(path.relative_to(directory).as_posix() for path in report.articles)
    if report.quiz:
        files.add(report.quiz.relative_to(directory).as_posix())
    files.update(
        path.relative_to(directory).as_posix()
        for path in (directory / "chapters").glob("best-*.html")
        if path.is_file() and is_generated(path)
    )
    write_text(
        directory / PROFILE_MANIFEST,
        json.dumps({"format": 1, "generator": PROFILE_GENERATOR, "slug": slug, "files": sorted(files)}, indent=2)
        + "\n",
    )


def _clean_removed_profiles(out_dir: Path, current: set[str]) -> None:
    manifest = out_dir / ROOT_MANIFEST
    if not manifest.is_file():
        return
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        slugs = data["slugs"]
        if data != {"format": 1, "generator": ROOT_GENERATOR, "slugs": slugs} or not isinstance(slugs, list):
            return
        if any(
            not isinstance(slug, str) or not SLUG.fullmatch(slug) or slug in {"assets", "index.html"}
            for slug in slugs
        ):
            return
        if len(set(slugs)) != len(slugs):
            return
        if any(
            out_dir / slug != (out_dir / slug).resolve()
            or out_dir not in (out_dir / slug).resolve().parents
            for slug in slugs
        ):
            return
        index = (out_dir / "index.html").read_text(encoding="utf-8")
        if '<meta name="generator" content="pgn-postmortem workspace">' not in index:
            return
        if not (out_dir / "assets" / "style.css").read_text(encoding="utf-8").startswith(ROOT_CSS_MARKER):
            return
        for slug in set(slugs) - current:
            _clean_profile(out_dir / slug, slug)
    except (OSError, ValueError, KeyError, TypeError):
        return


def _clean_profile(directory: Path, slug: str) -> None:
    marker = directory / PROFILE_MANIFEST
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
        files = data["files"]
        if data.get("format") != 1 or data.get("generator") != PROFILE_GENERATOR or data.get("slug") != slug:
            return
        if not isinstance(files, list):
            return
        validated = []
        for relative in files:
            path = Path(relative)
            if path.is_absolute() or ".." in path.parts or not _generated_profile_path(path):
                return
            target = directory / path
            if (
                not target.is_file()
                or not target.is_relative_to(directory)
                or not target.resolve().parent.is_relative_to(directory.resolve())
            ):
                return
            if path.as_posix() == "assets/style.css":
                if not target.read_text(encoding="utf-8").startswith(PROFILE_CSS_MARKER.format(slug=slug)):
                    return
            elif GENERATOR not in target.read_text(encoding="utf-8"):
                return
            validated.append(target)
        for target in validated:
            target.unlink()
        marker.unlink()
    except (OSError, ValueError, KeyError, TypeError):
        return


def _generated_profile_path(path: Path) -> bool:
    if path.as_posix() in {"index.html", "career.html", "quiz.html", "assets/style.css"}:
        return True
    return len(path.parts) == 2 and path.parts[0] in {"chapters", "games"} and path.suffix == ".html"


def _write_workspace_landing(
    out_dir: Path, profiles: tuple[CollectionProfile, ...], reports: dict[str, SiteReport]
) -> None:
    cards = []
    for profile in profiles:
        count = len(reports[profile.slug].articles)
        description = profile.description or profile.source_label
        cards.append(
            f'<article class="collection"><h2><a href="{escape(profile.slug)}/index.html">'
            f'{escape(profile.title)}</a></h2>'
            f"<p>{escape(description)}</p><p>{count} game(s)</p></article>\n"
        )
    html = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="generator" content="pgn-postmortem workspace">\n'
        '<title>Chess collections</title>\n<link rel="stylesheet" href="assets/style.css">\n</head>\n<body>\n'
        '<main><h1>Chess collections</h1>\n' + "".join(cards) + "</main>\n</body>\n</html>\n"
    )
    write_text(out_dir / "index.html", html)
    write_text(
        out_dir / "assets" / "style.css",
        ROOT_CSS_MARKER + "\n.collection{margin:1rem 0;padding:1rem;border:1px solid #aaa}\n",
    )
    write_text(
        out_dir / ROOT_MANIFEST,
        json.dumps({"format": 1, "generator": ROOT_GENERATOR, "slugs": [p.slug for p in profiles]}, indent=2) + "\n",
    )
