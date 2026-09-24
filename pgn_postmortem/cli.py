"""pgn-postmortem command line.

    pgn-postmortem ingest    collect new games from every configured source into games/
    pgn-postmortem analyze   run Stockfish over games not analyzed yet
    pgn-postmortem book      build the book site from the analyzed games
    pgn-postmortem run       all three, in order - what a nightly job calls

Every command reads pgn-postmortem.toml from the current directory, or from
the path given with --config.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import chess.engine

from pgn_postmortem.analysis import Thresholds, analyze_files
from pgn_postmortem.config import DEFAULT_CONFIG_NAME, Config, load_config
from pgn_postmortem.ingest import ingest


def cmd_ingest(config: Config, args: argparse.Namespace) -> None:
    report = ingest(config)
    print(
        f"Ingested {report.new} new game(s) from {report.read} read "
        f"({report.duplicates} already known, {report.not_player} not {config.player}'s, "
        f"{report.empty} without moves)."
    )


def cmd_analyze(config: Config, args: argparse.Namespace) -> None:
    games = sorted(config.games_dir.glob("*.pgn"))
    todo = [p for p in games if args.force or not (config.analyzed_dir / p.name).exists()]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(games)} game(s) in games/, {len(todo)} to analyze.")
    if not todo:
        return
    a = config.analysis
    limit = chess.engine.Limit(depth=a.depth) if a.depth else chess.engine.Limit(time=a.time)
    thresholds = Thresholds(a.inaccuracy_pct, a.mistake_pct, a.blunder_pct)
    written = analyze_files(todo, config.analyzed_dir, limit, a.pv_length, thresholds, a.workers)
    print(f"Analyzed {written} game(s).")


def cmd_book(config: Config, args: argparse.Namespace) -> None:
    from pgn_postmortem.book.build import build_book

    build_book(config)


def cmd_run(config: Config, args: argparse.Namespace) -> None:
    cmd_ingest(config, args)
    cmd_analyze(config, args)
    cmd_book(config, args)


COMMANDS = {"ingest": cmd_ingest, "analyze": cmd_analyze, "book": cmd_book, "run": cmd_run}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="pgn-postmortem", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--config", type=Path, default=Path(DEFAULT_CONFIG_NAME), help=f"config file (default ./{DEFAULT_CONFIG_NAME})"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        p = sub.add_parser(name)
        if name in ("analyze", "run"):
            p.add_argument("--force", action="store_true", help="re-analyze games already in analyzed/")
            p.add_argument("--limit", type=int, default=0, help="analyze at most this many games (0 = all)")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        sys.exit(1)
    COMMANDS[args.command](config, args)
