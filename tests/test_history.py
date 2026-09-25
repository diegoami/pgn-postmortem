"""The reading history in the site's pages (ROADMAP.md, F-8), built from the
committed fixture in tests/fixtures/site/analyzed/ (no Stockfish).

  tests/golden/site/             the pages with the history (the default)
  tests/golden/site-no-history/  the same pages built with --no-history; when it
                                 was added it was byte for byte the golden set
                                 of main before F-8

The script's own behaviour is tested by the "script" gate,
``node --test 'tests/js/*.test.mjs'``, on the golden pages.
"""

import re
import tomllib
from fnmatch import fnmatch
from pathlib import Path

import chess
import pytest

from pgn_postmortem import Collection, critical_moments
from pgn_postmortem.cli import main
from pgn_postmortem.collection import file_stem
from pgn_postmortem.site import build_site, default_site_key, move_key
from tests.test_site import ANALYZED, EXPECTED_MOMENTS, PLAYER, REGENERATE, build, files, parse

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "pgn_postmortem" / "static" / "history.js"
GOLDEN = REPO_ROOT / "tests" / "golden" / "site"
GOLDEN_NO_HISTORY = REPO_ROOT / "tests" / "golden" / "site-no-history"
# Run from the repository root; it rewrites tests/golden/site-no-history/ in place.
REGENERATE_NO_HISTORY = (
    ".venv/bin/python -m pgn_postmortem site tests/fixtures/site/analyzed "
    '--player "Ada Example" --alias adaex --alias "Example, Ada" --no-history --out tests/golden/site-no-history'
)
HISTORY_DATA = {"data-site", "data-game", "data-move", "data-moves"}  # the only data- attributes the history adds
SCRIPT_ELEMENT = re.compile(r"<script\b([^>]*)>(.*?)</script>\n", re.S)


def script_bytes() -> str:
    return SCRIPT.read_bytes().decode("utf-8")


def pages(root: Path) -> list[Path]:
    return sorted(root.rglob("*.html"))


@pytest.fixture(scope="module")
def sites(tmp_path_factory):
    """The fixture site built with and without the history."""
    with_history, without = tmp_path_factory.mktemp("history"), tmp_path_factory.mktemp("no-history")
    build([ANALYZED], with_history, *PLAYER)
    build([ANALYZED], without, *PLAYER, "--no-history")
    return with_history, without


# --- the two golden sets ----------------------------------------------------------------


def test_the_pages_without_the_history_render_to_their_golden_set_byte_for_byte(sites):
    built, golden = files(sites[1]), files(GOLDEN_NO_HISTORY)
    hint = f"if the change to the pages is intended, regenerate the golden files: {REGENERATE_NO_HISTORY}"
    assert sorted(built) == sorted(golden), hint
    for name in built:
        assert built[name] == golden[name], f"{name} differs; {hint}"


def test_the_pages_with_the_history_are_the_default_golden_set(sites):
    built, golden = files(sites[0]), files(GOLDEN)
    hint = f"if the change to the pages is intended, regenerate the golden files: {REGENERATE}"
    assert sorted(built) == sorted(golden), hint
    for name in built:
        assert built[name] == golden[name], f"{name} differs; {hint}"


# --- the script -------------------------------------------------------------------------


def test_every_page_carries_the_script_inline_byte_identical_to_the_package_file(sites):
    script = script_bytes()
    checked = 0
    for page in pages(sites[0]):
        text = page.read_text(encoding="utf-8")
        found = SCRIPT_ELEMENT.findall(text)
        assert len(found) == 1, f"{page.name}: {len(found)} script elements"
        attributes, body = found[0]
        assert attributes == "", f"{page.name}: <script{attributes}>"  # no src, no type: inline, as written
        assert body == script, f"{page.name}: the inlined script differs from {SCRIPT.name}"
        assert text.count("<script") == 1, page.name
        checked += 1
    assert checked == 7  # the index and six articles


def test_the_script_makes_no_network_use_and_cannot_break_out_of_its_element():
    script = script_bytes()
    for word in ("fetch", "XMLHttpRequest", "sendBeacon", "WebSocket", "EventSource", "import(", "importScripts"):
        assert word not in script, word
    for url in (
        r"://",  # any scheme with a host
        r"(?i)\b(?:https?|ftp|wss?|file|data|blob|javascript|mailto|about):",  # a URL scheme
        r"(?i)\bwww\.",
        r"//[A-Za-z0-9-]+\.[A-Za-z]",  # a protocol-relative link (a comment starts "// ")
        r"(?i)\bsrc\b",
    ):
        assert not re.search(url, script), re.search(url, script).group(0)
    assert "</script" not in script.lower() and "<!--" not in script  # the page's parser would end it early
    assert "*" not in script  # no page shows a bare * outside its PGN section (tests/test_presumed_results.py)


def test_the_package_declares_the_script_as_package_data():
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = config["tool"]["setuptools"]["package-data"]["pgn_postmortem"]
    assert any(fnmatch("static/history.js", pattern) for pattern in patterns), patterns


def test_the_script_gate_has_test_files():
    # node --test with a glob that matches nothing passes with 0 tests: a false green
    tests = sorted((REPO_ROOT / "tests" / "js").glob("*.test.mjs"))
    assert tests, "no tests/js/*.test.mjs: the script gate would pass with 0 tests"
    assert all("test(" in path.read_text(encoding="utf-8") for path in tests)


# --- the markup -----------------------------------------------------------------------------


def test_the_history_section_is_hidden_in_the_static_html(sites):
    hidden = [(page.name, e) for page in pages(sites[0]) for e in parse(page).iter() if "hidden" in e.attrs]
    assert [(name, e.tag, e.attrs.get("id")) for name, e in hidden] == [("index.html", "section", "history")]
    section = hidden[0][1]
    # the list and the button are inside it, and the list is empty until the script fills it
    ids = [e.attrs["id"] for e in section.iter() if e.attrs.get("id")]
    assert ids == ["history", "history-recent", "history-clear"]
    assert not section.find_all("li")
    assert "Recently viewed" in section.text() and "Clear history" in section.text()


def test_the_data_attributes_are_the_named_ones_and_only_those(sites):
    collection = Collection.read(ANALYZED, keep_analysis=True)
    by_stem = {file_stem(item.game, item.id): item for item in collection}
    key = default_site_key("Games of Ada Example")
    index = parse(sites[0] / "index.html")
    entries = {}
    for page in pages(sites[0]):
        dom = parse(page)
        names = {name for e in dom.iter() for name in e.attrs if name.startswith("data-")} - {"data-r", "data-f"}
        assert names <= HISTORY_DATA, f"{page.name}: {names - HISTORY_DATA}"
        (html,) = dom.find_all("html")
        assert html.attrs["data-site"] == key, page.name
        placed = {(e.tag, name) for e in dom.iter() for name in e.attrs if name in HISTORY_DATA}
        if page.name == "index.html":
            assert placed == {("html", "data-site"), ("li", "data-game"), ("li", "data-moves")}
            continue
        item = by_stem[page.stem]
        (article,) = dom.find_all("article")
        assert article.attrs["data-game"] == item.id == item.game.headers["PostmortemId"]
        moves = [d.attrs["data-move"] for d in dom.find_all("details", "answer")]
        expected = [move_key(r.board_before) for r in critical_moments(item.game)]
        assert moves == expected, page.name
        entries[item.id] = " ".join(expected)
        assert placed <= {("html", "data-site"), ("article", "data-game"), ("details", "data-move")}
    listed = {li.attrs["data-game"]: li.attrs["data-moves"] for li in index.find_all("li") if "data-game" in li.attrs}
    assert listed == entries
    assert sorted(entries.values()) == sorted(" ".join(k) for k in [[], [], ["3b"], ["5b"], ["5w"], ["2b"]])
    assert len(EXPECTED_MOMENTS) == len(entries)


def test_move_keys_name_the_move_number_and_side():
    board = chess.Board()
    assert move_key(board) == "1w"
    board.push_san("e4")
    assert move_key(board) == "1b"
    board.push_san("e5")
    assert move_key(board) == "2w"


# --- the history adds nothing else ---------------------------------------------------------


def strip_history(text: str) -> str:
    """A page with the history, without the script, the hidden history
    containers and the history's data- attributes."""
    text = SCRIPT_ELEMENT.sub("", text)
    text = re.sub(r'<(section|div)\b[^>]*\bhidden\b[^>]*>.*?</\1>\n', "", text, flags=re.S)
    names = "|".join(sorted(HISTORY_DATA))
    return re.sub(rf' (?:{names})="[^"]*"', "", text)


def test_stripping_the_history_gives_exactly_the_pages_without_it(sites):
    with_history, without = files(sites[0]), files(sites[1])
    assert sorted(with_history) == sorted(without)  # the stylesheet included: no file only one of them has
    for name, content in with_history.items():
        if name.endswith(".html"):
            assert content != without[name], f"{name}: the history is missing"
            assert strip_history(content.decode("utf-8")) == without[name].decode("utf-8"), name
        else:
            assert content == without[name], f"{name}: the history changed it"


def test_without_the_history_the_pages_carry_none_of_it(sites):
    for page in pages(sites[1]):
        text = page.read_text(encoding="utf-8")
        assert "<script" not in text and 'id="history' not in text, page.name
        assert not any(f"{name}=" in text for name in HISTORY_DATA), page.name
        assert not any("hidden" in e.attrs for e in parse(page).iter()), page.name


# --- the site key -----------------------------------------------------------------------------


def test_the_default_site_key_comes_from_the_title():
    assert default_site_key("Games of Ada Example") == default_site_key("Games of Ada Example")
    assert default_site_key("Games of Ada Example").startswith("games-of-ada-example-")
    assert default_site_key("Games of Ada Example") != default_site_key("Games of ada example")  # only the same title
    assert re.fullmatch(r"[0-9a-f]{8}", default_site_key("Партии"))  # no ASCII word: the digest alone
    long = default_site_key("A " * 100)
    assert len(long) <= 64 and not long.startswith("-")


def site_key_of(out: Path) -> str:
    return parse(out / "index.html").find_all("html")[0].attrs["data-site"]


def test_the_site_key_follows_the_title_and_can_be_set(tmp_path):
    games = Collection.read(ANALYZED, keep_analysis=True)
    build_site(games, tmp_path / "a", title="Ada's <games>")
    assert site_key_of(tmp_path / "a") == default_site_key("Ada's <games>")
    build_site(games, tmp_path / "b", title="Ada's <games>", site_key="ada.book_2")
    assert site_key_of(tmp_path / "b") == "ada.book_2"
    build([ANALYZED], tmp_path / "c", *PLAYER, "--site-key", "ada-otb")
    for page in pages(tmp_path / "c"):
        assert parse(page).find_all("html")[0].attrs["data-site"] == "ada-otb", page.name


@pytest.mark.parametrize("key", ["", "-ada", "a:b", "a b", "ä", "a" * 65, "a/b", 7, b"ada"])
def test_an_invalid_site_key_is_rejected_before_anything_is_written(tmp_path, key):
    out = tmp_path / "site"
    with pytest.raises(ValueError, match="site_key"):
        build_site(Collection.read(ANALYZED, keep_analysis=True), out, site_key=key)
    with pytest.raises(ValueError, match="site_key"):
        build_site([], out, site_key=key, history=False)
    assert not out.exists()


def test_the_command_line_rejects_an_invalid_site_key(tmp_path, capsys):
    with pytest.raises(SystemExit) as exit_:
        main(["site", str(ANALYZED), "--site-key", "a:b", "--out", str(tmp_path / "site")])
    assert exit_.value.code == 2
    assert "site_key must be" in capsys.readouterr().err
    assert not (tmp_path / "site").exists()
