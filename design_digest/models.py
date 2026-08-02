"""다이제스트에서 오가는 데이터 구조.

수집기(sources) -> 분류/랭킹(classify, rank) -> 렌더링(render) 사이에서
공통으로 주고받는 값 객체들이다. 모두 JSON 직렬화가 가능하도록
`to_dict()` / `from_dict()` 를 갖는다.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any

# 글 분류 카테고리. 화면/메일에서 이 순서대로 노출된다.
CATEGORY_TREND = "trend"
CATEGORY_METHODOLOGY = "methodology"
CATEGORY_PHILOSOPHY = "philosophy"
CATEGORY_GENERAL = "general"

CATEGORY_ORDER = (
    CATEGORY_TREND,
    CATEGORY_METHODOLOGY,
    CATEGORY_PHILOSOPHY,
    CATEGORY_GENERAL,
)

CATEGORY_LABELS = {
    CATEGORY_TREND: "최신 디자인 트렌드",
    CATEGORY_METHODOLOGY: "디자인 방법론",
    CATEGORY_PHILOSOPHY: "디자인 철학 · 관점",
    CATEGORY_GENERAL: "그 외 읽을거리",
}


def _to_iso(value: dt.datetime | None) -> str | None:
    return value.isoformat() if value else None


def _from_iso(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


@dataclass
class Article:
    """수집한 글 한 편."""

    title: str
    url: str
    source: str
    published: dt.datetime | None = None
    summary: str = ""
    author: str = ""
    category: str = CATEGORY_GENERAL
    keywords: list[str] = field(default_factory=list)
    #: 외부 인기 신호(HN 포인트 등). 없으면 0.
    popularity: int = 0
    popularity_note: str = ""
    image_url: str = ""
    #: 최종 정렬 점수. rank 단계에서 채워진다.
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        data["published"] = _to_iso(self.published)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Article":
        data = dict(data)
        data["published"] = _from_iso(data.get("published"))
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class ImageItem:
    """인기 있었던 디자인 이미지 한 장."""

    title: str
    #: 원본 글/게시물 주소 (출처 확인용)
    url: str
    #: 실제 이미지 파일 주소
    image_url: str
    source: str
    published: dt.datetime | None = None
    author: str = ""
    #: 좋아요/업보트 수 같은 인기 지표
    popularity: int = 0
    comments: int = 0
    popularity_note: str = ""
    #: 메일에 인라인 첨부할 때 쓰는 로컬 파일 경로
    local_path: str = ""
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        data["published"] = _to_iso(self.published)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImageItem":
        data = dict(data)
        data["published"] = _from_iso(data.get("published"))
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Digest:
    """하루치 수집 결과 묶음."""

    date: dt.date
    generated_at: dt.datetime
    articles: list[Article] = field(default_factory=list)
    images: list[ImageItem] = field(default_factory=list)
    #: 수집 중 실패한 소스 목록 (소스명, 사유)
    failures: list[tuple[str, str]] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.articles and not self.images

    def by_category(self) -> dict[str, list[Article]]:
        """카테고리별 글 묶음을 정해진 순서대로 돌려준다 (빈 것은 제외)."""
        grouped: dict[str, list[Article]] = {}
        for category in CATEGORY_ORDER:
            items = [a for a in self.articles if a.category == category]
            if items:
                grouped[category] = items
        return grouped

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "generated_at": self.generated_at.isoformat(),
            "articles": [a.to_dict() for a in self.articles],
            "images": [i.to_dict() for i in self.images],
            "failures": [list(f) for f in self.failures],
            "stats": self.stats,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Digest":
        generated_at = _from_iso(data.get("generated_at")) or dt.datetime.now(dt.timezone.utc)
        return cls(
            date=dt.date.fromisoformat(data["date"]),
            generated_at=generated_at,
            articles=[Article.from_dict(a) for a in data.get("articles", [])],
            images=[ImageItem.from_dict(i) for i in data.get("images", [])],
            failures=[tuple(f) for f in data.get("failures", [])],
            stats=data.get("stats", {}),
        )
