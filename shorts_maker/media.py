"""ffmpeg / ffprobe 호출."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Iterator

log = logging.getLogger("shorts_maker")


class MediaError(RuntimeError):
    pass


def require_ffmpeg() -> None:
    missing = [b for b in ("ffmpeg", "ffprobe") if not shutil.which(b)]
    if missing:
        raise MediaError(
            f"{', '.join(missing)} 가 설치돼 있지 않습니다. 맥에서는 `brew install ffmpeg` 로 설치하세요."
        )


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        raise MediaError(f"{path.name} 을 읽을 수 없습니다: {out.stderr.strip()[:300]}")
    return json.loads(out.stdout)


def duration(path: Path) -> float:
    info = probe(path)
    try:
        return float(info["format"]["duration"])
    except (KeyError, ValueError):
        raise MediaError(f"{path.name} 의 길이를 알 수 없습니다.") from None


def video_size(path: Path) -> tuple[int, int]:
    """회전 정보까지 반영한, 실제로 보이는 가로·세로 크기."""
    info = probe(path)
    for s in info.get("streams", []):
        if s.get("codec_type") != "video":
            continue
        w, h = int(s["width"]), int(s["height"])
        rotation = 0
        for sd in s.get("side_data_list", []):
            if "rotation" in sd:
                rotation = int(float(sd["rotation"]))
        rotation = rotation or int(s.get("tags", {}).get("rotate", 0) or 0)
        if abs(rotation) % 180 == 90:
            w, h = h, w
        return w, h
    raise MediaError(f"{path.name} 에 영상 트랙이 없습니다.")


def cover_filter(width: int, height: int) -> str:
    """비율이 달라도 빈 곳 없이 꽉 차게 확대한 뒤 가운데를 잘라낸다."""
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={width}:{height},setsar=1"
    )


def read_frames(path: Path, width: int, height: int, fps: int) -> Iterator[bytes]:
    """출력과 같은 구도로 자른 프레임(RGB24)을 차례로 돌려준다."""
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(path), "-an",
        "-vf", f"fps={fps},{cover_filter(width, height)}",
        "-pix_fmt", "rgb24", "-f", "rawvideo", "-",
    ]
    size = width * height * 3
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None
    try:
        while True:
            buf = proc.stdout.read(size)
            if len(buf) < size:
                break
            yield buf
    finally:
        proc.stdout.close()
        proc.kill()
        proc.wait()


def run(cmd: list[str]) -> None:
    log.debug("$ %s", " ".join(cmd))
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise MediaError(f"ffmpeg 실패:\n{out.stderr.strip()[-1500:]}")
