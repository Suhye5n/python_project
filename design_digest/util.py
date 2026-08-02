"""URL / 텍스트 / 날짜 관련 잡다한 헬퍼."""

from __future__ import annotations

import datetime as dt
import html
import re
import unicodedata
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# 링크에 붙어오는 추적용 쿼리 파라미터 (중복 판정을 방해한다)
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
    "source",
}

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_SENTENCE_RE = re.compile(r"(?<=[.!?。])\s+")


def normalize_url(url: str) -> str:
    """중복 판정을 위해 URL을 정규화한다.

    스킴/호스트 소문자화, `www.` 제거, 추적 파라미터 제거, 끝 슬래시 정리.
    """
    if not url:
        return ""
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return url.strip()

    # http/https 는 같은 글로 본다. 매체마다 피드에 적어두는 스킴이 달라서
    # 그대로 두면 같은 글이 두 번 보고된다.
    scheme = (parts.scheme or "https").lower()
    if scheme == "http":
        scheme = "https"
    netloc = parts.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    query = urlencode(
        [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS]
    )
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((scheme, netloc, path, query, ""))


def host_of(url: str) -> str:
    """표시용 호스트명 (`www.` 없는 도메인)."""
    try:
        netloc = urlsplit(url).netloc.lower()
    except ValueError:
        return ""
    return netloc[4:] if netloc.startswith("www.") else netloc


def strip_html(raw: str) -> str:
    """HTML 조각에서 사람이 읽을 텍스트만 뽑아낸다."""
    if not raw:
        return ""
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    text = re.sub(r"(?i)<br\s*/?>|</p>", "\n", text)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = unicodedata.normalize("NFKC", text)
    return _WS_RE.sub(" ", text).strip()


def summarize(raw: str, *, max_chars: int = 320, max_sentences: int = 3) -> str:
    """본문 요약(발췌). 문장 경계를 지키면서 길이를 맞춘다."""
    text = strip_html(raw)
    if not text:
        return ""
    sentences = _SENTENCE_RE.split(text)
    picked: list[str] = []
    total = 0
    for sentence in sentences[:max_sentences]:
        sentence = sentence.strip()
        if not sentence:
            continue
        if picked and total + len(sentence) > max_chars:
            break
        picked.append(sentence)
        total += len(sentence)
    summary = " ".join(picked) if picked else text
    return shorten(summary, max_chars)


def shorten(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def parse_datetime(value: str | None) -> dt.datetime | None:
    """RSS(RFC822) / Atom(ISO8601) 양쪽 날짜 형식을 모두 받아준다."""
    if not value:
        return None
    value = value.strip()
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
        if parsed is not None:
            return _as_utc(parsed)
    except (TypeError, ValueError, IndexError):
        pass

    candidate = value.replace("Z", "+00:00")
    for text in (candidate, candidate[:19]):
        try:
            return _as_utc(dt.datetime.fromisoformat(text))
        except ValueError:
            continue

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return _as_utc(dt.datetime.strptime(value[: len(fmt) + 4], fmt))
        except ValueError:
            continue
    return None


def _as_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc)


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def humanize_age(published: dt.datetime | None, now: dt.datetime | None = None) -> str:
    """'3시간 전' 같은 상대 시각 표기."""
    if not published:
        return ""
    now = now or utc_now()
    delta = now - published
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "방금"
    if minutes < 60:
        return f"{minutes}분 전"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}시간 전"
    days = hours // 24
    return f"{days}일 전"
