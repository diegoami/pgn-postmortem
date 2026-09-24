"""pgn-postmortem: turn a player's PGN collections into analyzed games, and
(in later releases) into a Wikipedia-style site and an EPUB book.

The library API::

    from pgn_postmortem import Collection

    games = Collection.read(["games/**/*.pgn"], player="Ada Example", aliases=["adaex"])
    games.write("games-clean/")                     # optional: one stripped PGN per game
    games.analyze("analyzed/", depth=18, workers=4)  # Stockfish, [%eval] comments, incremental
"""

from pgn_postmortem.analysis import AnalysisReport, Thresholds, analyze_games
from pgn_postmortem.collection import CollectedGame, Collection, ReadReport, find_pgn_files

__version__ = "0.1.0"

__all__ = [
    "AnalysisReport",
    "CollectedGame",
    "Collection",
    "ReadReport",
    "Thresholds",
    "__version__",
    "analyze_games",
    "find_pgn_files",
]
