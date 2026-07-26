"""수집 소스 정의와 로더.

소스 목록은 코드가 아니라 `design_digest/sources.toml` 에 있다.
매체를 추가/제거할 때 파이썬 파일을 건드릴 필요가 없다.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from ..models import CATEGORY_GENERAL


@dataclass
class FeedSource:
    """RSS/Atom 피드 하나."""

    name: str
    url: str
    #: 이 매체 글의 기본 카테고리 (본문 분류가 애매할 때 쓰는 힌트)
    category: str = CATEGORY_GENERAL
    #: 랭킹 가중치. 신뢰하는 매체를 조금 더 위로 올릴 때 쓴다.
    weight: float = 1.0
    #: 피드 이미지를 이미지 수집 후보로 쓸지
    use_images: bool = True


@dataclass
class RedditSource:
    """이미지 수집용 서브레딧."""

    subreddit: str
    label: str = ""
    #: 이 점수 미만은 '인기'로 보지 않는다
    min_score: int = 50
    limit: int = 25

    def __post_init__(self) -> None:
        if not self.label:
            self.label = f"r/{self.subreddit}"


@dataclass
class HackerNewsSource:
    """Hacker News 인기 신호 설정."""

    enabled: bool = True
    queries: list[str] = field(default_factory=lambda: ["design", "typography", "user experience"])
    min_points: int = 20
    hits_per_query: int = 40


@dataclass
class SourceSet:
    feeds: list[FeedSource] = field(default_factory=list)
    reddits: list[RedditSource] = field(default_factory=list)
    hackernews: HackerNewsSource = field(default_factory=HackerNewsSource)

    def __len__(self) -> int:
        return len(self.feeds) + len(self.reddits) + (1 if self.hackernews.enabled else 0)


def load_sources(path: Path | str) -> SourceSet:
    """sources.toml 을 읽어 소스 목록을 만든다."""
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))

    feeds = [
        FeedSource(
            name=entry["name"],
            url=entry["url"],
            category=entry.get("category", CATEGORY_GENERAL),
            weight=float(entry.get("weight", 1.0)),
            use_images=bool(entry.get("use_images", True)),
        )
        for entry in data.get("feed", [])
        if entry.get("url")
    ]

    reddits = [
        RedditSource(
            subreddit=entry["subreddit"],
            label=entry.get("label", ""),
            min_score=int(entry.get("min_score", 50)),
            limit=int(entry.get("limit", 25)),
        )
        for entry in data.get("reddit", [])
        if entry.get("subreddit")
    ]

    hn_data = data.get("hackernews", {})
    hackernews = HackerNewsSource(
        enabled=bool(hn_data.get("enabled", True)),
        queries=list(hn_data.get("queries", HackerNewsSource().queries)),
        min_points=int(hn_data.get("min_points", 20)),
        hits_per_query=int(hn_data.get("hits_per_query", 40)),
    )

    return SourceSet(feeds=feeds, reddits=reddits, hackernews=hackernews)
