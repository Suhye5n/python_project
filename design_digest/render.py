"""리포트 렌더링 (HTML + 텍스트).

메일 클라이언트는 CSS 지원이 제각각이라 `<table>` 레이아웃과 인라인 스타일로
쓴다. flex/grid 는 쓰지 않는다.

이미지 경로는 세 가지 모드가 있다.
  cid    : 메일 인라인 첨부 (`cid:` 참조) — 원격 이미지 차단을 피할 수 있다
  file   : 저장된 HTML 파일에서 로컬 이미지를 상대경로로 참조
  remote : 원본 이미지 URL 그대로
"""

from __future__ import annotations

import datetime as dt
import html
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from .models import CATEGORY_LABELS, Digest, ImageItem
from .util import host_of, humanize_age

BODY_BG = "#f4f4f5"
CARD_BG = "#ffffff"
TEXT = "#18181b"
MUTED = "#71717a"
BORDER = "#e4e4e7"
ACCENT = "#4f46e5"

CATEGORY_EMOJI = {
    "trend": "📈",
    "methodology": "🧭",
    "philosophy": "🌱",
    "general": "🔖",
}


def image_cid(index: int) -> str:
    return f"digest-image-{index}"


def inline_attachments(digest: Digest) -> list[tuple[str, Path]]:
    """(Content-ID, 파일경로) 목록. 실제로 내려받힌 이미지만."""
    pairs = []
    for index, item in enumerate(digest.images):
        if item.local_path and Path(item.local_path).exists():
            pairs.append((image_cid(index), Path(item.local_path)))
    return pairs


def _image_src(item: ImageItem, index: int, mode: str, base_dir: Path | None) -> str:
    if mode == "cid" and item.local_path and Path(item.local_path).exists():
        return f"cid:{image_cid(index)}"
    if mode == "file" and item.local_path and Path(item.local_path).exists():
        if base_dir:
            try:
                return os.path.relpath(item.local_path, base_dir).replace(os.sep, "/")
            except ValueError:  # 드라이브가 다르면 절대경로로
                pass
        return Path(item.local_path).as_uri()
    return item.image_url


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def _local_time(value: dt.datetime, timezone: str) -> dt.datetime:
    return value.astimezone(ZoneInfo(timezone))


def subject_line(digest: Digest, prefix: str = "[디자인 다이제스트]") -> str:
    counts = f"글 {len(digest.articles)}편 · 이미지 {len(digest.images)}장"
    top = digest.articles[0].title if digest.articles else ""
    date_text = digest.date.strftime("%m월 %d일")
    if top:
        return f"{prefix} {date_text} — {counts} · {top[:40]}"
    return f"{prefix} {date_text} — {counts}"


# ----------------------------------------------------------------- HTML


def _header_html(digest: Digest, timezone: str) -> str:
    generated = _local_time(digest.generated_at, timezone).strftime("%Y년 %m월 %d일 %H:%M")
    stats = digest.stats
    line = (
        f"수집 {stats.get('collected_articles', 0)}건 중 글 {len(digest.articles)}편, "
        f"이미지 {len(digest.images)}장을 골랐어요."
    )
    if stats.get("filtered_out"):
        line += f" (시각디자인 밖 {stats['filtered_out']}건 제외)"
    return f"""
      <tr>
        <td style="padding:28px 28px 8px 28px;">
          <div style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:{MUTED};">
            Daily Design Digest
          </div>
          <h1 style="margin:6px 0 4px 0;font-size:24px;line-height:1.3;color:{TEXT};">
            {digest.date.strftime('%Y년 %m월 %d일')} 디자인 브리핑
          </h1>
          <div style="font-size:13px;color:{MUTED};">{_esc(line)} · {generated} 기준</div>
        </td>
      </tr>
    """


def _images_html(digest: Digest, mode: str, base_dir: Path | None) -> str:
    if not digest.images:
        return ""

    cells = []
    for index, item in enumerate(digest.images):
        src = _image_src(item, index, mode, base_dir)
        if not src:
            continue
        meta = " · ".join(filter(None, [_esc(item.source), _esc(item.popularity_note)]))
        cells.append(
            f"""
            <td width="50%" valign="top" style="padding:6px;">
              <a href="{_esc(item.url)}" style="text-decoration:none;color:{TEXT};">
                <img src="{_esc(src)}" alt="{_esc(item.title)}" width="272"
                     style="width:100%;max-width:272px;height:auto;border-radius:10px;
                            border:1px solid {BORDER};display:block;" />
                <div style="font-size:13px;line-height:1.4;margin:8px 0 2px 0;font-weight:600;">
                  {_esc(item.title[:90])}
                </div>
                <div style="font-size:11px;color:{MUTED};">{meta}</div>
              </a>
            </td>
            """
        )

    rows = []
    for i in range(0, len(cells), 2):
        pair = cells[i : i + 2]
        if len(pair) == 1:
            pair.append('<td width="50%"></td>')
        rows.append(f"<tr>{''.join(pair)}</tr>")

    return f"""
      <tr>
        <td style="padding:18px 22px 4px 22px;">
          <h2 style="margin:0 0 4px 0;font-size:16px;color:{TEXT};">
            🖼️ 오늘 사람들이 많이 본 디자인
          </h2>
          <div style="font-size:12px;color:{MUTED};margin-bottom:6px;">
            업보트·댓글·언급량 기준 상위 {len(digest.images)}장
          </div>
          <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
            {''.join(rows)}
          </table>
        </td>
      </tr>
    """


def _article_html(article, timezone: str) -> str:
    age = humanize_age(article.published)
    meta_parts = [_esc(article.source or host_of(article.url))]
    if age:
        meta_parts.append(age)
    if article.popularity_note:
        meta_parts.append(_esc(article.popularity_note))
    meta = " · ".join(meta_parts)

    tags = "".join(
        f"""<span style="display:inline-block;font-size:11px;color:{ACCENT};
             background:#eef2ff;border-radius:999px;padding:2px 8px;margin:4px 4px 0 0;">
             {_esc(keyword)}</span>"""
        for keyword in article.keywords[:3]
    )
    summary = (
        f"""<div style="font-size:13px;line-height:1.6;color:#3f3f46;margin-top:6px;">
             {_esc(article.summary)}</div>"""
        if article.summary
        else ""
    )
    return f"""
      <div style="padding:14px 0;border-bottom:1px solid {BORDER};">
        <a href="{_esc(article.url)}"
           style="font-size:15px;font-weight:600;line-height:1.45;color:{TEXT};text-decoration:none;">
          {_esc(article.title)}
        </a>
        <div style="font-size:11px;color:{MUTED};margin-top:4px;">{meta}</div>
        {summary}
        <div>{tags}</div>
      </div>
    """


def _articles_html(digest: Digest, timezone: str) -> str:
    grouped = digest.by_category()
    if not grouped:
        return ""

    blocks = []
    for category, articles in grouped.items():
        emoji = CATEGORY_EMOJI.get(category, "🔖")
        label = CATEGORY_LABELS.get(category, category)
        items = "".join(_article_html(article, timezone) for article in articles)
        blocks.append(
            f"""
            <tr>
              <td style="padding:18px 28px 0 28px;">
                <h2 style="margin:0;font-size:16px;color:{TEXT};">{emoji} {_esc(label)}
                  <span style="font-size:12px;font-weight:400;color:{MUTED};">
                    {len(articles)}편</span>
                </h2>
                {items}
              </td>
            </tr>
            """
        )
    return "".join(blocks)


def _footer_html(digest: Digest) -> str:
    failure_note = ""
    if digest.failures:
        names = ", ".join(_esc(name) for name, _ in digest.failures[:6])
        more = f" 외 {len(digest.failures) - 6}곳" if len(digest.failures) > 6 else ""
        failure_note = (
            f"""<div style="font-size:11px;color:{MUTED};margin-top:6px;">
                 오늘 못 읽은 소스: {names}{more}</div>"""
        )
    return f"""
      <tr>
        <td style="padding:20px 28px 28px 28px;">
          <div style="border-top:1px solid {BORDER};padding-top:12px;font-size:11px;color:{MUTED};">
            design_digest가 자동으로 모아 보냈습니다 ·
            소스 {digest.stats.get('sources_total', 0)}곳 ·
            {digest.stats.get('elapsed_sec', 0)}초 소요
            {failure_note}
          </div>
        </td>
      </tr>
    """


def render_html(
    digest: Digest,
    *,
    timezone: str = "Asia/Seoul",
    mode: str = "remote",
    base_dir: Path | None = None,
) -> str:
    """다이제스트를 메일/브라우저용 HTML 한 덩어리로."""
    if digest.is_empty:
        body = f"""
          <tr><td style="padding:24px 28px;font-size:14px;color:{MUTED};">
            오늘은 새로 올라온 글이나 이미지를 찾지 못했어요.
            (소스 실패 {len(digest.failures)}건)
          </td></tr>
        """
    else:
        body = (
            _images_html(digest, mode, base_dir)
            + _articles_html(digest, timezone)
        )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="color-scheme" content="light" />
  <title>{_esc(digest.date.isoformat())} 디자인 다이제스트</title>
</head>
<body style="margin:0;padding:0;background:{BODY_BG};
             font-family:-apple-system,'Apple SD Gothic Neo','Malgun Gothic',
             'Noto Sans KR',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
         style="background:{BODY_BG};padding:16px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" role="presentation"
               style="width:100%;max-width:600px;background:{CARD_BG};border-radius:14px;
                      border:1px solid {BORDER};overflow:hidden;">
          {_header_html(digest, timezone)}
          {body}
          {_footer_html(digest)}
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


# ----------------------------------------------------------------- 텍스트


def render_text(digest: Digest, timezone: str = "Asia/Seoul") -> str:
    """HTML 을 못 보는 클라이언트를 위한 대체 본문."""
    lines = [
        f"{digest.date.isoformat()} 디자인 다이제스트",
        f"글 {len(digest.articles)}편 · 이미지 {len(digest.images)}장",
        "",
    ]

    for category, articles in digest.by_category().items():
        lines.append(f"[{CATEGORY_LABELS.get(category, category)}]")
        for article in articles:
            age = humanize_age(article.published)
            meta = " · ".join(filter(None, [article.source, age, article.popularity_note]))
            lines.append(f"- {article.title}")
            lines.append(f"  {meta}")
            if article.summary:
                lines.append(f"  {article.summary}")
            lines.append(f"  {article.url}")
        lines.append("")

    if digest.images:
        lines.append("[오늘 사람들이 많이 본 디자인]")
        for item in digest.images:
            meta = " · ".join(filter(None, [item.source, item.popularity_note]))
            lines.append(f"- {item.title} ({meta})")
            lines.append(f"  {item.url}")
        lines.append("")

    if digest.failures:
        lines.append("못 읽은 소스: " + ", ".join(name for name, _ in digest.failures))
    return "\n".join(lines)


def save_report(
    digest: Digest, reports_dir: Path, *, timezone: str = "Asia/Seoul"
) -> Path:
    """리포트를 HTML 파일로 저장하고 경로를 돌려준다."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"{digest.date.isoformat()}.html"
    path.write_text(
        render_html(digest, timezone=timezone, mode="file", base_dir=reports_dir),
        encoding="utf-8",
    )
    return path
