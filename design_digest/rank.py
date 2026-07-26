"""랭킹.

세 가지를 섞는다.
  - 인기도: HN 포인트 / 레딧 업보트 (로그 스케일 — 1만 업보트가 100배 중요하진 않다)
  - 신선도: 방금 올라온 글일수록 가산
  - 매체 가중치: sources.toml 의 weight

그리고 한 매체가 리포트를 도배하지 않도록 소스별 상한을 둔다.
"""

from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict

from .models import Article, ImageItem
from .util import utc_now

POPULARITY_FACTOR = 1.6
FRESHNESS_FACTOR = 2.0
IMAGE_BONUS = 0.4
SUMMARY_BONUS = 0.3


def _freshness(published: dt.datetime | None, now: dt.datetime, lookback_hours: int) -> float:
    """0(오래됨) ~ 1(방금). 날짜를 모르면 중간값."""
    if not published:
        return 0.4
    hours = (now - published).total_seconds() / 3600
    if hours < 0:  # 예약 발행 등으로 미래 시각이 찍힌 경우
        return 1.0
    return max(0.0, 1.0 - hours / max(lookback_hours, 1))


def score_article(
    article: Article,
    *,
    weight: float = 1.0,
    lookback_hours: int = 30,
    now: dt.datetime | None = None,
) -> float:
    now = now or utc_now()
    score = math.log1p(max(article.popularity, 0)) * POPULARITY_FACTOR
    score += _freshness(article.published, now, lookback_hours) * FRESHNESS_FACTOR
    if article.image_url:
        score += IMAGE_BONUS
    if len(article.summary) > 80:
        score += SUMMARY_BONUS
    return round(score * weight, 4)


def score_image(
    item: ImageItem,
    *,
    lookback_hours: int = 30,
    now: dt.datetime | None = None,
) -> float:
    now = now or utc_now()
    score = math.log1p(max(item.popularity, 0)) * POPULARITY_FACTOR
    # 댓글은 '언급이 많았다'는 신호라 별도로 조금 더 쳐준다.
    score += math.log1p(max(item.comments, 0)) * 0.6
    score += _freshness(item.published, now, lookback_hours) * FRESHNESS_FACTOR
    return round(score, 4)


def rank_articles(
    articles: list[Article],
    *,
    weights: dict[str, float] | None = None,
    lookback_hours: int = 30,
    now: dt.datetime | None = None,
) -> list[Article]:
    weights = weights or {}
    now = now or utc_now()
    for article in articles:
        article.score = score_article(
            article,
            weight=weights.get(article.source, 1.0),
            lookback_hours=lookback_hours,
            now=now,
        )
    return sorted(articles, key=lambda a: a.score, reverse=True)


def rank_images(
    items: list[ImageItem],
    *,
    lookback_hours: int = 30,
    now: dt.datetime | None = None,
) -> list[ImageItem]:
    now = now or utc_now()
    for item in items:
        item.score = score_image(item, lookback_hours=lookback_hours, now=now)
    return sorted(items, key=lambda i: i.score, reverse=True)


def select_articles(
    ranked: list[Article],
    *,
    per_category: int,
    per_source: int,
) -> list[Article]:
    """카테고리별·매체별 상한을 지키면서 뽑는다. 입력은 점수 내림차순."""
    category_counts: dict[str, int] = defaultdict(int)
    source_counts: dict[str, int] = defaultdict(int)
    picked: list[Article] = []

    for article in ranked:
        if category_counts[article.category] >= per_category:
            continue
        if source_counts[article.source] >= per_source:
            continue
        picked.append(article)
        category_counts[article.category] += 1
        source_counts[article.source] += 1
    return picked


def select_images(ranked: list[ImageItem], *, limit: int, per_source: int = 3) -> list[ImageItem]:
    source_counts: dict[str, int] = defaultdict(int)
    picked: list[ImageItem] = []
    for item in ranked:
        if len(picked) >= limit:
            break
        if source_counts[item.source] >= per_source:
            continue
        picked.append(item)
        source_counts[item.source] += 1
    return picked
