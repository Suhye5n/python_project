"""수집 → 분류 → 랭킹 → 다이제스트 조립.

이 모듈은 '무엇을 모을지'(sources)와 '어떻게 보여줄지'(render, mailer) 사이의
가운데 토막이다. 네트워크 실패는 개별 소스 단위로 삼키고 실패 목록에 남긴다.
하나가 죽었다고 그날 리포트 전체를 날릴 이유는 없다.
"""

from __future__ import annotations

import datetime as dt
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable
from zoneinfo import ZoneInfo

from . import classify, rank
from .config import Config
from .models import Article, Digest, ImageItem
from .media import download_all
from .net import FetchError
from .sources import SourceSet, load_sources
from .sources.feeds import FeedError, collect_feed, collect_image_feed
from .sources.hackernews import collect_stories, popularity_index
from .sources.reddit import collect_subreddit
from .sources.scrape import collect_scrape
from .storage import SeenStore
from .util import normalize_url, utc_now

log = logging.getLogger(__name__)

#: 인기 글 대표 이미지를 이미지 섹션에 넣을 때의 최소 인기 점수
ARTICLE_IMAGE_MIN_POPULARITY = 1


def _within_window(article: Article, now: dt.datetime, lookback_hours: int) -> bool:
    """발행 시각을 모르는 글은 통과시킨다 (중복 제거가 뒤에서 걸러준다)."""
    if article.published is None:
        return True
    return (now - article.published) <= dt.timedelta(hours=lookback_hours)


def collect_articles(
    sources: SourceSet, config: Config, failures: list[tuple[str, str]]
) -> list[Article]:
    """글 피드를 병렬로 훑는다."""
    articles: list[Article] = []
    feeds = sources.article_feeds
    if not feeds:
        return articles

    workers = max(1, min(config.max_workers, len(feeds)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(collect_feed, feed, config): feed for feed in feeds}
        for future in as_completed(futures):
            feed = futures[future]
            try:
                articles.extend(future.result())
            except (FetchError, FeedError) as exc:
                log.warning("%s 수집 실패: %s", feed.name, exc)
                failures.append((feed.name, str(exc)))
            except Exception as exc:  # 소스 하나 때문에 전체가 죽지 않도록
                log.exception("%s 처리 중 예외", feed.name)
                failures.append((feed.name, f"예상치 못한 오류: {exc}"))
    return articles


def collect_hn(
    sources: SourceSet, config: Config, failures: list[tuple[str, str]]
) -> list[Article]:
    if not sources.hackernews.enabled:
        return []
    try:
        return collect_stories(sources.hackernews, config)
    except FetchError as exc:
        log.warning("Hacker News 수집 실패: %s", exc)
        failures.append(("Hacker News", str(exc)))
        return []


def image_jobs(sources: SourceSet, config: Config) -> list[tuple[str, Callable[[], list[ImageItem]]]]:
    """이미지 소스 세 종류를 (이름, 실행함수) 형태로 통일해서 늘어놓는다.

    레딧처럼 인기 수치가 붙는 곳, RSSHub 같은 이미지 피드, 그리고 API 가 없어
    직접 긁는 사이트를 같은 방식으로 돌리기 위한 어댑터.
    """
    jobs: list[tuple[str, Callable[[], list[ImageItem]]]] = []
    for sub in sources.reddits:
        jobs.append((sub.label, lambda s=sub: collect_subreddit(s, config)))
    for feed in sources.image_feeds:
        jobs.append((feed.name, lambda f=feed: collect_image_feed(f, config)))
    for scrape in sources.scrapes:
        if scrape.enabled:
            jobs.append((scrape.name, lambda s=scrape: collect_scrape(s, config)))
    return jobs


def collect_images(
    sources: SourceSet, config: Config, failures: list[tuple[str, str]]
) -> list[ImageItem]:
    images: list[ImageItem] = []
    jobs = image_jobs(sources, config)
    if not jobs:
        return images

    workers = max(1, min(config.max_workers, len(jobs)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(job): name for name, job in jobs}
        for future in as_completed(futures):
            name = futures[future]
            try:
                images.extend(future.result())
            except (FetchError, FeedError) as exc:
                log.warning("%s 수집 실패: %s", name, exc)
                failures.append((name, str(exc)))
            except Exception as exc:
                log.exception("%s 처리 중 예외", name)
                failures.append((name, f"예상치 못한 오류: {exc}"))
    return images


def enrich_with_popularity(articles: list[Article], stories: list[Article]) -> int:
    """RSS 로 모은 글에 HN 인기 점수를 붙인다. 붙은 개수를 돌려준다."""
    index = popularity_index(stories)
    matched = 0
    for article in articles:
        story = index.get(normalize_url(article.url))
        if story and story.popularity > article.popularity:
            article.popularity = story.popularity
            article.popularity_note = story.popularity_note
            matched += 1
    return matched


def dedupe_articles(articles: list[Article]) -> list[Article]:
    """같은 URL 이면 인기 점수가 높은 쪽(=정보가 많은 쪽)만 남긴다."""
    best: dict[str, Article] = {}
    for article in articles:
        key = normalize_url(article.url)
        if not key:
            continue
        current = best.get(key)
        if current is None or article.popularity > current.popularity:
            # 이미지/요약은 둘 중 있는 쪽을 살린다.
            if current is not None:
                article.image_url = article.image_url or current.image_url
                article.summary = article.summary or current.summary
            best[key] = article
    return list(best.values())


def images_from_articles(articles: list[Article], existing: list[ImageItem]) -> list[ImageItem]:
    """오늘 많이 언급된 글의 대표 이미지도 이미지 섹션에 넣는다."""
    taken = {normalize_url(item.image_url) for item in existing}
    extra: list[ImageItem] = []
    for article in articles:
        if not article.image_url or article.popularity < ARTICLE_IMAGE_MIN_POPULARITY:
            continue
        key = normalize_url(article.image_url)
        if key in taken:
            continue
        taken.add(key)
        extra.append(
            ImageItem(
                title=article.title,
                url=article.url,
                image_url=article.image_url,
                source=article.source,
                published=article.published,
                author=article.author,
                popularity=article.popularity,
                popularity_note=article.popularity_note or "오늘 많이 언급된 글",
            )
        )
    return extra


def build_digest(
    config: Config,
    sources: SourceSet | None = None,
    store: SeenStore | None = None,
    now: dt.datetime | None = None,
) -> Digest:
    """하루치 다이제스트를 만든다."""
    started = time.monotonic()
    now = now or utc_now()
    sources = sources or load_sources(config.sources_path)
    failures: list[tuple[str, str]] = []

    raw_articles = collect_articles(sources, config, failures)
    hn_stories = collect_hn(sources, config, failures)
    raw_images = collect_images(sources, config, failures)

    collected_count = len(raw_articles) + len(hn_stories)

    # 1) 기간 필터 -> 2) 인기 신호 결합 -> 3) 중복 제거
    fresh = [a for a in raw_articles if _within_window(a, now, config.lookback_hours)]
    enrich_with_popularity(fresh, hn_stories)
    candidates = dedupe_articles(fresh + hn_stories)

    # 4) 이미 보고한 것 제외
    if store and config.skip_seen:
        candidates = store.filter_new(candidates)
        raw_images = store.filter_new(raw_images)

    # 5) 분류 + 랭킹 + 선별
    classify.apply(candidates)
    weights = {feed.name: feed.weight for feed in sources.feeds}
    ranked = rank.rank_articles(
        candidates, weights=weights, lookback_hours=config.lookback_hours, now=now
    )
    articles = rank.select_articles(
        ranked,
        per_category=config.max_articles_per_category,
        per_source=config.max_per_source,
    )

    image_candidates = raw_images + images_from_articles(articles, raw_images)
    ranked_images = rank.rank_images(
        image_candidates,
        weights=sources.image_weights(),
        lookback_hours=config.lookback_hours,
        now=now,
    )
    images = rank.select_images(
        ranked_images,
        limit=config.max_images,
        guarantee=config.guaranteed_images_per_source,
    )

    # 6) 이미지 파일 확보 (메일 인라인 첨부용)
    downloaded = 0
    local_date = now.astimezone(ZoneInfo(config.timezone)).date()
    if config.download_images and images:
        downloaded = download_all(images, config.images_dir / local_date.isoformat(), config)
        # 못 받은 이미지는 원격 링크로라도 남겨둔다.

    if store:
        store.mark_seen(articles, "article")
        store.mark_seen(images, "image")

    digest = Digest(
        date=local_date,
        generated_at=now,
        articles=articles,
        images=images,
        failures=failures,
        stats={
            "collected_articles": collected_count,
            "collected_images": len(raw_images),
            "candidates": len(candidates),
            "selected_articles": len(articles),
            "selected_images": len(images),
            "downloaded_images": downloaded,
            "sources_total": len(sources),
            "sources_failed": len(failures),
            "hn_stories": len(hn_stories),
            "elapsed_sec": round(time.monotonic() - started, 2),
        },
    )
    log.info(
        "다이제스트 완성: 글 %d편 / 이미지 %d장 (소스 실패 %d건, %.1f초)",
        len(articles),
        len(images),
        len(failures),
        digest.stats["elapsed_sec"],
    )
    return digest
