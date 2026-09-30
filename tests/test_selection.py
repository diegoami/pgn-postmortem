"""F-1.3's deterministic selection contract, without Stockfish."""

from copy import deepcopy
from pathlib import Path

import pytest

from pgn_postmortem import Collection
from pgn_postmortem.collection import CollectedGame
from pgn_postmortem.selection import (
    ChapterWeights,
    SelectionOptions,
    SelectionWeights,
    features,
    select_chapters,
)
from pgn_postmortem.site import make_articles


def fixture_path():
    return Path(__file__).parent / "fixtures" / "site" / "analyzed"


def test_default_weights_are_bound_and_invalid_options_fail():
    options = SelectionOptions()
    assert options.chapter_size == 5 and options.minimum_length == 20
    assert options.weights.wins.player_accuracy == 0.30
    with pytest.raises(ValueError):
        ChapterWeights(0.9, 0, 0, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        SelectionOptions(chapter_size=0)
    with pytest.raises(ValueError):
        SelectionOptions(minimum_length=0)
    custom = ChapterWeights(1, 0, 0, 0, 0, 0, 0)
    assert SelectionOptions(weights=SelectionWeights(wins=custom)).weights.wins == custom


def test_marker_only_and_partial_analysis_are_not_selection_candidates():
    collection = Collection.read(fixture_path(), keep_analysis=True)
    item = next(iter(collection))
    marker_only = deepcopy(item.game)
    for node in marker_only.mainline():
        node.set_eval(None)
    article = make_articles([CollectedGame(item.id, marker_only, item.origin)])[0]
    assert features(article, {"ada example"}, 1) is None

    partial = deepcopy(item.game)
    next(iter(partial.mainline())).set_eval(None)
    article = make_articles([CollectedGame(item.id, partial, item.origin)])[0]
    assert features(article, {"ada example"}, 1) is None


def test_selection_is_mutually_exclusive_and_deterministic():
    collection = Collection.read(fixture_path(), keep_analysis=True)
    articles = make_articles(collection)
    first = select_chapters(articles, {"ada example"}, SelectionOptions(minimum_length=1))
    second = select_chapters(articles, {"ada example"}, SelectionOptions(minimum_length=1))
    assert first == second
    ids = [article.item.id for games in first.values() for article, _ in games]
    assert len(ids) == len(set(ids))
