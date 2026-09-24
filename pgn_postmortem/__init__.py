"""pgn-postmortem: turn a player's PGN collections into analyzed games, and
(in later releases) into a Wikipedia-style site and an EPUB book.

The library API::

    from pgn_postmortem import Collection

    games = Collection.read(["games/**/*.pgn"], player="Ada Example", aliases=["adaex"])
    games.write("games-clean/")  # one stripped PGN per game
"""

from pgn_postmortem.collection import CollectedGame, Collection, ReadReport, find_pgn_files

__version__ = "0.1.0"

__all__ = ["CollectedGame", "Collection", "ReadReport", "__version__", "find_pgn_files"]
