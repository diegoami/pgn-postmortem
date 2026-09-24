"""The library's reading step (pgn_postmortem.collection) on the fixture
collection in tests/fixtures/collection/:

  club/2019.pgn         three games: Ada's annotated draw (as "Ada Example"),
                        a game between two other players, Ada's win as Black
                        (as "Example, Ada")
  online/2020/games.pgn two games: Ada's loss (as "AdaEx"), and the same
                        draw as in club/2019.pgn without its annotations
"""

from pathlib import Path

import chess
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


# A game's identity is its moves, result, date and start position, for every game length
# (owner decision, 2026-09-24); the players' names are not part of it.
SHORT = "1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0"
LONG = (
    "1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6 5. d3 d6 6. O-O O-O 7. Re1 a6 8. Bb3 Ba7 9. h3 h6"
    " 10. Nbd2 Re8 1-0"
)


def pgn(moves: str, date: str = "2020.06.01", white: str = "Ada Example", extra: str = "") -> str:
    result = moves.rsplit(" ", 1)[-1]
    return f'[Date "{date}"]\n[White "{white}"]\n[Black "Rival"]\n[Result "{result}"]\n{extra}\n{moves}\n\n'


def test_the_same_game_under_two_aliases_is_kept_once(tmp_path):
    path = tmp_path / "aliases.pgn"
    path.write_text(pgn(SHORT, white="Ada Example") + pgn(SHORT, white="adaex"), encoding="utf-8")
    collection = Collection.read(path, **PLAYER)
    assert (collection.report.kept, collection.report.duplicates) == (1, 1)


def test_the_same_moves_and_result_on_different_dates_are_kept_twice(tmp_path):
    path = tmp_path / "dates.pgn"
    path.write_text(pgn(LONG, date="2015.01.01") + pgn(LONG, date="2021.01.01"), encoding="utf-8")
    collection = Collection.read(path, **PLAYER)
    assert (collection.report.kept, collection.report.duplicates) == (2, 0)


def test_dates_written_differently_are_two_games_with_the_same_padded_file_date(tmp_path):
    # The id takes the Date header as written (owner decision, 2026-09-24): only the file
    # name pads it, so 2019.3.14 and 2019.03.14 are two games, both named 2019-03-14-<id>.pgn
    # (review 007, round 01, finding 1).
    path = tmp_path / "padding.pgn"
    path.write_text(pgn(LONG, date="2019.3.14") + pgn(LONG, date="2019.03.14"), encoding="utf-8")
    collection = Collection.read(path, **PLAYER)
    assert (collection.report.kept, collection.report.duplicates) == (2, 0)
    first, second = collection
    assert first.id != second.id
    assert [item.filename for item in collection] == [f"2019-03-14-{first.id}.pgn", f"2019-03-14-{second.id}.pgn"]


def test_an_explicit_standard_start_is_the_same_as_none(tmp_path):
    path = tmp_path / "fen.pgn"
    standard = f'[SetUp "1"]\n[FEN "{chess.STARTING_FEN}"]\n'
    path.write_text(pgn(LONG) + pgn(LONG, extra=standard), encoding="utf-8")
    collection = Collection.read(path, **PLAYER)
    assert (collection.report.kept, collection.report.duplicates) == (1, 1)


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


def test_file_names_are_zero_padded_so_a_listing_is_chronological(tmp_path):
    # A Date written without zero-padding (2019.3.14) must still give 2019-03-14 in the file
    # name, or 2019-3-14 sorts after 2019-12-01 (review 006, round 03, finding 14). Unknown
    # parts stay 00, and a game without a year stays undated.
    dates = ["2019.12.1", "2020.1.2", "2019.3.14", "2019.3.??", "????.??.??", "2019.??.??", "2019.03.9"]
    path = tmp_path / "dates.pgn"
    path.write_text("".join(pgn(SHORT, date=date) for date in dates), encoding="utf-8")
    collection = Collection.read(path, **PLAYER)
    assert len(collection) == len(dates)
    stems = {item.game.headers["Date"]: item.filename.removesuffix(f"-{item.id}.pgn") for item in collection}
    assert stems == {
        "2019.12.1": "2019-12-01",
        "2020.1.2": "2020-01-02",
        "2019.3.14": "2019-03-14",
        "2019.3.??": "2019-03-00",
        "????.??.??": "undated",
        "2019.??.??": "2019-00-00",
        "2019.03.9": "2019-03-09",
    }

    # a plain listing of the written files is in date order, the undated game last
    out = tmp_path / "out"
    collection.write(out)
    date_of = {item.filename: item.game.headers["Date"] for item in collection}
    assert [date_of[name] for name in sorted(p.name for p in out.iterdir())] == [
        "2019.??.??",
        "2019.3.??",
        "2019.03.9",
        "2019.3.14",
        "2019.12.1",
        "2020.1.2",
        "????.??.??",
    ]
