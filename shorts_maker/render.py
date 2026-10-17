"""ffmpeg 로 컷을 만들고 이어 붙여 최종 영상을 만든다."""

from __future__ import annotations

import logging
from pathlib import Path

from . import media
from .config import Config
from .planner import Cut
from .srt import Subtitle

log = logging.getLogger("shorts_maker")


def _encode_args(cfg: Config) -> list[str]:
    v = cfg.video
    # 모든 조각을 같은 설정으로 인코딩해야 다시 인코딩 없이 이어 붙일 수 있다
    return [
        "-an", "-c:v", "libx264", "-preset", v.preset, "-crf", str(v.crf),
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", str(v.fps),
        "-video_track_timescale", str(v.fps * 512),
    ]


def _even(v: int) -> int:
    return v - (v % 2)


def _blur_chain(label: str, boxes: list[list[int]], cfg: Config) -> tuple[list[str], str]:
    """원본 자막 영역을 흐리게 만드는 필터 체인."""
    parts: list[str] = []
    cur = label
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        x, y = _even(x0), _even(y0)
        w, h = _even(x1 - x), _even(y1 - y)
        parts.append(f"[{cur}]split=2[bb{i}][bs{i}]")
        parts.append(f"[bs{i}]crop={w}:{h}:{x}:{y},gblur=sigma={cfg.blur.sigma}:steps=3[bg{i}]")
        parts.append(f"[bb{i}][bg{i}]overlay={x}:{y}[bo{i}]")
        cur = f"bo{i}"
    return parts, cur


def render_cut(
    cut: Cut,
    clip_path: Path,
    subtitles: list[Subtitle],
    subtitle_pngs: list[Path],
    ad_tag_png: Path | None,
    out: Path,
    cfg: Config,
) -> None:
    fps = cfg.video.fps
    W, H = cfg.video.width, cfg.video.height
    seg = cut.segment
    src_len = (cut.src_end - cut.src_start) / fps
    t0, t1 = seg.start / fps, seg.end / fps

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-ss", f"{cut.src_start / fps:.4f}", "-t", f"{src_len:.4f}", "-i", str(clip_path),
    ]
    filters = [f"[0:v]{media.cover_filter(W, H)},format=yuv420p[c0]"]
    blur, cur = _blur_chain("c0", cut.blur_boxes, cfg)
    filters += blur
    filters.append(
        f"[{cur}]setpts=(PTS-STARTPTS)/{cut.speed:.6f},fps={fps},"
        f"tpad=stop_mode=clone:stop_duration=1[s0]"
    )
    cur = "s0"
    inp = 1
    for sub, png in zip(subtitles, subtitle_pngs):
        a, b = max(sub.start, t0), min(sub.end, t1)
        if b <= a:
            continue
        cmd += ["-i", str(png)]
        filters.append(
            f"[{cur}][{inp}:v]overlay=0:0:enable='gte(t,{a - t0:.4f})*lt(t,{b - t0:.4f})'[o{inp}]"
        )
        cur = f"o{inp}"
        inp += 1
    if ad_tag_png:
        cmd += ["-i", str(ad_tag_png)]
        filters.append(f"[{cur}][{inp}:v]overlay=0:0[o{inp}]")
        cur = f"o{inp}"
    cmd += ["-filter_complex", ";".join(filters), "-map", f"[{cur}]", "-frames:v", str(seg.frames)]
    cmd += _encode_args(cfg) + [str(out)]
    media.run(cmd)


def render_thumbnail(
    cut: Cut | None,
    clip_path: Path | None,
    background: Path | None,
    overlay_png: Path,
    out: Path,
    cfg: Config,
) -> None:
    """맨 앞 한 프레임짜리 썸네일."""
    fps = cfg.video.fps
    W, H = cfg.video.width, cfg.video.height
    if background is not None:
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(background)]
        filters = [f"[0:v]{media.cover_filter(W, H)},format=yuv420p[c0]"]
        cur = "c0"
    else:
        assert cut is not None and clip_path is not None
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{cut.best_frame / fps:.4f}", "-i", str(clip_path)]
        filters = [f"[0:v]{media.cover_filter(W, H)},format=yuv420p[c0]"]
        blur, cur = _blur_chain("c0", cut.blur_boxes, cfg)
        filters += blur
    cmd += ["-i", str(overlay_png)]
    filters.append(f"[{cur}][1:v]overlay=0:0,fps={fps}[out]")
    cmd += ["-filter_complex", ";".join(filters), "-map", "[out]", "-frames:v", "1"]
    cmd += _encode_args(cfg) + [str(out)]
    media.run(cmd)


def save_thumbnail_png(video: Path, out: Path) -> None:
    media.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-frames:v", "1", str(out)])


def concat(parts: list[Path], voice: Path, total_frames: int, out: Path, cfg: Config) -> None:
    """조각을 이어 붙이고 목소리를 넣는다. 썸네일 한 프레임만큼 목소리를 늦춘다."""
    fps = cfg.video.fps
    listing = out.parent / f"{out.stem}.concat.txt"
    listing.write_text(
        "".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf-8"
    )
    delay_ms = round(1000 / fps)
    af = [f"adelay={delay_ms}:all=1", f"volume={cfg.audio.gain_db}dB"]
    if cfg.audio.limiter:
        af.append("alimiter=limit=0.95:level=false")
    af.append("apad")
    duration = (total_frames + 1) / fps
    media.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(voice),
        "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-af", ",".join(af), "-c:a", "aac", "-b:a", cfg.audio.bitrate, "-ar", "48000",
        "-t", f"{duration:.4f}", "-movflags", "+faststart", str(out),
    ])
    listing.unlink(missing_ok=True)
