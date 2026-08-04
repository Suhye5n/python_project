"""수집 소스 정의와 로더.

소스 목록은 코드가 아니라 `design_digest/sources.toml` 에 있다.
매체를 추가/제거할 때 파이썬 파일을 건드릴 필요가 없다.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from ..focus import Focus, from_toml as focus_from_toml
from ..models import CATEGORY_GENERAL


#: 피드가 글 목록인지 이미지 갤러리인지
KIND_ARTICLE = "article"
KIND_IMAGE = "image"


@dataclass
class FeedSource:
    """RSS/Atom 피드 하나.

    `kind = "image"` 로 두면 항목을 글이 아니라 이미지로 취급한다.
    RSSHub 처럼 인스타그램·핀터레스트·비핸스를 RSS 로 바꿔주는 게이트웨이를
    붙일 때 이 모드를 쓴다.
    """

    name: str
    url: str
    #: 이 매체 글의 기본 카테고리 (본문 분류가 애매할 때 쓰는 힌트)
    category: str = CATEGORY_GENERAL
    #: 랭킹 가중치. 신뢰하는 매체를 조금 더 위로 올릴 때 쓴다.
    weight: float = 1.0
    #: 피드 이미지를 이미지 수집 후보로 쓸지
    use_images: bool = True
    kind: str = KIND_ARTICLE
    #: 인증이 필요한 게이트웨이용. 값이 아니라 '환경변수 이름'을 적는다.
    cookie_env: str = ""

    @property
    def is_image_feed(self) -> bool:
        return self.kind == KIND_IMAGE


@dataclass
class RedditSource:
    """이미지 수집용 서브레딧."""

    subreddit: str
    label: str = ""
    #: 이 점수 미만은 '인기'로 보지 않는다
    min_score: int = 50
    limit: int = 25
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.label:
            self.label = f"r/{self.subreddit}"


@dataclass
class ScrapeSource:
    """공개 API 가 없는 사이트에서 이미지를 긁어오는 설정.

    사이트마다 파이썬 코드를 따로 쓰지 않는다. 추출 전략과 필드 위치만
    TOML 에 적어두고, 사이트가 구조를 바꾸면 설정만 고친다.
    """

    name: str
    url: str
    #: json | embedded_json | html | og
    strategy: str = "og"
    #: json 계열: 항목 배열까지의 점(.) 경로. 비우면 자동 탐색한다.
    json_path: str = ""
    #: embedded_json 전략에서 찾을 script 표식 (예: __NEXT_DATA__)
    marker: str = ""
    #: html 전략에서 항목으로 볼 링크의 URL 조각 (예: /shots/)
    link_pattern: str = ""
    #: 항목 -> ImageItem 필드 매핑. json 계열에서만 쓴다.
    fields: dict[str, str] = field(default_factory=dict)
    #: 항목에 주소가 없고 id/slug 만 있을 때 작품 페이지 주소를 조립하는 틀.
    #: 예: "https://www.behance.net/gallery/{id}/{slug}"
    link_template: str = ""
    #: 상대경로를 절대경로로 만들 때 쓸 기준 주소
    base_url: str = ""
    limit: int = 12
    min_popularity: int = 0
    weight: float = 1.0
    enabled: bool = True
    #: 목록 추출이 실패했을 때 페이지 대표 이미지(og:image)로 대신할지.
    #: 갤러리 페이지에서는 사이트 간판이 잡히므로 기본은 끔.
    og_fallback: bool = False
    #: 로그인이 필요한 사이트용. 값이 아니라 '환경변수 이름'을 적는다.
    cookie_env: str = ""


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
    scrapes: list[ScrapeSource] = field(default_factory=list)
    hackernews: HackerNewsSource = field(default_factory=HackerNewsSource)
    #: 관심 분야 필터 (기본: 시각디자인)
    focus: Focus = field(default_factory=Focus)

    @property
    def article_feeds(self) -> list[FeedSource]:
        return [feed for feed in self.feeds if not feed.is_image_feed]

    @property
    def image_feeds(self) -> list[FeedSource]:
        return [feed for feed in self.feeds if feed.is_image_feed]

    def image_weights(self) -> dict[str, float]:
        """이미지 소스 이름 -> 가중치."""
        weights = {sub.label: sub.weight for sub in self.reddits}
        weights.update({feed.name: feed.weight for feed in self.image_feeds})
        weights.update({scrape.name: scrape.weight for scrape in self.scrapes})
        return weights

    def __len__(self) -> int:
        return (
            len(self.feeds)
            + len(self.reddits)
            + len([s for s in self.scrapes if s.enabled])
            + (1 if self.hackernews.enabled else 0)
        )


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
            kind=entry.get("kind", KIND_ARTICLE),
            cookie_env=entry.get("cookie_env", ""),
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
            weight=float(entry.get("weight", 1.0)),
        )
        for entry in data.get("reddit", [])
        if entry.get("subreddit")
    ]

    scrapes = [
        ScrapeSource(
            name=entry["name"],
            url=entry["url"],
            strategy=entry.get("strategy", "og"),
            json_path=entry.get("json_path", ""),
            marker=entry.get("marker", ""),
            link_pattern=entry.get("link_pattern", ""),
            fields=dict(entry.get("fields", {})),
            base_url=entry.get("base_url", ""),
            limit=int(entry.get("limit", 12)),
            min_popularity=int(entry.get("min_popularity", 0)),
            weight=float(entry.get("weight", 1.0)),
            enabled=bool(entry.get("enabled", True)),
            og_fallback=bool(entry.get("og_fallback", False)),
            cookie_env=entry.get("cookie_env", ""),
        )
        for entry in data.get("scrape", [])
        if entry.get("url") and entry.get("name")
    ]

    hn_data = data.get("hackernews", {})
    hackernews = HackerNewsSource(
        enabled=bool(hn_data.get("enabled", True)),
        queries=list(hn_data.get("queries", HackerNewsSource().queries)),
        min_points=int(hn_data.get("min_points", 20)),
        hits_per_query=int(hn_data.get("hits_per_query", 40)),
    )

    return SourceSet(
        feeds=feeds,
        reddits=reddits,
        scrapes=scrapes,
        hackernews=hackernews,
        focus=focus_from_toml(data),
    )
