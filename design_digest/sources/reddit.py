"""Reddit 인기 게시물에서 이미지 수집.

'사람들에게 인기가 많았던 디자인'을 판단할 근거가 필요한데, 서브레딧의
하루 상위 게시물은 업보트/댓글 수라는 숫자가 붙어 있어 그 근거로 쓰기 좋다.
로그인 없이 쓸 수 있는 공개 JSON 엔드포인트만 사용한다.
"""

from __future__ import annotations

import base64
import datetime as dt
import logging
import os
import time
from typing import Any
from urllib.parse import urlencode

from ..config import Config
from ..models import ImageItem
from ..net import FetchError, fetch_json
from . import RedditSource

log = logging.getLogger(__name__)

API_TEMPLATE = "https://www.reddit.com/r/{subreddit}/top.json?t=day&limit={limit}&raw_json=1"
#: 인증을 쓰면 이쪽. 공개 엔드포인트와 응답 모양은 같다.
OAUTH_TEMPLATE = "https://oauth.reddit.com/r/{subreddit}/top?t=day&limit={limit}&raw_json=1"
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"

#: 실행 중 토큰 재사용 (만료시각, 토큰)
_token_cache: tuple[float, str] | None = None
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp")
#: 메일에 넣을 이미지의 목표 가로 폭. 원본은 수 MB짜리도 있어서 그대로 쓰면
#: 메일이 너무 무거워진다. reddit 이 만들어 둔 리사이즈본을 우선 쓴다.
TARGET_WIDTH = 1080


def _best_resolution(candidates: list[dict[str, Any]], key: str = "url") -> str:
    """목표 폭을 넘지 않는 가장 큰 리사이즈본. 없으면 가장 작은 것."""
    sized = [
        (int(item.get("x") or item.get("width") or 0), item.get(key) or item.get("u") or "")
        for item in candidates
    ]
    sized = [(width, url) for width, url in sized if url.startswith("http")]
    if not sized:
        return ""
    within = [pair for pair in sized if pair[0] <= TARGET_WIDTH]
    return max(within)[1] if within else min(sized)[1]


def _image_url(post: dict[str, Any]) -> str:
    """게시물에서 가장 쓸 만한 이미지 주소를 뽑는다."""
    previews = (post.get("preview") or {}).get("images") or []
    if previews:
        resized = _best_resolution(previews[0].get("resolutions") or [])
        if resized:
            return resized

    url = (post.get("url_overridden_by_dest") or post.get("url") or "").strip()
    if url.lower().endswith(IMAGE_EXTENSIONS) or (
        post.get("post_hint") == "image" and url.startswith("http")
    ):
        return url

    # 갤러리 게시물: 첫 장을 대표 이미지로.
    metadata = post.get("media_metadata")
    if isinstance(metadata, dict):
        for item in metadata.values():
            item = item or {}
            resized = _best_resolution(item.get("p") or [], key="u")
            if resized:
                return resized
            source = item.get("s", {})
            candidate = source.get("u") or source.get("gif")
            if candidate:
                return candidate

    # 리사이즈본이 없으면 원본 미리보기라도.
    if previews:
        candidate = (previews[0].get("source") or {}).get("url", "")
        if candidate.startswith("http"):
            return candidate
    return ""


def parse_listing(payload: dict[str, Any], source: RedditSource) -> list[ImageItem]:
    """Reddit listing JSON 을 ImageItem 목록으로."""
    children = (payload.get("data") or {}).get("children") or []
    items: list[ImageItem] = []

    for child in children:
        post = child.get("data") or {}
        if post.get("stickied") or post.get("over_18") or post.get("is_self"):
            continue
        score = int(post.get("score") or 0)
        if score < source.min_score:
            continue
        image_url = _image_url(post)
        if not image_url:
            continue

        created = post.get("created_utc")
        published = (
            dt.datetime.fromtimestamp(float(created), tz=dt.timezone.utc) if created else None
        )
        permalink = post.get("permalink") or ""
        items.append(
            ImageItem(
                title=(post.get("title") or "").strip(),
                url=f"https://www.reddit.com{permalink}" if permalink else image_url,
                image_url=image_url,
                source=source.label,
                published=published,
                author=f"u/{post['author']}" if post.get("author") else "",
                popularity=score,
                comments=int(post.get("num_comments") or 0),
                popularity_note=f"업보트 {score:,} · 댓글 {int(post.get('num_comments') or 0):,}",
            )
        )
    return items


def access_token(config: Config) -> str:
    """OAuth 토큰을 받아온다. 자격증명이 없으면 빈 문자열.

    Reddit 은 공개 `.json` 엔드포인트로 오는 데이터센터 IP 요청을 막는다.
    GitHub Actions 러너가 딱 그 경우라 전부 `403 Blocked` 가 난다.
    앱을 등록해 client_credentials 토큰을 쓰면 정식 API 로 접근할 수 있다.
    """
    global _token_cache

    client_id = os.environ.get("REDDIT_CLIENT_ID", "").strip()
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "").strip()
    if not (client_id and client_secret):
        return ""

    if _token_cache and _token_cache[0] > time.time():
        return _token_cache[1]

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    payload = fetch_json(
        TOKEN_URL,
        data=urlencode({"grant_type": "client_credentials"}).encode(),
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=config.http_timeout,
        retries=1,
        user_agent=config.user_agent,
    )
    token = str(payload.get("access_token") or "")
    if not token:
        raise FetchError("Reddit 토큰 응답에 access_token 이 없습니다")

    expires_in = float(payload.get("expires_in") or 3600)
    _token_cache = (time.time() + expires_in - 60, token)
    log.debug("Reddit OAuth 토큰 발급 (%.0f초 유효)", expires_in)
    return token


def collect_subreddit(source: RedditSource, config: Config) -> list[ImageItem]:
    try:
        token = access_token(config)
    except FetchError as exc:
        log.warning("Reddit 인증 실패, 공개 엔드포인트로 시도합니다: %s", exc)
        token = ""

    if token:
        url = OAUTH_TEMPLATE.format(subreddit=source.subreddit, limit=source.limit)
        headers = {"Authorization": f"Bearer {token}"}
    else:
        url = API_TEMPLATE.format(subreddit=source.subreddit, limit=source.limit)
        headers = None

    payload = fetch_json(
        url,
        headers=headers,
        timeout=config.http_timeout,
        retries=config.http_retries,
        user_agent=config.user_agent,
    )
    items = parse_listing(payload, source)
    log.debug("%s: 이미지 %d개", source.label, len(items))
    return items
