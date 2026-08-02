"""Hacker News 인기 신호.

같은 글이라도 '얼마나 언급됐는지'를 알아야 위로 올릴 수 있다.
HN Algolia 검색 API(무인증)로 최근 디자인 관련 스토리를 가져와서

1. 그 자체를 읽을거리 후보로 쓰고,
2. RSS 로 모은 글과 URL 이 겹치면 포인트를 인기 점수로 붙여준다.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any
from urllib.parse import quote_plus

from ..config import Config
from ..models import Article
from ..net import fetch_json
from ..util import normalize_url
from . import HackerNewsSource

log = logging.getLogger(__name__)

SEARCH_URL = (
    "https://hn.algolia.com/api/v1/search"
    "?query={query}&tags=story&numericFilters=created_at_i>{since},points>={points}"
    "&hitsPerPage={hits}"
)
ITEM_URL = "https://news.ycombinator.com/item?id={object_id}"


def parse_hits(payload: dict[str, Any], min_points: int) -> list[Article]:
    articles: list[Article] = []
    for hit in payload.get("hits", []):
        title = (hit.get("title") or "").strip()
        if not title:
            continue
        points = int(hit.get("points") or 0)
        if points < min_points:
            continue

        object_id = hit.get("objectID", "")
        discussion = ITEM_URL.format(object_id=object_id)
        url = (hit.get("url") or "").strip() or discussion
        comments = int(hit.get("num_comments") or 0)

        created_at = hit.get("created_at_i")
        published = (
            dt.datetime.fromtimestamp(float(created_at), tz=dt.timezone.utc) if created_at else None
        )
        articles.append(
            Article(
                title=title,
                url=url,
                source="Hacker News",
                published=published,
                summary=(hit.get("story_text") or "")[:400],
                popularity=points,
                popularity_note=f"HN {points}점 · 댓글 {comments}개",
            )
        )
    return articles


def collect_stories(source: HackerNewsSource, config: Config) -> list[Article]:
    """설정된 검색어별로 최근 인기 스토리를 모은다 (URL 기준 중복 제거)."""
    since = int((dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=config.lookback_hours)).timestamp())
    collected: dict[str, Article] = {}

    for query in source.queries:
        url = SEARCH_URL.format(
            query=quote_plus(query),
            since=since,
            points=source.min_points,
            hits=source.hits_per_query,
        )
        payload = fetch_json(
            url,
            timeout=config.http_timeout,
            retries=config.http_retries,
            user_agent=config.user_agent,
        )
        for article in parse_hits(payload, source.min_points):
            key = normalize_url(article.url)
            existing = collected.get(key)
            if existing is None or article.popularity > existing.popularity:
                collected[key] = article

    log.debug("Hacker News: %d개 스토리", len(collected))
    return list(collected.values())


def popularity_index(stories: list[Article]) -> dict[str, Article]:
    """URL -> HN 스토리 사전. 다른 소스의 글에 인기 점수를 붙일 때 쓴다."""
    return {normalize_url(story.url): story for story in stories if story.url}
