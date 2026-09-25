"""pgn-postmortem command line.

    pgn-postmortem read INPUT... [--player NAME] [--alias NAME]... [--out DIR]
        Read PGN collections (files, directories, glob patterns; quote a
        pattern with ** so the library expands it), keep the player's games
        once each, strip comments, variations and NAGs, and print what was
        kept. With --out, write one PGN per game to DIR.

    pgn-postmortem analyze INPUT... --out DIR [--player NAME] [--alias NAME]...
                           [--depth N | --time SECONDS] [--workers N] [--engine PATH]
        Read the same way, then analyze with Stockfish every game that is not
        in DIR yet, writing it to DIR with [%eval] comments.

    pgn-postmortem site INPUT... --out DIR [--player NAME] [--alias NAME]... [--title TEXT]
                        [--site-key KEY] [--no-history]
        Read the same way, keeping the analysis of games that `analyze` wrote,
        and write a static site to DIR: one article per game and an index by
        year. Analyzed games get notes, diagrams and a "what would you play?"
        question at each critical moment; the others get a plain article.
        With --player or --alias, a quiz page lists the player's own critical
        moments, the costliest first, each linking to its question.
        Every page carries a small script that keeps a reading history in the
        reader's browser; --site-key sets the key it is stored under (by
        default one derived from the title), and --no-history leaves it out.

Without --player or --alias, every game is kept.
"""

from __future__ import annotations

import argparse
import sys

from pgn_postmortem import __version__
from pgn_postmortem.analysis import DEFAULT_TIME, EngineFailure, analyze_games
from pgn_postmortem.collection import CollectedGame, Collection
from pgn_postmortem.site import build_site, check_site_key, display_name


def add_reading_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("inputs", nargs="+", metavar="INPUT", help="a PGN file, a directory or a glob pattern")
    parser.add_argument("--player", help="the player's name as it appears in White/Black")
    parser.add_argument(
        "--alias", action="append", default=[], metavar="NAME", help="another name of the player (repeatable)"
    )


def read_collection(args: argparse.Namespace, keep_analysis: bool = False) -> Collection:
    collection = Collection.read(args.inputs, player=args.player, aliases=args.alias, keep_analysis=keep_analysis)
    for warning in collection.report.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(collection.report.summary())
    return collection


def cmd_read(args: argparse.Namespace) -> int:
    collection = read_collection(args)
    if args.out:
        paths = collection.write(args.out)
        kept = len(collection) - len(paths)
        already = f"; {kept} already analyzed there, left as they are" if kept else ""
        print(f"Wrote {len(paths)} game(s) to {args.out}{already}.")
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    collection = read_collection(args)

    def progress(done: int, total: int, item: CollectedGame) -> None:
        print(f"  [{done}/{total}] {item.filename}", flush=True)

    report = analyze_games(
        collection,
        args.out,
        depth=args.depth,
        time=args.time,
        workers=args.workers,
        engine_path=args.engine,
        progress=progress,
    )
    print(f"Analyzed {report.analyzed} game(s) into {args.out}; {report.skipped} already there.")
    return 0


def site_key(value: str) -> str:
    try:
        return check_site_key(value)
    except ValueError as err:
        raise argparse.ArgumentTypeError(str(err)) from None


def cmd_site(args: argparse.Namespace) -> int:
    collection = read_collection(args, keep_analysis=True)
    title = args.title or (f"Games of {display_name(args.player)}" if args.player else "Games")
    report = build_site(
        collection,
        args.out,
        title=title,
        history=args.history,
        site_key=args.site_key,
        player=args.player,
        aliases=args.alias,
    )
    print(report.summary(args.out))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pgn-postmortem", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    read = sub.add_parser("read", help="read and strip PGN collections")
    add_reading_options(read)
    read.add_argument("--out", metavar="DIR", help="write one stripped PGN per game here")
    read.set_defaults(func=cmd_read)

    analyze = sub.add_parser("analyze", help="analyze the games with Stockfish")
    add_reading_options(analyze)
    analyze.add_argument("--out", metavar="DIR", required=True, help="where analyzed games are written")
    budget = analyze.add_mutually_exclusive_group()
    budget.add_argument("--depth", type=int, help="search each position to this depth (reproducible)")
    budget.add_argument(
        "--time", type=float, default=DEFAULT_TIME, help=f"seconds per position (default {DEFAULT_TIME})"
    )
    analyze.add_argument("--workers", type=int, default=0, help="parallel Stockfish processes (default: one per CPU)")
    analyze.add_argument("--engine", metavar="PATH", help="the Stockfish binary (default: stockfish on PATH)")
    analyze.set_defaults(func=cmd_analyze)

    site = sub.add_parser("site", help="write the static site: an article per game and an index")
    add_reading_options(site)
    site.add_argument("--out", metavar="DIR", required=True, help="where the site is written")
    site.add_argument("--title", help='the site\'s title (default: "Games of <player>", or "Games")')
    site.add_argument(
        "--site-key",
        type=site_key,
        metavar="KEY",
        help="the key the reading history is stored under in the reader's browser: 1 to 64 letters, digits, "
        "'.', '_' or '-' (default: derived from the title)",
    )
    site.add_argument(
        "--no-history",
        dest="history",
        action="store_false",
        help="write the pages without the reading-history script, its section and its data- attributes",
    )
    site.set_defaults(func=cmd_site)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, EngineFailure) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
