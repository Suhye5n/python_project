"""커맨드라인 인터페이스.

    python -m shorts_maker 작업폴더             # 영상 만들기
    python -m shorts_maker 작업폴더 --plan-only # 어떤 컷을 쓸지만 확인
    python -m shorts_maker 작업폴더 --preview   # 자막·썸네일 문구 모양만 PNG 로 확인

작업폴더 구성:
    clips/          원본 클립 (mp4, mov …)
    product/        제품 사진 1~3장
    *.mp3           목소리
    *.srt           자막
    thumbnail.txt   썸네일 문구 (줄바꿈 그대로, *강조* 는 노란색)
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
import time
from pathlib import Path

from . import media
from .analyze import analyze_all
from .config import Config
from .planner import Cut, PlanError, plan_cuts, thumbnail_source
from .render import concat, render_cut, render_thumbnail, save_thumbnail_png
from .srt import SrtError, Subtitle, build_segments, load_srt
from .text import (
    TextError,
    flatten,
    load_thumbnail_lines,
    render_ad_tag,
    render_subtitle,
    render_thumbnail_text,
    too_long,
)

log = logging.getLogger("shorts_maker")

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
AUDIO_EXT = {".mp3", ".m4a", ".wav", ".aac"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class InputError(RuntimeError):
    pass


def _files(folder: Path, exts: set[str]) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in exts and not p.name.startswith("."))


def _one(folder: Path, exts: set[str], what: str) -> Path:
    found = _files(folder, exts)
    if len(found) != 1:
        names = ", ".join(p.name for p in found) or "없음"
        raise InputError(f"{what} 파일이 작업폴더에 딱 1개 있어야 합니다 (지금: {names}).")
    return found[0]


def find_inputs(day: Path) -> dict:
    clips = _files(day / "clips", VIDEO_EXT) or _files(day, VIDEO_EXT)
    if not clips:
        raise InputError(f"{day}/clips/ 에 영상 클립이 없습니다.")
    thumb = day / "thumbnail.txt"
    if not thumb.exists():
        raise InputError("thumbnail.txt (썸네일 문구) 가 없습니다.")
    return {
        "clips": clips,
        "voice": _one(day, AUDIO_EXT, "목소리(mp3)"),
        "srt": _one(day, {".srt"}, "자막(srt)"),
        "product": _files(day / "product", IMAGE_EXT),
        "thumbnail": thumb,
    }


def _fmt(frames: int, fps: int) -> str:
    return f"{frames / fps:6.2f}s"


def write_plan(cuts: list[Cut], subs: list[Subtitle], analyses, cfg: Config, path: Path) -> str:
    fps = cfg.video.fps
    lines = [f"{'#':>3}  {'시작':>7} {'길이':>7}  {'배속':>5}  {'점수':>6}  {'원본':<28} {'원본 구간':<17}  자막"]
    for i, c in enumerate(cuts, 1):
        a = analyses[c.clip]
        lines.append(
            f"{i:>3}  {_fmt(c.segment.start, fps)} {_fmt(c.segment.frames, fps)}  "
            f"{c.speed:4.2f}x  {c.score:6.2f}  {a.name[:28]:<28} "
            f"{c.src_start / fps:6.2f}~{c.src_end / fps:6.2f}s  "
            f"{subs[c.segment.subtitle_index].text}"
            + (f"  (가림 {len(c.blur_boxes)}곳)" if c.blur_boxes else "")
        )
    usage: dict[str, float] = {}
    for c in cuts:
        usage[analyses[c.clip].name] = usage.get(analyses[c.clip].name, 0) + c.segment.frames / fps
    lines.append("")
    lines.append("영상별 사용 시간: " + ", ".join(f"{k} {v:.2f}s" for k, v in sorted(usage.items())))
    text = "\n".join(lines)
    path.write_text(text + "\n", encoding="utf-8")
    return text


def make(day: Path, cfg: Config, plan_only: bool, preview: bool, keep_work: bool) -> Path | None:
    media.require_ffmpeg()
    inputs = find_inputs(day)
    fps = cfg.video.fps
    result_dir = day / "result"
    work = day / ".work"
    result_dir.mkdir(exist_ok=True)
    work.mkdir(exist_ok=True)

    subs = load_srt(inputs["srt"])
    long_subs = too_long([s.text for s in subs], cfg)
    if long_subs:
        detail = "\n".join(f"  {i}번 ({w}px): {t}" for i, t, w in long_subs)
        raise TextError(
            f"한 줄에 다 들어가지 않는 자막이 있습니다 (최대 {cfg.subtitle.max_width}px). "
            f"srt 를 짧게 고쳐서 다시 넣어주세요.\n{detail}"
        )
    thumb_lines = load_thumbnail_lines(inputs["thumbnail"])
    thumb_text = render_thumbnail_text(thumb_lines, cfg)
    ad_tag = render_ad_tag(cfg)
    thumb_overlay = flatten(thumb_text, ad_tag)

    if preview:
        thumb_overlay.save(result_dir / "preview_thumbnail_text.png")
        for s in subs:
            flatten(render_subtitle(s.text, cfg), ad_tag).save(result_dir / f"preview_sub_{s.index:02d}.png")
        log.info("미리보기 PNG 를 %s 에 저장했습니다.", result_dir)
        return None

    voice_len = media.duration(inputs["voice"])
    total_frames = round(voice_len * fps)
    max_seg = round(cfg.cut.per_source_limit * fps)
    segments = build_segments(subs, total_frames, fps, max_seg)
    log.info(
        "목소리 %.2f초, 자막 %d개 → 컷 %d개, 클립 %d개, 제품 사진 %d장",
        voice_len, len(subs), len(segments), len(inputs["clips"]), len(inputs["product"]),
    )

    analyses = analyze_all(inputs["clips"], inputs["product"], cfg, day / ".cache")
    cuts = plan_cuts(segments, analyses, cfg)
    plan_text = write_plan(cuts, subs, analyses, cfg, result_dir / "plan.txt")
    print(plan_text)
    if plan_only:
        return None

    sub_pngs = []
    for s in subs:
        p = work / f"sub_{s.index:03d}.png"
        render_subtitle(s.text, cfg).save(p)
        sub_pngs.append(p)
    tag_png = None
    if ad_tag is not None:
        tag_png = work / "ad_tag.png"
        ad_tag.save(tag_png)
    thumb_png = work / "thumb_overlay.png"
    thumb_overlay.save(thumb_png)

    parts = []
    thumb_part = work / "part_000.mp4"
    if cfg.thumbnail.background == "auto":
        src = thumbnail_source(cuts)
        render_thumbnail(src, Path(analyses[src.clip].path), None, thumb_png, thumb_part, cfg)
    else:
        bg = cfg.resolve(cfg.thumbnail.background)
        if not bg.is_absolute() or not bg.exists():
            bg = day / cfg.thumbnail.background
        render_thumbnail(None, None, bg, thumb_png, thumb_part, cfg)
    parts.append(thumb_part)

    for i, cut in enumerate(cuts, 1):
        log.info("컷 %d/%d 만드는 중…", i, len(cuts))
        out = work / f"part_{i:03d}.mp4"
        render_cut(cut, Path(analyses[cut.clip].path), subs, sub_pngs, tag_png, out, cfg)
        parts.append(out)

    final = result_dir / f"{day.resolve().name}.mp4"
    concat(parts, inputs["voice"], total_frames, final, cfg)
    save_thumbnail_png(thumb_part, result_dir / "thumbnail.png")
    if not keep_work:
        shutil.rmtree(work, ignore_errors=True)
    return final


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shorts_maker", description="매일 쇼츠 자동 편집")
    parser.add_argument("day", type=Path, help="오늘 재료를 넣은 작업폴더")
    parser.add_argument("--config", type=Path, default=None, help="설정 파일 (기본: shorts_maker.toml)")
    parser.add_argument("--plan-only", action="store_true", help="컷 계획만 만들고 영상은 만들지 않음")
    parser.add_argument("--preview", action="store_true", help="자막·썸네일 문구 모양만 PNG 로 저장")
    parser.add_argument("--keep-work", action="store_true", help="중간 파일(.work) 지우지 않기")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
    )
    started = time.time()
    try:
        cfg = Config.load(args.config)
        final = make(args.day, cfg, args.plan_only, args.preview, args.keep_work)
    except (InputError, SrtError, TextError, PlanError, media.MediaError, ValueError) as exc:
        log.error("%s", exc)
        return 1
    if final:
        log.info("완성: %s (%.0f초 걸림)", final, time.time() - started)
    return 0
