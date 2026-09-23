import pytest

from openings import load_book


@pytest.fixture(scope="module")
def book():
    return load_book()


def test_named_line_that_is_left(book):
    moves = ["e4", "e5", "f4", "exf4", "Nf3", "Nf6", "e5", "Nh5", "Be2"]
    result = book.find_deviation(moves)
    assert result["in_book_plies"] == 8
    assert result["opening"] == ("C34", "King's Gambit Accepted: Schallopp Defense")
    assert result["left_book"]


def test_position_inside_a_line_without_its_own_name(book):
    # 1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 is in book but only the shorter prefix is named
    result = book.find_deviation(["e4", "e5", "Nf3", "Nc6", "Bb5", "a6"])
    assert result["in_book_plies"] == 6
    assert not result["left_book"]
    assert result["opening"][1].startswith("Ruy Lopez")


def test_nothing_matches(book):
    result = book.find_deviation(["h4", "h5", "Rh3", "Rh6", "Ra3"])
    assert result["opening"] is None or result["in_book_plies"] < 5


def test_continuations_extend_the_prefix(book):
    conts = book.continuations(["e4", "e5", "f4", "exf4", "Nf3", "Nf6", "e5", "Nh5"])
    assert conts
    assert all(eco.startswith("C") for eco, _, _ in conts)
    assert len({moves[0] for _, _, moves in conts}) == len(conts)  # one example per distinct next move
