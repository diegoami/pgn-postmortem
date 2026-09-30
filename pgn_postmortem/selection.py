"""Deterministic featured-game selection for the book layer."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pgn_postmortem.collection import ANALYSIS_HEADER

if TYPE_CHECKING:
    from pgn_postmortem.site import Article, MoveReview


CHAPTERS = ("wins", "losses", "draws")
RESULTS = {"wins": "1-0", "losses": "0-1", "draws": "1/2-1/2"}


@dataclass(frozen=True)
class ChapterWeights:
    player_accuracy: float
    opponent_accuracy: float
    opponent_strength: float
    fight: float
    recovery: float
    early_blunder_avoidance: float
    draw_save: float

    def __post_init__(self) -> None:
        values = (
            self.player_accuracy,
            self.opponent_accuracy,
            self.opponent_strength,
            self.fight,
            self.recovery,
            self.early_blunder_avoidance,
            self.draw_save,
        )
        if any(
            not isinstance(value, int | float)
            or isinstance(value, bool)
            or not math.isfinite(value)
            for value in values
        ):
            raise ValueError("selection weights must be finite numbers")
        if any(value < 0 for value in values) or not math.isclose(sum(values), 1.0, abs_tol=1e-9):
            raise ValueError("selection weights must be non-negative and sum to 1")


@dataclass(frozen=True)
class SelectionWeights:
    wins: ChapterWeights = field(
        default_factory=lambda: ChapterWeights(0.30, 0.15, 0.20, 0.15, 0.20, 0.0, 0.0)
    )
    losses: ChapterWeights = field(
        default_factory=lambda: ChapterWeights(0.35, 0.15, 0.20, 0.15, 0.0, 0.15, 0.0)
    )
    draws: ChapterWeights = field(
        default_factory=lambda: ChapterWeights(0.25, 0.15, 0.15, 0.20, 0.0, 0.0, 0.25)
    )


@dataclass(frozen=True)
class SelectionOptions:
    chapter_size: int = 5
    minimum_length: int = 20
    weights: SelectionWeights = field(default_factory=SelectionWeights)

    def __post_init__(self) -> None:
        if isinstance(self.chapter_size, bool) or not isinstance(self.chapter_size, int) or self.chapter_size < 1:
            raise ValueError("chapter_size must be an integer of at least 1")
        if isinstance(self.minimum_length, bool) or not isinstance(self.minimum_length, int) or self.minimum_length < 1:
            raise ValueError("minimum_length must be an integer of at least 1")
        if not isinstance(self.weights, SelectionWeights):
            raise ValueError("weights must be a SelectionWeights value")


DEFAULT_SELECTION_OPTIONS = SelectionOptions()


@dataclass(frozen=True)
class SelectionFeatures:
    player_accuracy: float
    opponent_accuracy: float
    opponent_strength: float
    fight: float
    recovery: float
    early_blunder_avoidance: float
    draw_save: float

    def score(self, weights: ChapterWeights) -> float:
        return sum(
            value * weight
            for value, weight in zip(
                (
                    self.player_accuracy,
                    self.opponent_accuracy,
                    self.opponent_strength,
                    self.fight,
                    self.recovery,
                    self.early_blunder_avoidance,
                    self.draw_save,
                ),
                (
                    weights.player_accuracy,
                    weights.opponent_accuracy,
                    weights.opponent_strength,
                    weights.fight,
                    weights.recovery,
                    weights.early_blunder_avoidance,
                    weights.draw_save,
                ),
                strict=True,
            )
        )


def _names(names: set[str] | frozenset[str]) -> set[str]:
    return {name.strip().casefold() for name in names if name.strip()}


def _own_colors(article: Article, names: set[str]) -> set[bool]:
    return {
        color
        for color, key in ((True, "White"), (False, "Black"))
        if (article.game.headers.get(key) or "").strip().casefold() in names
    }


def _complete_analysis(article: Article) -> bool:
    if ANALYSIS_HEADER not in article.game.headers:
        return False
    return all(node.board().is_game_over() or node.eval() is not None for node in article.game.mainline())


def _player_chances(review: MoveReview, own: set[bool]) -> tuple[float, float] | None:
    if review.before is None or review.after is None:
        return None
    before, after = review.before, review.after
    if review.mover not in own:
        before, after = 100 - before, 100 - after
    return before, after


def features(article: Article, names: set[str], minimum_length: int) -> SelectionFeatures | None:
    """Return features for a complete, analyzed player's game, else ``None``."""
    names = _names(names)
    own = _own_colors(article, names)
    if not own or not _complete_analysis(article):
        return None
    reviews = article.reviews
    player = [
        review for review in reviews if review.mover in own and review.before is not None and review.after is not None
    ]
    opponent = [
        review
        for review in reviews
        if review.mover not in own and review.before is not None and review.after is not None
    ]
    player_accuracy = 1 - (sum(review.loss for review in player) / len(player) if player else 50) / 100
    opponent_accuracy = 1 - (sum(review.loss for review in opponent) / len(opponent) if opponent else 50) / 100
    ratings = []
    if own == {True}:
        ratings.append(article.game.headers.get("BlackElo"))
    elif own == {False}:
        ratings.append(article.game.headers.get("WhiteElo"))
    rating = next((int(value) for value in ratings if value and value.isascii() and value.isdigit()), None)
    opponent_strength = max(0.0, min(1.0, (rating - 1800) / 600)) if rating is not None else 0.5
    plies = sum(1 for _ in article.game.mainline_moves())
    fight = max(0.0, min(1.0, (plies - 2 * minimum_length) / (4 * minimum_length)))
    losses = [review.loss for review in player if review.node.ply() <= 20]
    early_blunder_avoidance = 1 - (max(losses, default=50) / 100)
    chances = [_player_chances(review, own) for review in reviews]
    recovery = max(
        (pair[1] - pair[0] for pair in chances if pair and pair[0] < 40), default=0
    ) / 100
    recovery = max(0.0, min(1.0, recovery))
    draw_save = recovery if article.result == "1/2-1/2" else 0.0
    return SelectionFeatures(
        max(0.0, min(1.0, player_accuracy)),
        max(0.0, min(1.0, opponent_accuracy)),
        opponent_strength,
        fight,
        recovery,
        max(0.0, min(1.0, early_blunder_avoidance)),
        draw_save,
    )


def select_chapters(
    articles: list[Article], names: set[str], options: SelectionOptions
) -> dict[str, list[tuple[Article, float]]]:
    """Rank eligible games into mutually exclusive win/loss/draw chapters."""
    selected: dict[str, list[tuple[Article, float]]] = {chapter: [] for chapter in CHAPTERS}
    claimed: set[str] = set()
    for chapter in CHAPTERS:
        weights = getattr(options.weights, chapter)
        candidates = []
        for position, article in enumerate(articles):
            if article.item.id in claimed or article.result != RESULTS[chapter]:
                continue
            if sum(1 for _ in article.game.mainline_moves()) < 2 * options.minimum_length:
                continue
            feature = features(article, names, options.minimum_length)
            if feature is not None:
                candidates.append((feature.score(weights), position, article.filename, article.item.id, article))
        candidates.sort(key=lambda item: (-item[0], item[1], item[2], item[3]))
        for score, _, _, gid, article in candidates[: options.chapter_size]:
            selected[chapter].append((article, score))
            claimed.add(gid)
    return selected
