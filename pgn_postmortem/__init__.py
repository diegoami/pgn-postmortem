"""pgn-postmortem: turn a player's PGN collections into analyzed games and a
Wikipedia-style site, and (in a later release) an EPUB book.

The library API::

    from pgn_postmortem import Collection

    games = Collection.read(["games/**/*.pgn"], player="Ada Example", aliases=["adaex"])
    games.write("games-clean/")                     # optional: one stripped PGN per game
    games.analyze("analyzed/", depth=18, workers=4)  # Stockfish, [%eval] comments, incremental

    analyzed = Collection.read("analyzed/", keep_analysis=True)
    analyzed.build_site("site/", title="Games of Ada Example")  # one article per game, an index

The same steps from the command line are ``pgn-postmortem read``,
``pgn-postmortem analyze`` and ``pgn-postmortem site`` (see ``pgn_postmortem.cli``).
"""

from pgn_postmortem.analysis import AnalysisReport, EngineFailure, Thresholds, analyze_games
from pgn_postmortem.collection import CollectedGame, Collection, ReadReport, find_pgn_files
from pgn_postmortem.site import SiteReport, build_site, critical_moments, shown_result

__version__ = "0.1.0"

__all__ = [
    "AnalysisReport",
    "CollectedGame",
    "Collection",
    "EngineFailure",
    "ReadReport",
    "Thresholds",
    "__version__",
    "SiteReport",
    "analyze_games",
    "build_site",
    "critical_moments",
    "find_pgn_files",
    "shown_result",
]
