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

Without --player or --alias, every game is kept.
"""

from __future__ import annotations

import argparse
import sys

from pgn_postmortem import __version__
from pgn_postmortem.analysis import DEFAULT_TIME, analyze_games
from pgn_postmortem.collection import CollectedGame, Collection


def add_reading_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("inputs", nargs="+", metavar="INPUT", help="a PGN file, a directory or a glob pattern")
    parser.add_argument("--player", help="the player's name as it appears in White/Black")
    parser.add_argument(
        "--alias", action="append", default=[], metavar="NAME", help="another name of the player (repeatable)"
    )


def read_collection(args: argparse.Namespace) -> Collection:
    collection = Collection.read(args.inputs, player=args.player, aliases=args.alias)
    for warning in collection.report.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(collection.report.summary())
    return collection


def cmd_read(args: argparse.Namespace) -> int:
    collection = read_collection(args)
    if args.out:
        paths = collection.write(args.out)
        print(f"Wrote {len(paths)} game(s) to {args.out}.")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
