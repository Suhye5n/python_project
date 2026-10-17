"""컷 계획: 자막 구간마다 어떤 클립의 어느 부분을 쓸지 고른다.

규칙
- 장면(샷) 길이는 자막 구간 이상이어야 한다 (느리게 늘리지 않는다).
- 장면이 구간보다 길면 최대 `max_speed` 배까지 빠르게 해서 맞춘다.
- 한 번 쓴 부분은 다시 쓰지 않는다.
- 한 원본 영상에서 가져온 컷의 화면 시간 합계는 `per_source_limit` 초 이하.
"""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field

from .config import Config
from .srt import Segment

log = logging.getLogger("shorts_maker")

WHOLE_SHOT_BONUS = 0.15  # 동작이 끊기지 않게 장면을 통째로 쓰는 쪽을 조금 우대
NEIGHBOR_PENALTY = 0.3  # 바로 옆 컷과 같은 영상이면 감점
SOURCE_GAP_FRAMES = 3  # 같은 영상에서 컷 두 개를 뽑을 때 사이에 두는 간격


class PlanError(RuntimeError):
    pass


@dataclass
class Cut:
    segment: Segment
    clip: int  # analyses 인덱스
    src_start: int  # 원본 프레임 (출력 fps 기준)
    src_end: int
    score: float
    best_frame: int  # 컷 안에서 점수가 가장 높은 원본 프레임
    best_score: float
    blur_boxes: list[list[int]] = field(default_factory=list)

    @property
    def speed(self) -> float:
        return (self.src_end - self.src_start) / self.segment.frames


def _zscores(values: list[float]) -> list[float]:
    if len(values) < 2:
        return [0.0] * len(values)
    mean = statistics.fmean(values)
    std = statistics.pstdev(values) or 1.0
    return [(v - mean) / std for v in values]


def frame_scores(analyses, cfg: Config) -> list[list[float]]:
    """모든 클립의 분석 지점마다 '이 장면을 쓰고 싶은 정도'를 매긴다."""
    sc = cfg.score
    flat_p = [v for a in analyses for v in a.product]
    flat_s = [v for a in analyses for v in a.sharpness]
    zp, zs = _zscores(flat_p), _zscores(flat_s)
    out: list[list[float]] = []
    k = 0
    for a in analyses:
        res_deficit = max(0.0, 1.0 - min(a.src_width, a.src_height) / cfg.video.width)
        scores = []
        for area, height in zip(a.text_area, a.text_height):
            # 글자 면적 + 너무 큰 글자(원본 자막이 큰 경우)
            text_pen = min(3.0, 12.0 * area) + min(3.0, max(0.0, (height - 0.035) / 0.02))
            scores.append(
                sc.product * zp[k] + sc.sharpness * zs[k] - sc.text * text_pen
                - sc.resolution * 3.0 * res_deficit
            )
            k += 1
        out.append(scores)
    return out


class _ClipScores:
    """한 클립의 분석 지점 점수를 프레임 구간으로 빠르게 조회."""

    def __init__(self, frames: list[int], scores: list[float]):
        self.frames = frames
        self.scores = scores
        self.prefix = [0.0]
        for s in scores:
            self.prefix.append(self.prefix[-1] + s)

    def _range(self, a: int, b: int) -> tuple[int, int]:
        import bisect

        i = bisect.bisect_left(self.frames, a)
        j = bisect.bisect_left(self.frames, b)
        if j <= i:  # 구간이 분석 간격보다 짧으면 가장 가까운 지점 하나
            mid = (a + b) / 2
            i = min(range(len(self.frames)), key=lambda k: abs(self.frames[k] - mid))
            j = i + 1
        return i, j

    def window(self, a: int, b: int) -> float:
        i, j = self._range(a, b)
        mean = (self.prefix[j] - self.prefix[i]) / (j - i)
        return 0.7 * mean + 0.3 * min(self.scores[i:j])

    def best(self, a: int, b: int) -> tuple[int, float]:
        i, j = self._range(a, b)
        k = max(range(i, j), key=lambda k: self.scores[k])
        return self.frames[k], self.scores[k]


def _candidates(n: int, shots: list[list[int]], cfg: Config):
    """길이 n 프레임 구간에 넣을 수 있는 (원본 시작, 끝, 통째 여부) 후보."""
    fps = cfg.video.fps
    margin = round(cfg.cut.shot_margin * fps)
    step = max(1, fps // 10)
    max_len = int(n * cfg.cut.max_speed + 1e-9)
    for s0, s1 in shots:
        a, b = s0 + margin, s1 - margin
        length = b - a
        if length < n:
            continue
        if cfg.cut.long_shot == "fit" and length <= max_len:
            yield a, b, True
        for start in range(a, b - n + 1, step):
            yield start, start + n, False


def plan_cuts(segments: list[Segment], analyses, cfg: Config) -> list[Cut]:
    if cfg.cut.long_shot not in ("fit", "natural"):
        raise PlanError('cut.long_shot 은 "fit" 또는 "natural" 이어야 합니다.')
    scores = [_ClipScores(a.sample_frames, s) for a, s in zip(analyses, frame_scores(analyses, cfg))]
    limit = round(cfg.cut.per_source_limit * cfg.video.fps)
    used: list[list[tuple[int, int]]] = [[] for _ in analyses]
    screen_time = [0] * len(analyses)
    chosen: dict[int, Cut] = {}

    order = sorted(range(len(segments)), key=lambda i: -segments[i].frames)
    for si in order:
        seg = segments[si]
        n = seg.frames
        neighbors = {chosen[j].clip for j in (si - 1, si + 1) if j in chosen}
        best: tuple[float, int, int, int] | None = None
        for ci, a in enumerate(analyses):
            if screen_time[ci] + n > limit:
                continue
            for start, end, whole in _candidates(n, a.shots, cfg):
                if any(start < u1 + SOURCE_GAP_FRAMES and u0 < end + SOURCE_GAP_FRAMES for u0, u1 in used[ci]):
                    continue
                value = scores[ci].window(start, end)
                if whole:
                    value += WHOLE_SHOT_BONUS
                if ci in neighbors:
                    value -= NEIGHBOR_PENALTY
                if best is None or value > best[0]:
                    best = (value, ci, start, end)
        if best is None:
            raise PlanError(
                f"{seg.subtitle_index + 1}번 자막 구간({n / cfg.video.fps:.2f}초)에 쓸 장면이 부족합니다. "
                f"이 길이 이상인 장면이 있는 클립을 더 넣어주세요. "
                f"(한 영상당 {cfg.cut.per_source_limit:g}초 제한, 최대 {cfg.cut.max_speed:g}배속)"
            )
        value, ci, start, end = best
        frame, fscore = scores[ci].best(start, end)
        chosen[si] = Cut(seg, ci, start, end, value, frame, fscore)
        used[ci].append((start, end))
        screen_time[ci] += n

    cuts = [chosen[i] for i in range(len(segments))]
    for cut in cuts:
        cut.blur_boxes = blur_boxes(analyses[cut.clip].ocr, cut.src_start, cut.src_end, cfg)
    return cuts


# ---------------------------------------------------------------- 원본 자막 가리기


def _overlaps(a: list[int], b: list[int]) -> bool:
    """같은 자리에 있는 글자인지 (세로는 절반 이상 겹치고 가로도 겹침)."""
    vy = min(a[3], b[3]) - max(a[1], b[1])
    vx = min(a[2], b[2]) - max(a[0], b[0])
    return vx > 0 and vy >= 0.5 * min(a[3] - a[1], b[3] - b[1])


def blur_boxes(ocr: list[list], start: int, end: int, cfg: Config) -> list[list[int]]:
    """컷 안에서 계속 같은 자리에 떠 있는 글자(=원본 자막) 영역을 돌려준다."""
    if not cfg.blur.enabled or not ocr:
        return []
    samples = [boxes for f, boxes in ocr if start <= f < end]
    if not samples:
        mid = (start + end) / 2
        samples = [min(ocr, key=lambda o: abs(o[0] - mid))[1]]
    keep = []
    for boxes in samples:
        for box in boxes:
            hits = sum(1 for other in samples if any(_overlaps(box, o) for o in other))
            if hits / len(samples) >= cfg.blur.min_persistence:
                keep.append(box)
    pad = cfg.blur.padding
    W, H = cfg.video.width, cfg.video.height
    rects = [[max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)] for x0, y0, x1, y1 in keep]
    # 겹치는 상자는 하나로 합친다
    merged = True
    while merged:
        merged = False
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                a, b = rects[i], rects[j]
                if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                    rects[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    del rects[j]
                    merged = True
                    break
            if merged:
                break
    # 너무 작은 건 무시 (오검출)
    return [r for r in rects if (r[2] - r[0]) >= 24 and (r[3] - r[1]) >= 16]


def thumbnail_source(cuts: list[Cut]) -> Cut:
    """썸네일 배경으로 쓸 컷: 제품이 가장 잘 보이는 프레임이 있는 컷."""
    return max(cuts, key=lambda c: c.best_score)
