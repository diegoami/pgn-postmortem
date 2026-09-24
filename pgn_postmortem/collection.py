"""Reading PGN collections: find the files, read every game in them, keep the
player's games once each, and strip what the source attached to the moves.

Stripping keeps the headers and the mainline moves only. Every comment
(a source ``[%eval]`` included), variation and NAG is dropped: the library
re-analyzes every game itself, and old collections carry stale engine notes
(CLAUDE.md, *decided*). The headers that only describe such notes
(``DROPPED_HEADERS``) go too, and so does ``PostmortemAnalysis``, the marker
the analysis step writes: a game read back from the library's own output is
a stripped game again, to be analyzed again wherever it is written. One
header of our own is added: ``PostmortemId``, the game's content id.

Games are identified by their content, not by where they were found, so the
same game in two files is kept once, and a game read back from the library's
own output has the same id as before it was analyzed.

The duplicate rule, exactly (``game_id``; the owner's decision of
2026-09-24, for every game length): a game's identity is its **start
position, moves, result and date**. The id is the first 10 hex digits of the
SHA-1 of:

- the start position as a normalized FEN: python-chess's rendering of the
  position the ``FEN`` header sets up, and empty for the standard start, so a
  ``FEN`` header that spells out the standard start is the same as none;
- the ``Result`` header as written (``*`` when there is none);
- the ``Date`` header as written (``????.??.??``, python-chess's placeholder,
  when there is none);
- the mainline moves in UCI.

The players' names are not part of it, so a game exported under two of the
player's names or aliases is one game. Two games with the same id are one
game, and the first one read is kept (inputs in the order given, files sorted
within a directory or a pattern, games in file order). What follows from it:

- copies whose ``Date`` headers differ in any way are kept twice: one with no
  date or a partial date (``2019.??.??``) and one with the full date, or dates
  written differently (``2019.03.14`` and ``2019.3.14``);
- copies whose ``Result`` headers differ (``1-0`` and ``*``), or that differ
  in any move, are kept twice;
- two different games with the same start, moves, result and date are merged:
  a short trap, or the same opening line agreed drawn, played twice on the
  same day against different opponents keeps only the first game.
"""

from __future__ import annotations

import glob
import hashlib
import io
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

import chess
import chess.pgn

ID_HEADER = "PostmortemId"
ANALYSIS_HEADER = "PostmortemAnalysis"  # written only by the analysis step (pgn_postmortem.analysis)
DROPPED_HEADERS = {"Annotator", "PlyCount", "CurrentPosition", ANALYSIS_HEADER}

GLOB_CHARS = set("*?[")


@dataclass(frozen=True)
class CollectedGame:
    """One game of a collection, already stripped."""

    id: str
    game: chess.pgn.Game
    origin: str  # the file it was first found in, and its position there, e.g. "club/2019.pgn#2"

    @property
    def filename(self) -> str:
        """``<date>-<id>.pgn``, the date zero-padded (``2019-03-14``), so a
        plain directory listing is chronological (see ``file_stem``)."""
        return f"{file_stem(self.game, self.id)}.pgn"


@dataclass
class ReadReport:
    files: int = 0
    read: int = 0
    unparseable: int = 0
    empty: int = 0
    not_player: int = 0
    duplicates: int = 0
    kept: int = 0
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"Read {self.read} game(s) from {self.files} file(s): {self.not_player} not the player's, "
            f"{self.duplicates} duplicate(s), {self.empty} without moves, {self.unparseable} unparseable; "
            f"kept {self.kept}."
        )


def find_pgn_files(inputs: Iterable[str | Path]) -> list[Path]:
    """The PGN files named by ``inputs``, in order and each once.

    Each input is a file (taken whatever its extension), a directory (every
    ``*.pgn`` below it, recursively) or a glob pattern (``**`` crosses
    directories). An existing path is always taken as that path, even when
    its name contains ``*``, ``?`` or ``[``; only an input that does not
    exist is expanded as a pattern. A path that does not exist, or a pattern
    that matches nothing, raises ``FileNotFoundError``: a typo should not read
    as an empty collection.
    """
    found: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        key = path.resolve()
        if key not in seen:
            seen.add(key)
            found.append(path)

    def add_dir(path: Path) -> None:
        for child in sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() == ".pgn"):
            add(child)

    for item in inputs:
        text = str(item)
        path = Path(text).expanduser()
        if GLOB_CHARS & set(text) and not path.exists():
            matches = sorted(Path(p) for p in glob.glob(text, recursive=True))
            if not matches:
                raise FileNotFoundError(f"no file matches {text}")
            for match in matches:
                if match.is_dir():
                    add_dir(match)
                else:
                    add(match)
            continue
        if path.is_dir():
            add_dir(path)
        elif path.is_file():
            add(path)
        else:
            raise FileNotFoundError(f"no such file or directory: {text}")
    return found


def read_text(path: Path) -> str:
    """The file's text, decoded once for the whole file: UTF-8 (with or
    without a BOM) if the whole file is valid UTF-8; else Windows-1252, what
    old Windows-era collections are usually in (a superset of Latin-1's
    letters, with curly quotes and dashes); else, for the five bytes
    Windows-1252 leaves undefined, Latin-1, which decodes any byte, so a file
    is never rejected for its encoding.

    The decision is per file, not per game: a file that concatenates UTF-8
    and Windows-1252 games is not valid UTF-8, so its UTF-8 games come out
    as mojibake (``JÃ¼rgen``). Convert such a file to UTF-8 first."""
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("latin-1")


def iter_games(path: Path, report: ReadReport) -> Iterator[tuple[str, chess.pgn.Game]]:
    """Every game in a (possibly multi-game) PGN file. A game python-chess
    cannot parse cleanly is reported and skipped, not half-read."""
    handle = io.StringIO(read_text(path))
    index = 0
    while (game := chess.pgn.read_game(handle)) is not None:
        index += 1
        report.read += 1
        origin = f"{path}#{index}"
        if game.errors:
            report.unparseable += 1
            report.warnings.append(f"skipping unparseable game {origin}: {game.errors[0]}")
            continue
        yield origin, game


def game_id(game: chess.pgn.Game) -> str:
    """A short id computed from the game's start position, moves, result and
    date (the exact rule and what follows from it are in the module
    docstring). Comments, variations, NAGs, the players' names and the
    headers stripping drops or adds do not change it."""
    start = game.board().fen()
    parts = [
        "" if start == chess.STARTING_FEN else start,
        game.headers.get("Result", "*"),
        game.headers.get("Date", ""),
        " ".join(move.uci() for move in game.mainline_moves()),
    ]
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:10]


def file_stem(game: chess.pgn.Game, gid: str) -> str:
    """``<yyyy>-<mm>-<dd>-<id>`` from the ``Date`` header: month and day
    zero-padded to two digits (``2019.3.14`` gives ``2019-03-14``), an unknown
    month or day as ``00``, and ``undated-<id>`` when the year is unknown. Only
    the file name is normalized; the id keeps the header as written."""
    date = game.headers.get("Date", "")
    y, m, d = (date.split(".") + ["", "", ""])[:3]
    if not y.isdigit():
        return f"undated-{gid}"
    return f"{y}-{m.zfill(2) if m.isdigit() else '00'}-{d.zfill(2) if d.isdigit() else '00'}-{gid}"


def strip_game(game: chess.pgn.Game, gid: str) -> chess.pgn.Game:
    """A copy of ``game`` with its headers and mainline moves only."""
    out = chess.pgn.Game()
    for key, value in game.headers.items():
        if key not in DROPPED_HEADERS:
            out.headers[key] = value
    if "FEN" in game.headers:
        out.setup(game.board())
    out.headers[ID_HEADER] = gid

    node: chess.pgn.GameNode = out
    for move in game.mainline_moves():
        node = node.add_variation(move)
    return out


def analyzed_id(path: Path) -> str | None:
    """The ``PostmortemId`` of the game in ``path`` if the analysis step
    wrote it (its first game carries the ``PostmortemAnalysis`` marker), else
    None: a stripped game, or any other file."""
    headers = chess.pgn.read_headers(io.StringIO(read_text(path)))
    if headers is None or ANALYSIS_HEADER not in headers:
        return None
    return headers.get(ID_HEADER)


def analyzed_ids(out_dir: Path) -> set[str]:
    """The ids of the games already analyzed into ``out_dir``: the
    ``PostmortemId`` of each file there whose first game carries the
    ``PostmortemAnalysis`` marker, whatever the file is called. A file
    without it (a game that was only stripped, or anything else) does not
    count."""
    return {gid for path in out_dir.glob("*.pgn") if (gid := analyzed_id(path))}


def format_game(game: chess.pgn.Game) -> str:
    """PGN text wrapped at 80 columns, the usual PGN convention."""
    exporter = chess.pgn.StringExporter(columns=80)
    return game.accept(exporter) + "\n"


def player_names(player: str | None, aliases: Iterable[str]) -> set[str]:
    return {name.strip().casefold() for name in [player or "", *aliases] if name and name.strip()}


class Collection:
    """The games read from one or more PGN collections: the player's games
    only, each once, stripped. ``report`` says what was left out and why."""

    def __init__(self, games: list[CollectedGame], report: ReadReport | None = None):
        self.games = games
        self.report = report or ReadReport(kept=len(games))

    @classmethod
    def read(
        cls,
        inputs: str | Path | Iterable[str | Path],
        player: str | None = None,
        aliases: Iterable[str] = (),
    ) -> Collection:
        """Read ``inputs`` (files, directories, globs; see ``find_pgn_files``).

        With a ``player`` or ``aliases``, only games where White or Black is
        one of those names (compared without regard to case or surrounding
        spaces) are kept; with neither, every game is.
        """
        if isinstance(inputs, str | Path):
            inputs = [inputs]
        names = player_names(player, aliases)
        report = ReadReport()
        games: list[CollectedGame] = []
        seen: set[str] = set()

        for path in find_pgn_files(inputs):
            report.files += 1
            for origin, game in iter_games(path, report):
                if names and not (
                    game.headers.get("White", "").strip().casefold() in names
                    or game.headers.get("Black", "").strip().casefold() in names
                ):
                    report.not_player += 1
                    continue
                if game.next() is None:
                    report.empty += 1
                    continue
                gid = game_id(game)
                if gid in seen:
                    report.duplicates += 1
                    continue
                seen.add(gid)
                games.append(CollectedGame(gid, strip_game(game, gid), origin))

        report.kept = len(games)
        return cls(games, report)

    def __iter__(self) -> Iterator[CollectedGame]:
        return iter(self.games)

    def __len__(self) -> int:
        return len(self.games)

    def write(self, out_dir: str | Path) -> list[Path]:
        """Write every game, stripped, to ``out_dir/<date>-<id>.pgn``, and
        return the paths written.

        A game already analyzed into ``out_dir`` is not written, so reading
        new games into an analysis directory never throws away analysis
        already done, nor adds a stripped copy next to it. "Already analyzed"
        is the analysis step's own test (``analyzed_ids``): a file there whose
        first game carries the ``PostmortemAnalysis`` marker and a
        ``PostmortemId`` equal to this game's content id (``game_id``: start
        position, moves, result and date). It goes by the id, not the file
        name, so a game analyzed under an older name (before dates in names
        were zero-padded, ``2019-3-14-<id>.pgn``) still counts. Any other
        file at the game's name (a stripped copy, or something else) is
        overwritten."""
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        done_ids = analyzed_ids(out_dir)
        paths = []
        for item in self.games:
            if item.id in done_ids:
                continue
            path = out_dir / item.filename
            path.write_text(format_game(item.game), encoding="utf-8")
            paths.append(path)
        return paths

    def analyze(self, out_dir: str | Path, **options):
        """Analyze the games with Stockfish into ``out_dir``; see
        ``pgn_postmortem.analysis.analyze_games`` for the options."""
        from pgn_postmortem.analysis import analyze_games

        return analyze_games(self.games, out_dir, **options)
