"""SRT 자막 파싱과 컷 구간 계산 (표준 라이브러리만 사용)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_TIME = re.compile(r"(\d+):(\d{1,2}):(\d{1,2})[,.](\d{1,3})")


class SrtError(ValueError):
    pass


@dataclass
class Subtitle:
    index: int  # 1부터 시작하는 순번
    start: float
    end: float
    text: str


@dataclass
class Segment:
    """출력 영상에서 컷 하나가 차지하는 구간 (프레임 단위, [start, end))."""

    start: int
    end: int
    subtitle_index: int  # 이 구간을 만든 자막 (0부터)

    @property
    def frames(self) -> int:
        return self.end - self.start


def _parse_time(raw: str) -> float:
    m = _TIME.search(raw)
    if not m:
        raise SrtError(f"시간 형식을 읽을 수 없습니다: {raw!r}")
    h, mi, s, ms = m.groups()
    return int(h) * 3600 + int(mi) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000


def parse_srt(content: str) -> list[Subtitle]:
    content = content.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    subs: list[Subtitle] = []
    for block in re.split(r"\n\s*\n", content.strip()):
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        arrow = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if arrow is None:
            raise SrtError(f"시간 줄(-->)이 없는 블록이 있습니다: {block[:40]!r}")
        start_raw, end_raw = lines[arrow].split("-->", 1)
        start, end = _parse_time(start_raw), _parse_time(end_raw)
        if end <= start:
            raise SrtError(f"끝 시간이 시작 시간보다 빠릅니다: {lines[arrow]}")
        # 여러 줄로 적힌 자막은 한 줄로 합친다 (화면에는 항상 1줄)
        text = " ".join(re.sub(r"<[^>]+>", "", line) for line in lines[arrow + 1 :]).strip()
        subs.append(Subtitle(index=len(subs) + 1, start=start, end=end, text=text))
    if not subs:
        raise SrtError("자막이 하나도 없습니다.")
    subs.sort(key=lambda s: s.start)
    for i, s in enumerate(subs, 1):
        s.index = i
    return subs


def load_srt(path: Path) -> list[Subtitle]:
    return parse_srt(path.read_text(encoding="utf-8-sig", errors="replace"))


def build_segments(
    subs: list[Subtitle], total_frames: int, fps: int, max_frames: int
) -> list[Segment]:
    """자막이 바뀌는 시점마다 컷을 나눈다.

    첫 컷은 0초부터, 마지막 컷은 음성이 끝날 때까지 이어진다.
    한 구간이 `max_frames` 보다 길면 (한 영상에서 쓸 수 있는 시간 제한 때문에)
    같은 길이로 쪼갠다.
    """
    starts = [0] + [round(s.start * fps) for s in subs[1:]]
    bounds = starts + [total_frames]
    segments: list[Segment] = []
    for i in range(len(subs)):
        a, b = bounds[i], bounds[i + 1]
        if b <= a:
            if a >= total_frames:
                raise SrtError(
                    f"{subs[i].index}번 자막({subs[i].text!r})이 음성 파일이 끝난 뒤에 시작합니다."
                )
            raise SrtError(f"{subs[i].index}번 자막과 다음 자막의 시작 시간이 같습니다.")
        parts = max(1, -(-(b - a) // max_frames))
        for p in range(parts):
            segments.append(
                Segment(a + (b - a) * p // parts, a + (b - a) * (p + 1) // parts, i)
            )
    return segments
