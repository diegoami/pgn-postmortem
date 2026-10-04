"""pgn-postmortem command line.

    pgn-postmortem read INPUT... [--player NAME] [--alias NAME]... [--out DIR]
        Read PGN collections (files, directories, glob patterns; quote a
        pattern with ** so the library expands it), keep the player's games
        once each, strip comments, variations and NAGs, and print what was
        kept. With --out, write one PGN per game to DIR.

    pgn-postmortem analyze INPUT... --out DIR [--player NAME] [--alias NAME]...
                           [--depth N | --time SECONDS] [--workers N] [--engine PATH]
                           [--correct-results [--result-policy NAME] [--result-threshold PERCENT]
                            [--result-skip-header NAME=REGEX]...]
        Read the same way, then analyze with Stockfish every game that is not
        in DIR yet, writing it to DIR with [%eval] comments. With
        --correct-results, each game analyzed now also gets its Result corrected
        from its final position (the source's value is kept in OriginalResult).

    pgn-postmortem correct-results DIR [--policy NAME] [--threshold PERCENT]
                           [--skip-header NAME=REGEX]... [--dry-run] [--explain]
        Optional: nothing is corrected unless you run this (or analyze
        --correct-results). Correct, without an engine, the Result of every
        analyzed game in DIR from its final position, and keep the source's value
        in the OriginalResult header. The policy (see --help) says which
        corrections are made; a decisive result in a level position can be genuine
        (a time forfeit, a resignation), so the default policy is not for every
        collection. Ids and file names do not change; running it again changes
        nothing. --dry-run only lists; --explain also lists every game kept, and why.
        Full reference: docs/result-correction.md.

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
from pgn_postmortem.results import DEFAULT_POLICY, POLICIES, PRESUME_THRESHOLD, correct_results, header_skip
from pgn_postmortem.selection import SelectionOptions
from pgn_postmortem.site import build_site, check_site_key, display_name
from pgn_postmortem.workspace import Workspace


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


POLICY_HELP = (
    "which corrections are made: 'all' (default): the final position's result whenever there is one, so a "
    "recorded decisive result in a level position becomes a draw; 'contradictions': only a recorded win or loss "
    "reversed, or a recorded draw made decisive; 'unrecorded': only a missing or '*' result is filled in; "
    "'board': only what the board itself decides (checkmate, stalemate, insufficient material)"
)
SKIP_HELP = (
    "leave alone the games whose header NAME matches the regular expression REGEX (repeatable; any rule skips), "
    "e.g. 'Termination=(?i)forfeit|time' or 'PostmortemId=^bf58e2afa0$'"
)


def skip_rule(value: str) -> str:
    try:
        header_skip([value])
    except ValueError as err:
        raise argparse.ArgumentTypeError(str(err)) from None
    return value


def cmd_analyze(args: argparse.Namespace) -> int:
    given = [
        flag
        for flag, value in (
            ("--result-threshold", args.result_threshold),
            ("--result-policy", args.result_policy),
            ("--result-skip-header", args.result_skip_header),
        )
        if value not in (None, [])
    ]
    if given and not args.correct_results:
        verb = "only applies" if len(given) == 1 else "only apply"
        raise SystemExit(f"error: {' and '.join(given)} {verb} with --correct-results")
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
        correct_results=args.correct_results,
        presume_threshold=args.result_threshold,
        result_policy=args.result_policy,
        result_skip=header_skip(args.result_skip_header),
        progress=progress,
    )
    print(f"Analyzed {report.analyzed} game(s) into {args.out}; {report.skipped} already there.")
    if args.correct_results:
        threshold = PRESUME_THRESHOLD if args.result_threshold is None else args.result_threshold
        print(f"Policy: {args.result_policy or DEFAULT_POLICY}, threshold {threshold:g}.")
    for change in report.corrections:
        print(change.line())
    if args.correct_results:
        print(f"Corrected the result of {len(report.corrections)} game(s) analyzed now.")
    return 0


def cmd_correct_results(args: argparse.Namespace) -> int:
    report = correct_results(
        args.directory,
        presume_threshold=args.threshold,
        dry_run=args.dry_run,
        policy=args.policy,
        skip=header_skip(args.skip_header),
    )
    for warning in report.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(report.header())
    if args.skip_header:
        print("Skip rules: " + "; ".join(args.skip_header))
    for change in report.changes:
        print(change.line())
    if args.explain:
        for line in report.explain():
            print(line)
    print(report.summary())
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
        selection_options=SelectionOptions(chapter_size=args.chapter_size, minimum_length=args.minimum_length),
    )
    print(report.summary(args.out))
    return 0


def cmd_workspace(args: argparse.Namespace) -> int:
    report = Workspace.from_toml(args.manifest).build(args.out, history=args.history)
    for slug, correction in report.corrections.items():
        print(f"{slug}: result correction in memory. {correction.header()} {correction.summary()}")
    print(f"Wrote workspace landing page to {report.landing} with {len(report.profiles)} collection(s).")
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
    analyze.add_argument(
        "--correct-results",
        action="store_true",
        help="correct each newly analyzed game's Result from its final position (keeps OriginalResult)",
    )
    analyze.add_argument(
        "--result-threshold",
        type=float,
        metavar="PERCENT",
        help=f"winning chances (55 to 95) that make a win when correcting (default {PRESUME_THRESHOLD:g})",
    )
    analyze.add_argument(
        "--result-policy", choices=POLICIES, metavar="NAME", help="with --correct-results, " + POLICY_HELP
    )
    analyze.add_argument(
        "--result-skip-header",
        action="append",
        default=[],
        type=skip_rule,
        metavar="NAME=REGEX",
        help="with --correct-results, " + SKIP_HELP,
    )
    analyze.set_defaults(func=cmd_analyze)

    correct = sub.add_parser("correct-results", help="correct the Result of analyzed games from the final position")
    correct.add_argument("directory", metavar="DIR", help="a directory of analyzed PGNs (or one file)")
    correct.add_argument(
        "--threshold",
        type=float,
        default=PRESUME_THRESHOLD,
        metavar="PERCENT",
        help=f"winning chances (55 to 95) that make a win (default {PRESUME_THRESHOLD:g})",
    )
    correct.add_argument("--policy", choices=POLICIES, default=DEFAULT_POLICY, metavar="NAME", help=POLICY_HELP)
    correct.add_argument(
        "--skip-header", action="append", default=[], type=skip_rule, metavar="NAME=REGEX", help=SKIP_HELP
    )
    correct.add_argument("--explain", action="store_true", help="also list every game kept, and why")
    correct.add_argument("--dry-run", action="store_true", help="list the changes without writing anything")
    correct.set_defaults(func=cmd_correct_results)

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
    site.add_argument("--chapter-size", type=int, default=5, help="number of games in each featured chapter")
    site.add_argument("--minimum-length", type=int, default=20, help="minimum game length in full moves for selection")
    site.set_defaults(func=cmd_site)

    workspace = sub.add_parser("workspace", help="write isolated collection sites and a landing page")
    workspace.add_argument("manifest", metavar="MANIFEST", help="the profile-only collections.toml manifest")
    workspace.add_argument("--out", metavar="DIR", required=True, help="where the workspace is written")
    workspace.add_argument(
        "--no-history",
        dest="history",
        action="store_false",
        help="write collection pages without the reading-history script",
    )
    workspace.set_defaults(func=cmd_workspace, history=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, EngineFailure, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
