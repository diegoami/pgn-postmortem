"""Workspace configuration, read from a pgn-postmortem.toml file.

The directory holding the config file is the *workspace*: everything the
pipeline produces lives next to it, so a workspace can be any folder - a git
repo, a synced cloud folder, or just a directory on disk:

    pgn-postmortem.toml
    games/       one normalized PGN per game, fed by the configured sources
    analyzed/    the same games after the Stockfish pass
    site/        the generated book
    .cache/      downloaded archives, cloned repos, LLM responses

See examples/pgn-postmortem.toml for an annotated example.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_NAME = "pgn-postmortem.toml"


@dataclass
class AnalysisConfig:
    time: float = 0.3
    depth: int | None = None
    workers: int = 0  # 0 = one per CPU
    pv_length: int = 8
    inaccuracy_pct: float = 10.0
    mistake_pct: float = 20.0
    blunder_pct: float = 30.0


@dataclass
class LLMConfig:
    """Any OpenAI-compatible chat-completions endpoint (DeepSeek by default).
    The key itself is never stored in the config file, only the name of the
    environment variable holding it."""

    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    api_key_env: str = "DEEPSEEK_API_KEY"
    temperature: float = 0.7

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env) or None


@dataclass
class BookConfig:
    title: str = ""
    best: int = 12  # games per chapter
    min_moves: int = 20


@dataclass
class Config:
    workspace: Path
    player: str
    aliases: list[str]
    sources: list[dict]
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    llm: LLMConfig | None = None
    book: BookConfig = field(default_factory=BookConfig)

    @property
    def games_dir(self) -> Path:
        return self.workspace / "games"

    @property
    def analyzed_dir(self) -> Path:
        return self.workspace / "analyzed"

    @property
    def site_dir(self) -> Path:
        return self.workspace / "site"

    @property
    def cache_dir(self) -> Path:
        return self.workspace / ".cache"

    def is_player(self, name: str | None) -> bool:
        return bool(name) and name.strip().lower() in {a.lower() for a in [self.player, *self.aliases]}


def load_config(path: Path) -> Config:
    path = path.resolve()
    if path.is_dir():
        path = path / DEFAULT_CONFIG_NAME
    raw = tomllib.loads(path.read_text(encoding="utf-8"))

    player = raw.get("player", {})
    if not player.get("name"):
        raise ValueError(f"{path}: [player] name is required")
    sources = raw.get("sources", [])
    if not sources:
        raise ValueError(f"{path}: at least one [[sources]] entry is required")

    llm = LLMConfig(**raw["llm"]) if "llm" in raw else None
    return Config(
        workspace=path.parent,
        player=player["name"],
        aliases=list(player.get("aliases", [])),
        sources=sources,
        analysis=AnalysisConfig(**raw.get("analysis", {})),
        llm=llm,
        book=BookConfig(**raw.get("book", {})),
    )
