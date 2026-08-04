"""공개 API 가 없는 사이트에서 이미지를 긁어오는 범용 수집기.

Behance, Dribbble, 노트폴리오처럼 API 가 닫혔거나 없는 곳은 결국 사이트가
브라우저에 내려주는 데이터를 그대로 읽는 수밖에 없다. 문제는 그 구조가
자주 바뀐다는 것이다. 그래서 **사이트별 파이썬 코드를 쓰지 않는다.**
추출 전략과 필드 위치만 `sources.toml` 에 적고, 사이트가 바뀌면 설정만 고친다.

전략 네 가지:
  json          JSON 을 주는 주소에서 항목 배열을 꺼낸다
  embedded_json HTML 안에 박힌 `<script>` JSON(__NEXT_DATA__ 등)에서 꺼낸다
  html          카드 그리드의 <a>/<img> 짝을 훑는다
  og            페이지 대표 이미지(og:image) 한 장

경로를 못 찾으면 자동 탐색으로 넘어간다. 설정이 조금 틀려도 이미지처럼
생긴 배열을 스스로 찾아내므로, 사이트 개편에 한 번에 죽지는 않는다.
"""

from __future__ import annotations

import json
import logging
import os
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit

from ..config import Config
from ..models import ImageItem
from ..net import fetch_text
from ..util import parse_datetime, strip_html
from . import ScrapeSource

log = logging.getLogger(__name__)

HTML_ACCEPT = "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"
#: 이미지 후보로 볼 확장자/경로 힌트
_IMAGE_HINT = re.compile(r"(?i)\.(jpe?g|png|webp|avif|gif)(\?|$)|/image|/photo|cdn")
#: 아이콘·로고·추적픽셀 배제
_BAD_IMAGE = re.compile(r"(?i)(sprite|pixel|spacer|1x1|avatar|icon|logo|badge|placeholder|blank)")
#: 사이트가 공유용으로 하나 걸어두는 대표 이미지. 콘텐츠가 아니라 간판이라
#: 이걸 집으면 매일 같은 그림이 리포트에 실린다.
_PLACEHOLDER_IMAGE = re.compile(r"(?i)(/seo/|[-_/]og[-_.]|opengraph|share[-_]image|default|standard)")
#: "1,234" "1.2k" "3.4M" 같은 표기
_NUMBER = re.compile(r"(?i)^\s*([\d,.]+)\s*([km])?\s*$")
#: 이미지 URL 을 담고 있을 법한 키 이름 (자동 탐색용)
_IMAGE_KEYS = ("image", "img", "cover", "thumb", "thumbnail", "picture", "src", "url_m", "media")
#: 제목 / 링크 / 인기수치가 들어 있을 법한 키 이름
_TITLE_KEYS = {"name", "title", "headline", "caption", "description", "text"}
_LINK_KEYS = {"url", "permalink", "href", "link", "slug", "path", "uri", "url_path", "shorturl"}
_SCORE_KEYS = {
    "likecount", "likes", "like", "appreciations", "appreciationcount", "saves", "savecount",
    "hearts", "votes", "score", "favorites", "favoritecount", "reactions", "viewcount", "views",
}
TARGET_WIDTH = 1080


# --------------------------------------------------------------- 값 헬퍼


def parse_count(value: Any) -> int:
    """'1,234' / '1.2k' / 3400 을 정수로."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str):
        return 0
    match = _NUMBER.match(value)
    if not match:
        return 0
    number, suffix = match.groups()
    try:
        amount = float(number.replace(",", ""))
    except ValueError:
        return 0
    if suffix and suffix.lower() == "k":
        amount *= 1_000
    elif suffix and suffix.lower() == "m":
        amount *= 1_000_000
    return int(amount)


def dig(data: Any, path: str) -> Any:
    """`a.b.0.c` 형태의 점 경로로 중첩 구조를 따라간다."""
    if not path:
        return data
    current = data
    for part in path.split("."):
        if current is None:
            return None
        if isinstance(current, list):
            if not part.isdigit():
                return None
            index = int(part)
            current = current[index] if index < len(current) else None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def looks_like_image_url(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.startswith(("http", "//", "/"))
        and bool(_IMAGE_HINT.search(value))
        and not _BAD_IMAGE.search(value)
    )


def find_image(node: Any, depth: int = 0) -> str:
    """딕셔너리 안 어딘가에 있는 이미지 URL 을 찾아낸다."""
    if depth > 4:
        return ""
    if isinstance(node, str):
        return node if looks_like_image_url(node) else ""
    if isinstance(node, list):
        for item in node[:8]:
            found = find_image(item, depth + 1)
            if found:
                return found
        return ""
    if isinstance(node, dict):
        # 이름이 그럴듯한 키부터 본다.
        for key, value in node.items():
            if any(hint in key.lower() for hint in _IMAGE_KEYS):
                found = find_image(value, depth + 1)
                if found:
                    return found
        for value in node.values():
            found = find_image(value, depth + 1)
            if found:
                return found
    return ""


def autodetect_items(data: Any, depth: int = 0) -> list[dict]:
    """이미지가 들어 있는 딕셔너리 배열 중 가장 큰 것을 찾는다.

    설정한 json_path 가 사이트 개편으로 어긋났을 때의 안전망이다.
    """
    best: list[dict] = []
    if depth > 6:
        return best

    if isinstance(data, list):
        dicts = [item for item in data if isinstance(item, dict)]
        if len(dicts) >= 3 and sum(1 for item in dicts if find_image(item)) >= len(dicts) // 2:
            best = dicts
        for item in data[:20]:
            candidate = autodetect_items(item, depth + 1)
            if len(candidate) > len(best):
                best = candidate
    elif isinstance(data, dict):
        for value in data.values():
            candidate = autodetect_items(value, depth + 1)
            if len(candidate) > len(best):
                best = candidate
    return best


def pick_srcset(value: str) -> str:
    """srcset 에서 목표 폭을 넘지 않는 가장 큰 후보."""
    candidates: list[tuple[int, str]] = []
    for part in value.split(","):
        chunk = part.strip().split()
        if not chunk:
            continue
        url = chunk[0]
        width = 0
        if len(chunk) > 1 and chunk[1].endswith("w"):
            width = parse_count(chunk[1][:-1])
        candidates.append((width, url))
    if not candidates:
        return ""
    within = [pair for pair in candidates if pair[0] <= TARGET_WIDTH]
    return max(within)[1] if within else min(candidates)[1]


# --------------------------------------------------------------- HTML 파서


class MetaParser(HTMLParser):
    """og:/twitter: 메타태그와 <title> 수집."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self._in_title = False
        self.title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True
            return
        if tag != "meta":
            return
        data = {key.lower(): (value or "") for key, value in attrs}
        name = (data.get("property") or data.get("name") or "").lower()
        content = data.get("content", "")
        if name and content and name not in self.meta:
            self.meta[name] = content

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title and not self.title:
            self.title = data.strip()

    @property
    def image(self) -> str:
        for key in ("og:image", "og:image:secure_url", "twitter:image", "twitter:image:src"):
            if self.meta.get(key):
                return self.meta[key]
        return ""

    @property
    def headline(self) -> str:
        return self.meta.get("og:title") or self.title


class CardParser(HTMLParser):
    """카드 그리드에서 (링크, 이미지, 제목) 묶음을 뽑는다.

    `<a><img></a>` 구조와 `<a>...</a><img>` 구조를 모두 받아내려고,
    이미지는 '아직 이미지가 없는 가장 최근 링크'에 붙인다.
    """

    def __init__(self, link_pattern: str) -> None:
        super().__init__(convert_charrefs=True)
        self.link_pattern = link_pattern
        self.items: list[dict[str, str]] = []
        self._seen_links: set[str] = set()
        self._text_target: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key.lower(): (value or "") for key, value in attrs}

        if tag == "a":
            href = data.get("href", "")
            if not href or (self.link_pattern and self.link_pattern not in href):
                return
            if href in self._seen_links:
                self._text_target = None
                return
            self._seen_links.add(href)
            item = {
                "url": href,
                "image": "",
                # 제목 후보는 셋을 따로 모아 두고 나중에 우선순위로 고른다.
                "label": data.get("aria-label") or data.get("title") or "",
                "alt": "",
                "text": "",
            }
            self.items.append(item)
            self._text_target = item
            return

        if tag == "img":
            src = data.get("src") or data.get("data-src") or data.get("data-lazy-src") or ""
            srcset = data.get("srcset") or data.get("data-srcset") or ""
            if srcset:
                src = pick_srcset(srcset) or src
            if not src or _BAD_IMAGE.search(src):
                return
            for item in reversed(self.items):
                if not item["image"]:
                    item["image"] = src
                    item["alt"] = data.get("alt", "")
                    break

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self._text_target = None

    def handle_data(self, data: str) -> None:
        if self._text_target is not None and len(self._text_target["text"]) < 120:
            self._text_target["text"] += data.strip() + " "


def extract_meta(html: str) -> MetaParser:
    parser = MetaParser()
    parser.feed(html)
    return parser


def extract_embedded_json(html: str, marker: str = "") -> list[Any]:
    """`<script>` 안에 박힌 JSON 덩어리들을 꺼낸다.

    `__NEXT_DATA__` 같은 id/변수명이 있으면 그것만, 없으면 파싱되는 것 전부.
    """
    blobs: list[Any] = []
    for match in re.finditer(r"(?is)<script[^>]*>(.*?)</script>", html):
        raw = match.group(1).strip()
        header = match.group(0)[: match.group(0).find(">") + 1]
        if marker and marker not in header and marker not in raw[:200]:
            continue
        if not raw:
            continue

        # `window.__X__ = {...};` 형태면 우변만 떼어낸다.
        assignment = re.match(r"(?s)^[^={]*=\s*(\{.*\}|\[.*\])\s*;?\s*$", raw)
        candidate = assignment.group(1) if assignment else raw
        if not candidate.startswith(("{", "[")):
            continue
        try:
            blobs.append(json.loads(candidate))
        except (json.JSONDecodeError, ValueError):
            continue
    return blobs


# --------------------------------------------------------------- 매핑


def _first_by_key(raw: dict, keys: set[str], *, want_str: bool = True) -> Any:
    """이름이 맞는 키의 첫 값. 사이트마다 필드명이 달라 필요한 최소한의 추측."""
    for key, value in raw.items():
        if key.lower().replace("_", "") not in keys:
            continue
        if want_str:
            if isinstance(value, str) and value.strip():
                return value
        elif isinstance(value, (str, int, float)) and not isinstance(value, bool):
            return value
    return "" if want_str else 0


def _looks_like_page_link(value: str, base_host: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if looks_like_image_url(value):
        return False
    if value.startswith("/") and not value.startswith("//"):
        return True
    if value.startswith("http") and base_host and base_host in value:
        return True
    return False


def _resolve_link(raw: dict, source: ScrapeSource) -> str:
    """항목이 가리키는 '페이지' 주소를 찾는다.

    이걸 못 찾으면 리포트에서 제목을 눌렀을 때 이미지 파일만 열린다.
    작품 페이지로 가야 하므로 여러 방법을 순서대로 시도한다.
    """
    fields = source.fields

    explicit = dig(raw, fields["link"]) if fields.get("link") else None
    if isinstance(explicit, str) and explicit:
        return explicit

    # 항목에 id/slug 만 있고 주소가 없는 사이트를 위해 주소를 조립한다.
    if source.link_template:
        try:
            link = source.link_template.format(**raw)
            if "{" not in link:
                return link
        except (KeyError, IndexError, ValueError):
            pass

    by_name = _first_by_key(raw, _LINK_KEYS)
    if by_name:
        return by_name

    # 키 이름이 낯설어도 값 모양으로 찾아본다.
    base_host = urlsplit(source.base_url or source.url).netloc
    for value in raw.values():
        if _looks_like_page_link(value, base_host):
            return value
    return ""


def map_item(raw: dict, source: ScrapeSource) -> ImageItem | None:
    """설정된 필드 매핑(없으면 자동 탐색)으로 ImageItem 을 만든다."""
    fields = source.fields
    base = source.base_url or source.url

    image = dig(raw, fields["image"]) if fields.get("image") else None
    if not isinstance(image, str) or not image:
        image = find_image(raw)
    if not image:
        return None

    title = dig(raw, fields["title"]) if fields.get("title") else None
    if not isinstance(title, str) or not title:
        title = _first_by_key(raw, _TITLE_KEYS)

    link = _resolve_link(raw, source)

    popularity = parse_count(dig(raw, fields["score"])) if fields.get("score") else 0
    if not popularity:
        popularity = parse_count(_first_by_key(raw, _SCORE_KEYS, want_str=False))
    comments = parse_count(dig(raw, fields["comments"])) if fields.get("comments") else 0
    published = parse_datetime(dig(raw, fields["published"])) if fields.get("published") else None
    author = dig(raw, fields["author"]) if fields.get("author") else ""

    return ImageItem(
        title=strip_html(str(title))[:200] or source.name,
        # 링크를 못 찾으면 이미지 주소를 쓴다. 페이지 주소로 뭉뚱그리면 항목들이
        # 전부 같은 URL 이 되어 중복 제거에 통째로 잡아먹힌다.
        url=urljoin(base, link) if link else (urljoin(base, image) or source.url),
        image_url=urljoin(base, image),
        source=source.name,
        published=published,
        author=str(author)[:80] if isinstance(author, str) else "",
        popularity=popularity,
        comments=comments,
        popularity_note=(f"좋아요 {popularity:,}" if popularity else source.name),
    )


def parse_json_payload(data: Any, source: ScrapeSource) -> list[ImageItem]:
    """JSON 구조에서 이미지 항목을 뽑는다. 경로가 틀리면 자동 탐색으로."""
    items = dig(data, source.json_path) if source.json_path else None
    if not isinstance(items, list) or not items:
        items = autodetect_items(data)

    results: list[ImageItem] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        item = map_item(raw, source)
        if item and item.popularity >= source.min_popularity:
            results.append(item)
    return results


def parse_html_cards(html: str, source: ScrapeSource) -> list[ImageItem]:
    parser = CardParser(source.link_pattern)
    parser.feed(html)
    base = source.base_url or source.url

    results: list[ImageItem] = []
    for card in parser.items:
        if not card["image"]:
            continue
        # aria-label 이 가장 정확하고, 없으면 링크 텍스트, 마지막이 alt.
        title = card["label"] or card["text"].strip() or card["alt"]
        results.append(
            ImageItem(
                title=strip_html(title)[:200] or source.name,
                url=urljoin(base, card["url"]),
                image_url=urljoin(base, card["image"]),
                source=source.name,
                popularity_note=source.name,
            )
        )
    return results


def parse_og_page(html: str, source: ScrapeSource) -> list[ImageItem]:
    meta = extract_meta(html)
    if not meta.image or _PLACEHOLDER_IMAGE.search(meta.image):
        return []
    return [
        ImageItem(
            title=strip_html(meta.headline)[:200] or source.name,
            url=source.url,
            image_url=urljoin(source.base_url or source.url, meta.image),
            source=source.name,
            popularity_note=source.name,
        )
    ]


def parse_scrape(text: str, source: ScrapeSource) -> list[ImageItem]:
    """받아온 본문을 전략에 따라 이미지 목록으로. (네트워크와 분리해 테스트 가능)"""
    strategy = source.strategy.lower()

    if strategy == "json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # JSON 인 줄 알았는데 HTML 이 왔다면 embedded 로 한 번 더 시도한다.
            blobs = extract_embedded_json(text, source.marker)
            data = blobs[0] if blobs else None
        items = parse_json_payload(data, source) if data is not None else []
    elif strategy == "embedded_json":
        items = []
        for blob in extract_embedded_json(text, source.marker):
            items = parse_json_payload(blob, source)
            if items:
                break
    elif strategy == "html":
        items = parse_html_cards(text, source)
    else:
        items = parse_og_page(text, source)

    # 목록을 못 읽었을 때 페이지 대표 이미지로 때우는 건 기본적으로 하지 않는다.
    # 갤러리 페이지의 og:image 는 대개 사이트 간판이라, 매일 같은 그림이 실린다.
    # 상세 페이지처럼 대표 이미지가 곧 콘텐츠인 경우에만 켜서 쓴다.
    if not items and source.og_fallback and strategy != "og" and "<" in text[:200]:
        items = parse_og_page(text, source)

    # 같은 이미지가 여러 번 나오는 경우 제거
    seen: set[str] = set()
    unique: list[ImageItem] = []
    for item in items:
        if item.image_url in seen:
            continue
        seen.add(item.image_url)
        unique.append(item)
    return unique[: source.limit]


def collect_scrape(source: ScrapeSource, config: Config) -> list[ImageItem]:
    """설정된 사이트 하나에서 이미지를 긁어온다."""
    headers = {"Referer": source.base_url or source.url}
    if source.cookie_env:
        cookie = os.environ.get(source.cookie_env, "")
        if cookie:
            headers["Cookie"] = cookie
        else:
            log.debug("%s: 쿠키 환경변수 %s 가 비어 있음", source.name, source.cookie_env)

    text = fetch_text(
        source.url,
        timeout=config.http_timeout,
        retries=config.http_retries,
        user_agent=config.user_agent,
        accept=HTML_ACCEPT,
        headers=headers,
        max_bytes=12 * 1024 * 1024,
    )
    items = parse_scrape(text, source)
    log.debug("%s: 이미지 %d장", source.name, len(items))
    return items
