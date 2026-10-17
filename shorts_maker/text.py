"""자막·썸네일 문구·[광고] 표시를 투명 PNG 로 그린다."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .config import AdTagConfig, Config, SubtitleConfig, ThumbnailConfig

REFERENCE_GLYPH = "가나다"


class TextError(ValueError):
    pass


@lru_cache(maxsize=16)
def font_for_height(path: str, glyph_height: int) -> ImageFont.FreeTypeFont:
    """한글 글자 높이가 glyph_height(px)가 되는 크기로 폰트를 연다.

    폰트마다 같은 pt 라도 실제 글자 크기가 달라서, pt 대신 글자 높이로 맞춘다.
    """
    if not Path(path).exists():
        raise TextError(f"폰트 파일이 없습니다: {path}")
    lo, hi = 4, 600
    while lo < hi:
        mid = (lo + hi + 1) // 2
        f = ImageFont.truetype(path, mid)
        x0, y0, x1, y1 = f.getbbox(REFERENCE_GLYPH)
        if y1 - y0 <= glyph_height:
            lo = mid
        else:
            hi = mid - 1
    return ImageFont.truetype(path, lo)


def _rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    c = color.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), alpha


def _ink_center_offset(font: ImageFont.FreeTypeFont) -> float:
    """글자 기준점에서 한글 글자 세로 중심까지의 거리."""
    _, y0, _, y1 = font.getbbox(REFERENCE_GLYPH)
    return (y0 + y1) / 2


def text_width(text: str, font: ImageFont.FreeTypeFont) -> int:
    return int(round(font.getlength(text)))


# ---------------------------------------------------------------- 자막


def subtitle_font(cfg: Config) -> ImageFont.FreeTypeFont:
    return font_for_height(str(cfg.resolve(cfg.subtitle.font)), cfg.subtitle.glyph_height)


def too_long(texts: list[str], cfg: Config) -> list[tuple[int, str, int]]:
    """화면 폭을 넘는 자막: (순번, 내용, 폭)."""
    font = subtitle_font(cfg)
    out = []
    for i, t in enumerate(texts, 1):
        w = text_width(t, font)
        if w > cfg.subtitle.max_width:
            out.append((i, t, w))
    return out


def render_subtitle(text: str, cfg: Config) -> Image.Image:
    sc: SubtitleConfig = cfg.subtitle
    W, H = cfg.video.width, cfg.video.height
    font = subtitle_font(cfg)
    x = W / 2
    y = sc.center_y - _ink_center_offset(font)

    # 글자 모양 마스크 → 넓히고 번지게 해서 그림자 (캡컷 그림자 거리 0,0 과 같은 효과)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).text(
        (x, y), text, font=font, fill=255, anchor="ma",
        stroke_width=sc.shadow_stroke, stroke_fill=255,
    )
    shadow_alpha = mask.filter(ImageFilter.GaussianBlur(sc.shadow_blur)).point(
        lambda v: min(255, int(v * sc.shadow_strength))
    )
    img = Image.new("RGBA", (W, H), _rgba(sc.shadow_color, 0))
    img.putalpha(shadow_alpha)
    ImageDraw.Draw(img).text((x, y), text, font=font, fill=_rgba(sc.color), anchor="ma")
    return img


# ---------------------------------------------------------------- [광고] 표시


def render_ad_tag(cfg: Config) -> Image.Image | None:
    tc: AdTagConfig = cfg.ad_tag
    if not tc.enabled or not tc.text:
        return None
    W, H = cfg.video.width, cfg.video.height
    font = font_for_height(str(cfg.resolve(tc.font or cfg.subtitle.font)), tc.glyph_height)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(img).text(
        (tc.center_x, tc.center_y - _ink_center_offset(font)), tc.text, font=font,
        fill=_rgba(tc.color), anchor="ma", stroke_width=tc.stroke, stroke_fill=_rgba(tc.stroke_color),
    )
    return img


# ---------------------------------------------------------------- 썸네일 문구


def parse_highlights(line: str) -> list[tuple[str, bool]]:
    """'*세탁소* 하시면' → [('세탁소', True), (' 하시면', False)]"""
    parts = re.split(r"(\*[^*]+\*)", line)
    out = []
    for p in parts:
        if not p:
            continue
        if p.startswith("*") and p.endswith("*") and len(p) > 2:
            out.append((p[1:-1], True))
        else:
            out.append((p, False))
    return out


def load_thumbnail_lines(path: Path) -> list[str]:
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8-sig").splitlines() if ln.strip()]
    if not lines:
        raise TextError(f"{path.name} 이 비어 있습니다.")
    return lines


def render_thumbnail_text(lines: list[str], cfg: Config) -> Image.Image:
    tc: ThumbnailConfig = cfg.thumbnail
    W, H = cfg.video.width, cfg.video.height
    font = font_for_height(str(cfg.resolve(tc.font)), tc.glyph_height)
    offset = _ink_center_offset(font)
    first_center = tc.center_y - tc.line_spacing * (len(lines) - 1) / 2

    layout = []  # (x, y, 조각, 강조여부)
    for li, line in enumerate(lines):
        runs = parse_highlights(line)
        plain = "".join(t for t, _ in runs)
        width = font.getlength(plain)
        if width > tc.max_width:
            raise TextError(f"썸네일 {li + 1}번째 줄이 너무 깁니다: {plain!r} — 줄을 나눠 주세요.")
        x = (W - width) / 2
        y = first_center + li * tc.line_spacing - offset
        prefix = ""
        for text, hl in runs:
            # 앞 글자들과의 자간(커닝)을 살리려고 줄 처음부터의 길이로 위치를 잡는다
            layout.append((x + font.getlength(prefix), y, text, hl))
            prefix += text

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    stroke = _rgba(tc.stroke_color)
    # 테두리를 먼저 모두 그리고 그 위에 글자색을 칠해야 조각 경계에 테두리가 안 겹친다
    for x, y, text, _ in layout:
        draw.text((x, y), text, font=font, fill=stroke, stroke_width=tc.stroke, stroke_fill=stroke)
    for x, y, text, hl in layout:
        draw.text((x, y), text, font=font, fill=_rgba(tc.highlight_color if hl else tc.color))
    return img


def flatten(*layers: Image.Image | None) -> Image.Image:
    base = None
    for layer in layers:
        if layer is None:
            continue
        base = layer.copy() if base is None else Image.alpha_composite(base, layer)
    return base

