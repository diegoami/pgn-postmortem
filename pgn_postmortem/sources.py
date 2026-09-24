"""Where games come from. Every source yields (origin, game) pairs; the
ingest step (ingest.py) decides which of them are the player's and new.

Source types, as [[sources]] entries in pgn-postmortem.toml:

  type = "pgn"       any PGN collection: a file, a directory (searched with
                     `include`/`exclude` globs), an http(s) URL to a .pgn
                     file, or a git repository URL (cloned into .cache/)
  type = "chesscom"  a chess.com account, via the public API's monthly archives
  type = "lichess"   a lichess account, via the public game export API

Every source can carry a `label` (e.g. "Over the board"), recorded on each
game and used to group games in the book.
"""

from __future__ import annotations

import fnmatch
import hashlib
import io
import json
import subprocess
import sys
import time
import urllib.request
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import chess.pgn

from pgn_postmortem import __version__

USER_AGENT = f"pgn-postmortem/{__version__} (+https://github.com/diegoami/pgn-postmortem)"

SourceGame = tuple[str, chess.pgn.Game]


def http_get(url: str, accept: str = "*/*") -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as err:
            if err.code != 429 or attempt == 2:
                raise
            time.sleep(60)  # both APIs ask clients to back off for a minute when rate-limited
    raise AssertionError("unreachable")


def read_pgn_text(text: str, origin: str) -> Iterator[SourceGame]:
    """Every game in a (possibly multi-game) PGN string. Games python-chess
    couldn't parse cleanly are reported and skipped rather than half-imported."""
    handle = io.StringIO(text)
    while (game := chess.pgn.read_game(handle)) is not None:
        if game.errors:
            print(f"  warning: skipping unparseable game in {origin}: {game.errors[0]}", file=sys.stderr)
            continue
        yield origin, game


def read_pgn_file(path: Path, origin: str) -> Iterator[SourceGame]:
    # utf-8-sig drops the BOM some Windows tools write; errors="replace" keeps
    # old latin-1 exports readable instead of aborting the whole file.
    yield from read_pgn_text(path.read_text(encoding="utf-8-sig", errors="replace"), origin)


def is_git_url(location: str) -> bool:
    return location.startswith("git@") or location.endswith(".git") or location.startswith("https://github.com/")


_synced_this_run: set[Path] = set()


def sync_git_repo(url: str, cache_dir: Path) -> Path:
    """Clone url into the cache, or pull it if already cloned - once per run,
    however many sources point at the same repository."""
    checkout = cache_dir / "git" / hashlib.sha1(url.encode()).hexdigest()[:12]
    if checkout in _synced_this_run:
        return checkout
    _synced_this_run.add(checkout)
    if (checkout / ".git").is_dir():
        subprocess.run(["git", "-C", str(checkout), "pull", "--quiet", "--ff-only"], check=True)
    else:
        checkout.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", "--depth", "1", url, str(checkout)], check=True)
    return checkout


def pgn_source(source: dict, cache_dir: Path, base_dir: Path) -> Iterator[SourceGame]:
    location = source["path"]
    include = source.get("include", ["**/*.pgn"])
    exclude = source.get("exclude", [])

    if location.startswith(("http://", "https://")) and not is_git_url(location):
        yield from read_pgn_text(http_get(location).decode("utf-8", errors="replace"), location)
        return

    root = sync_git_repo(location, cache_dir) if is_git_url(location) else (base_dir / location).expanduser()
    if root.is_file():
        yield from read_pgn_file(root, root.name)
        return

    paths = sorted({p for pattern in include for p in root.glob(pattern) if p.is_file()})
    for path in paths:
        rel = path.relative_to(root).as_posix()
        if any(fnmatch.fnmatch(rel, pattern) for pattern in exclude):
            continue
        yield from read_pgn_file(path, rel)


def chesscom_source(source: dict, cache_dir: Path) -> Iterator[SourceGame]:
    """chess.com's public API serves one PGN archive per month. Past months
    never change, so they're downloaded once and cached; the current month is
    always re-fetched (finished daily games land in the month they ended)."""
    user = source["username"].lower()
    month_cache = cache_dir / "chesscom" / user
    month_cache.mkdir(parents=True, exist_ok=True)
    this_month = datetime.now(UTC).strftime("%Y-%m")

    archives = json.loads(http_get(f"https://api.chess.com/pub/player/{user}/games/archives"))["archives"]
    for archive_url in archives:
        month = "-".join(archive_url.rstrip("/").split("/")[-2:])
        cached = month_cache / f"{month}.pgn"
        if month >= this_month or not cached.exists():
            cached.write_bytes(http_get(f"{archive_url}/pgn"))
        yield from read_pgn_file(cached, f"chess.com {month}")


def lichess_source(source: dict, cache_dir: Path) -> Iterator[SourceGame]:
    """The lichess export API streams every game as PGN; only games newer than
    the last cached one are requested on later runs."""
    user = source["username"].lower()
    cached = cache_dir / "lichess" / f"{user}.pgn"
    state = cache_dir / "lichess" / f"{user}.json"
    cached.parent.mkdir(parents=True, exist_ok=True)

    since = json.loads(state.read_text())["until"] if state.exists() else 0
    now_ms = int(time.time() * 1000)
    new = http_get(
        f"https://lichess.org/api/games/user/{user}?since={since}&until={now_ms}&clocks=false&evals=false&opening=true",
        accept="application/x-chess-pgn",
    ).decode("utf-8")
    if new.strip():
        with cached.open("a", encoding="utf-8") as fh:
            fh.write(new.strip() + "\n\n")
    state.write_text(json.dumps({"until": now_ms + 1}))

    if cached.exists():
        yield from read_pgn_file(cached, "lichess")


def iter_source(source: dict, cache_dir: Path, base_dir: Path) -> Iterator[SourceGame]:
    kind = source.get("type")
    if kind == "pgn":
        return pgn_source(source, cache_dir, base_dir)
    if kind == "chesscom":
        return chesscom_source(source, cache_dir)
    if kind == "lichess":
        return lichess_source(source, cache_dir)
    raise ValueError(f"unknown source type {kind!r} (expected pgn, chesscom or lichess)")


def describe(source: dict) -> str:
    return source.get("label") or source.get("path") or f"{source.get('type')}:{source.get('username')}"
