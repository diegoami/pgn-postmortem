import os

from pgn_io import load_dotenv, read_single_game

GAME = '[White "A"]\n[Black "B"]\n[Result "*"]\n\n1. e4 e5 *\n'


def test_read_single_game(tmp_path):
    path = tmp_path / "1.pgn"
    path.write_text(GAME)
    game = read_single_game(path)
    assert game is not None
    assert game.headers["White"] == "A"


def test_multi_game_file_is_rejected_not_silently_truncated(tmp_path, capsys):
    path = tmp_path / "1.pgn"
    path.write_text(GAME + "\n" + GAME)
    assert read_single_game(path) is None
    assert "more than one game" in capsys.readouterr().err


def test_empty_file_is_rejected(tmp_path):
    path = tmp_path / "1.pgn"
    path.write_text("")
    assert read_single_game(path) is None


def test_load_dotenv_never_overrides_real_environment(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# comment\nPGN_TEST_A='quoted'\nPGN_TEST_B=from_file\nnot a pair\n")
    monkeypatch.delenv("PGN_TEST_A", raising=False)
    monkeypatch.setenv("PGN_TEST_B", "from_env")
    load_dotenv(env)
    assert os.environ["PGN_TEST_A"] == "quoted"
    assert os.environ["PGN_TEST_B"] == "from_env"
    monkeypatch.delenv("PGN_TEST_A")


def test_load_dotenv_missing_file_is_fine(tmp_path):
    load_dotenv(tmp_path / "nope")
