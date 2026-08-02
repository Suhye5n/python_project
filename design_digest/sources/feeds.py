"""RSS / Atom 피드 파서.

feedparser 같은 외부 의존성 없이 `xml.etree` 로 직접 읽는다.
피드마다 네임스페이스를 제각각 쓰기 때문에 태그는 네임스페이스를 떼고
지역명(local name)으로만 비교한다.
"""

from __future__ import annotations

import logging
import os
import re
from xml.etree import ElementTree

from ..config import Config
from ..models import Article, ImageItem
from ..net import fetch_bytes
from ..util import parse_datetime, strip_html, summarize
from . import FeedSource

log = logging.getLogger(__name__)

FEED_ACCEPT = "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8"
_IMG_SRC_RE = re.compile(r"""<img[^>]+src\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
# 1x1 추적 픽셀이나 아이콘은 이미지 후보에서 제외한다.
_BAD_IMAGE_HINT = re.compile(r"(?i)(pixel|spacer|1x1|avatar|icon|logo|badge|feedburner|gravatar)")


class FeedError(RuntimeError):
    """피드를 읽거나 해석하지 못했을 때."""


def _local(tag: str) -> str:
    """`{namespace}tag` 에서 `tag` 만 소문자로."""
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1].lower()


def _children(element: ElementTree.Element, *names: str):
    wanted = {n.lower() for n in names}
    for child in element:
        if _local(child.tag) in wanted:
            yield child


def _first(element: ElementTree.Element, *names: str) -> ElementTree.Element | None:
    return next(_children(element, *names), None)


def _text(element: ElementTree.Element | None) -> str:
    if element is None:
        return ""
    # itertext() 로 감싸야 <description> 안에 인라인 태그가 있어도 살아남는다.
    return "".join(element.itertext()).strip()


def _entry_link(entry: ElementTree.Element) -> str:
    """RSS 의 <link>텍스트</link> 와 Atom 의 <link href=...> 를 모두 처리."""
    fallback = ""
    for link in _children(entry, "link"):
        href = (link.get("href") or "").strip()
        rel = (link.get("rel") or "alternate").lower()
        if href:
            if rel == "alternate":
                return href
            fallback = fallback or href
            continue
        text = _text(link)
        if text:
            return text
    if fallback:
        return fallback
    # 마지막 수단: <guid isPermaLink="true">
    guid = _first(entry, "guid", "id")
    text = _text(guid)
    return text if text.startswith("http") else ""


def _entry_body(entry: ElementTree.Element) -> str:
    """요약에 쓸 본문 후보 중 가장 내용이 많은 것."""
    candidates = [
        _text(node)
        for node in _children(entry, "encoded", "content", "description", "summary", "subtitle")
    ]
    candidates = [c for c in candidates if c]
    return max(candidates, key=len) if candidates else ""


def _entry_author(entry: ElementTree.Element) -> str:
    author = _first(entry, "author", "creator")
    if author is None:
        return ""
    name = _first(author, "name")
    return strip_html(_text(name) or _text(author))[:80]


def _entry_image(entry: ElementTree.Element, body: str) -> str:
    """media:content / media:thumbnail / enclosure / 본문 <img> 순으로 탐색."""
    candidates: list[str] = []

    for node in _children(entry, "content", "thumbnail"):
        url = (node.get("url") or "").strip()
        medium = (node.get("medium") or "").lower()
        mime = (node.get("type") or "").lower()
        if url and (medium == "image" or mime.startswith("image") or not (medium or mime)):
            candidates.append(url)

    for node in _children(entry, "enclosure"):
        url = (node.get("url") or "").strip()
        if url and (node.get("type") or "").lower().startswith("image"):
            candidates.append(url)

    for group in _children(entry, "group"):
        for node in _children(group, "content", "thumbnail"):
            url = (node.get("url") or "").strip()
            if url:
                candidates.append(url)

    candidates.extend(_IMG_SRC_RE.findall(body))

    for url in candidates:
        if url.startswith("http") and not _BAD_IMAGE_HINT.search(url):
            return url
    return ""


def parse_feed(xml_bytes: bytes | str, source: FeedSource) -> list[Article]:
    """피드 XML을 Article 목록으로."""
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise FeedError(f"XML 파싱 실패: {exc}") from exc

    # RSS 는 <rss><channel><item>, Atom 은 <feed><entry>
    container = _first(root, "channel") or root
    entries = list(_children(container, "item", "entry"))
    if not entries:
        entries = list(_children(root, "item", "entry"))

    articles: list[Article] = []
    for entry in entries:
        title = strip_html(_text(_first(entry, "title")))
        url = _entry_link(entry)
        if not title or not url.startswith("http"):
            continue

        body = _entry_body(entry)
        published = parse_datetime(
            _text(_first(entry, "pubdate", "published", "date", "updated", "modified")) or None
        )
        articles.append(
            Article(
                title=title,
                url=url,
                source=source.name,
                published=published,
                summary=summarize(body),
                author=_entry_author(entry),
                category=source.category,
                image_url=_entry_image(entry, body) if source.use_images else "",
            )
        )
    return articles


def to_image_items(articles: list[Article], source: FeedSource) -> list[ImageItem]:
    """이미지 피드(`kind = "image"`)의 항목을 이미지로 변환한다.

    RSSHub 같은 게이트웨이가 인스타그램/핀터레스트/비핸스를 RSS 로 바꿔줄 때,
    각 항목은 '글'이 아니라 '작업물 한 점'이다. 인기 수치는 대개 없으므로
    소스 가중치로 순위를 조절한다.
    """
    items = []
    for article in articles:
        if not article.image_url:
            continue
        items.append(
            ImageItem(
                title=article.title,
                url=article.url,
                image_url=article.image_url,
                source=source.name,
                published=article.published,
                author=article.author,
                popularity_note=source.name,
            )
        )
    return items


def collect_feed(source: FeedSource, config: Config) -> list[Article]:
    """피드 하나를 받아 글 목록으로. 네트워크 오류는 그대로 올린다."""
    headers = {}
    if source.cookie_env:
        cookie = os.environ.get(source.cookie_env, "")
        if cookie:
            headers["Cookie"] = cookie

    body, _ = fetch_bytes(
        source.url,
        timeout=config.http_timeout,
        retries=config.http_retries,
        user_agent=config.user_agent,
        accept=FEED_ACCEPT,
        headers=headers or None,
        max_bytes=8 * 1024 * 1024,
    )
    articles = parse_feed(body, source)
    log.debug("%s: %d개 항목", source.name, len(articles))
    return articles


def collect_image_feed(source: FeedSource, config: Config) -> list[ImageItem]:
    """이미지 피드 하나를 받아 이미지 목록으로."""
    return to_image_items(collect_feed(source, config), source)
