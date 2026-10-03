"""pgn-postmortem: turn a player's PGN collections into analyzed games and a
Wikipedia-style site, and (in a later release) an EPUB book.

The library API::

    from pgn_postmortem import Collection

    games = Collection.read(["games/**/*.pgn"], player="Ada Example", aliases=["adaex"])
    games.write("games-clean/")                     # optional: one stripped PGN per game
    games.analyze("analyzed/", depth=18, workers=4)  # Stockfish, [%eval] comments, incremental

    analyzed = Collection.read("analyzed/", player="Ada Example", aliases=["adaex"], keep_analysis=True)
    analyzed.build_site("site/", title="Games of Ada Example")  # an article per game, an index, the quiz

The same steps from the command line are ``pgn-postmortem read``,
``pgn-postmortem analyze`` and ``pgn-postmortem site`` (see ``pgn_postmortem.cli``).
"""

from pgn_postmortem.analysis import AnalysisReport, EngineFailure, Thresholds, analyze_games
from pgn_postmortem.collection import CollectedGame, Collection, ReadReport, find_pgn_files
from pgn_postmortem.selection import (
    ChapterWeights,
    SelectionFeatures,
    SelectionOptions,
    SelectionWeights,
    select_chapters,
)
from pgn_postmortem.site import SiteReport, build_site, critical_moments, shown_result
from pgn_postmortem.workspace import (
    CollectionProfile,
    Workspace,
    WorkspaceBuildError,
    WorkspaceConfigError,
    WorkspaceReport,
)

__version__ = "0.1.2"

__all__ = [
    "AnalysisReport",
    "CollectedGame",
    "Collection",
    "EngineFailure",
    "ReadReport",
    "ChapterWeights",
    "SelectionFeatures",
    "SelectionOptions",
    "SelectionWeights",
    "Thresholds",
    "__version__",
    "SiteReport",
    "analyze_games",
    "build_site",
    "critical_moments",
    "find_pgn_files",
    "shown_result",
    "select_chapters",
    "CollectionProfile",
    "Workspace",
    "WorkspaceBuildError",
    "WorkspaceConfigError",
    "WorkspaceReport",
]
