"""The library's reading step (pgn_postmortem.collection) on the fixture
collection in tests/fixtures/collection/:

  club/2019.pgn         three games: Ada's annotated draw (as "Ada Example"),
                        a game between two other players, Ada's win as Black
                        (as "Example, Ada")
  online/2020/games.pgn two games: Ada's loss (as "AdaEx"), and the same
                        draw as in club/2019.pgn without its annotations
"""

from pathlib import Path

import chess.pgn
import pytest

from pgn_postmortem import Collection, find_pgn_files

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "collection"
CLUB = FIXTURES / "club" / "2019.pgn"
ONLINE = FIXTURES / "online" / "2020" / "games.pgn"
PLAYER = {"player": "Ada Example", "aliases": ["adaex", "Example, Ada"]}


def test_a_multi_game_file_is_read_whole():
    collection = Collection.read(CLUB)
    assert collection.report.read == 3
    assert [item.game.headers["White"] for item in collection] == ["Ada Example", "Carla Stranger", "Enzo Opponent"]


def test_a_glob_collects_files_across_directories():
    assert find_pgn_files([f"{FIXTURES}/**/*.pgn"]) == [CLUB, ONLINE]
    collection = Collection.read(f"{FIXTURES}/**/*.pgn")
    assert {Path(item.origin.split("#")[0]) for item in collection} == {CLUB, ONLINE}


def test_a_directory_is_searched_recursively():
    assert find_pgn_files([FIXTURES]) == [CLUB, ONLINE]


def test_an_existing_path_with_glob_characters_is_read_as_that_file(tmp_path):
    literal = tmp_path / "games [2019] *?.pgn"
    literal.write_text(CLUB.read_text(encoding="utf-8"), encoding="utf-8")
    assert find_pgn_files([str(literal)]) == [literal]
    assert len(Collection.read(str(literal))) == 3


def test_a_missing_input_is_an_error_not_an_empty_collection(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_pgn_files([tmp_path / "nope.pgn"])
    with pytest.raises(FileNotFoundError):
        find_pgn_files([f"{tmp_path}/**/*.pgn"])


def test_only_the_players_games_are_kept_under_any_alias():
    collection = Collection.read(FIXTURES, **PLAYER)
    players = sorted((item.game.headers["White"], item.game.headers["Black"]) for item in collection)
    assert players == [
        ("Ada Example", "Bruno Rival"),
        ("Enzo Opponent", "Example, Ada"),
        ("Fabio Quick", "AdaEx"),  # the alias "adaex", matched without regard to case
    ]
    assert collection.report.not_player == 1


def test_a_game_found_in_two_files_is_kept_once():
    collection = Collection.read([CLUB, ONLINE], **PLAYER)
    draws = [item for item in collection if item.game.headers["Black"] == "Bruno Rival"]
    assert len(draws) == 1
    assert draws[0].origin == f"{CLUB}#1"  # the first file it was found in
    assert collection.report.duplicates == 1
    assert collection.report.kept == 3


def test_comments_variations_and_nags_are_stripped():
    source = chess.pgn.read_game(CLUB.open(encoding="utf-8"))
    assert source.comment and source.next().comment.startswith("[%eval")  # the fixture does carry them

    draw = Collection.read(CLUB).games[0].game
    nodes = [draw, *draw.mainline()]
    assert all(not node.comment for node in nodes)
    assert all(len(node.variations) <= 1 for node in nodes)
    assert all(not node.nags for node in nodes)
    assert "[%eval" not in str(draw)
    assert "Annotator" not in draw.headers and "PlyCount" not in draw.headers
    assert [m.uci() for m in draw.mainline_moves()] == [m.uci() for m in source.mainline_moves()]


def test_a_latin1_file_is_read_without_losing_its_accents(tmp_path):
    path = tmp_path / "old.pgn"
    path.write_bytes('[White "Jürgen Müller"]\n[Black "B"]\n[Result "*"]\n\n1. e4 e5 *\n'.encode("latin-1"))
    assert Collection.read(path).games[0].game.headers["White"] == "Jürgen Müller"


def test_a_windows_file_keeps_its_curly_quotes(tmp_path):
    path = tmp_path / "windows.pgn"
    path.write_bytes('[Event "Café “Open”"]\n[White "A"]\n[Black "B"]\n[Result "*"]\n\n1. e4 e5 *\n'.encode("cp1252"))
    assert Collection.read(path).games[0].game.headers["Event"] == "Café “Open”"

    # 0x81 is undefined in Windows-1252: the file is still read, through Latin-1
    path.write_bytes(b'[White "A\x81"]\n[Black "B"]\n[Result "*"]\n\n1. e4 e5 *\n')
    assert Collection.read(path).games[0].game.headers["White"] == "A\x81"


def test_the_library_output_reads_back_with_the_same_ids(tmp_path):
    collection = Collection.read(FIXTURES, **PLAYER)
    collection.write(tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(item.filename for item in collection)
    assert sorted(item.id for item in Collection.read(tmp_path)) == sorted(item.id for item in collection)
