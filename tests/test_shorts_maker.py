"""shorts_maker 의 자막 파싱·컷 계획 테스트 (ffmpeg·모델 없이 돈다)."""

from __future__ import annotations

import unittest
from dataclasses import dataclass, field

from shorts_maker.config import Config
from shorts_maker.planner import PlanError, blur_boxes, plan_cuts
from shorts_maker.srt import SrtError, build_segments, parse_srt

SRT = """﻿1
00:00:00,000 --> 00:00:02,000
첫 번째 자막

2
00:00:02,000 --> 00:00:03,500
두 번째
자막

3
00:00:04,000 --> 00:00:06,000
<i>세 번째</i>
"""


@dataclass
class FakeAnalysis:
    name: str
    shots: list[list[int]]
    frames: int
    src_width: int = 1080
    src_height: int = 1920
    sample_frames: list[int] = field(default_factory=list)
    product: list[float] = field(default_factory=list)
    sharpness: list[float] = field(default_factory=list)
    text_area: list[float] = field(default_factory=list)
    text_height: list[float] = field(default_factory=list)
    ocr: list[list] = field(default_factory=list)

    def __post_init__(self):
        if not self.sample_frames:
            self.sample_frames = list(range(0, self.frames, 8))
        n = len(self.sample_frames)
        self.product = self.product or [0.5] * n
        self.sharpness = self.sharpness or [1.0] * n
        self.text_area = self.text_area or [0.0] * n
        self.text_height = self.text_height or [0.0] * n


class SrtTest(unittest.TestCase):
    def test_parse(self):
        subs = parse_srt(SRT)
        self.assertEqual([s.text for s in subs], ["첫 번째 자막", "두 번째 자막", "세 번째"])
        self.assertAlmostEqual(subs[1].end, 3.5)
        self.assertEqual(subs[2].index, 3)

    def test_bad_time(self):
        with self.assertRaises(SrtError):
            parse_srt("1\n00:00:02,000 --> 00:00:01,000\n뒤집힌 시간\n")

    def test_segments_follow_subtitle_starts(self):
        subs = parse_srt(SRT)
        segs = build_segments(subs, total_frames=210, fps=30, max_frames=150)
        self.assertEqual([(s.start, s.end) for s in segs], [(0, 60), (60, 120), (120, 210)])

    def test_long_segment_is_split(self):
        subs = parse_srt("1\n00:00:00,000 --> 00:00:08,000\n길다\n")
        segs = build_segments(subs, total_frames=240, fps=30, max_frames=150)
        self.assertEqual([(s.start, s.end) for s in segs], [(0, 120), (120, 240)])
        self.assertTrue(all(s.subtitle_index == 0 for s in segs))

    def test_subtitle_after_audio(self):
        subs = parse_srt(SRT)
        with self.assertRaises(SrtError):
            build_segments(subs, total_frames=100, fps=30, max_frames=150)


class PlannerTest(unittest.TestCase):
    def setUp(self):
        self.cfg = Config()
        subs = parse_srt(SRT)
        self.segments = build_segments(subs, total_frames=210, fps=30, max_frames=150)

    def test_respects_limits(self):
        clips = [FakeAnalysis(f"c{i}.mp4", [[0, 200]], 200) for i in range(3)]
        cuts = plan_cuts(self.segments, clips, self.cfg)
        self.assertEqual(len(cuts), 3)
        per_clip: dict[int, int] = {}
        for c in cuts:
            self.assertGreaterEqual(c.speed, 1.0)
            self.assertLessEqual(c.speed, self.cfg.cut.max_speed)
            per_clip[c.clip] = per_clip.get(c.clip, 0) + c.segment.frames
        self.assertTrue(all(v <= 150 for v in per_clip.values()))

    def test_no_overlap_within_clip(self):
        clips = [FakeAnalysis("one.mp4", [[0, 100], [100, 200], [200, 330]], 330)]
        segs = build_segments(parse_srt(SRT), total_frames=150, fps=30, max_frames=150)[:2]
        cuts = plan_cuts(segs, clips, self.cfg)
        a, b = sorted((c.src_start, c.src_end) for c in cuts)
        self.assertLessEqual(a[1], b[0])

    def test_short_shot_speeds_up_whole_shot(self):
        # 2초 구간에 3초짜리 장면 하나 → 통째로 1.5배속
        clips = [FakeAnalysis("a.mp4", [[0, 94]], 94)]
        segs = build_segments(parse_srt("1\n00:00:00,000 --> 00:00:02,000\n자막\n"), 60, 30, 150)
        cut = plan_cuts(segs, clips, self.cfg)[0]
        self.assertGreater(cut.speed, 1.4)

    def test_prefers_product_scene(self):
        good = FakeAnalysis("good.mp4", [[0, 200]], 200)
        good.product = [3.0] * len(good.sample_frames)
        clips = [FakeAnalysis("plain.mp4", [[0, 200]], 200), good]
        segs = build_segments(parse_srt("1\n00:00:00,000 --> 00:00:02,000\n자막\n"), 60, 30, 150)
        self.assertEqual(plan_cuts(segs, clips, self.cfg)[0].clip, 1)

    def test_not_enough_footage(self):
        clips = [FakeAnalysis("short.mp4", [[0, 40]], 40)]
        with self.assertRaises(PlanError):
            plan_cuts(self.segments, clips, self.cfg)


class BlurTest(unittest.TestCase):
    def test_static_text_only(self):
        cfg = Config()
        subtitle = [200, 500, 880, 560]
        ocr = [[f, [subtitle] + ([[100, 1500, 300, 1540]] if f == 0 else [])] for f in range(0, 60, 15)]
        boxes = blur_boxes(ocr, 0, 60, cfg)
        self.assertEqual(len(boxes), 1)
        x0, y0, x1, y1 = boxes[0]
        self.assertLessEqual(x0, 200)
        self.assertGreaterEqual(y1, 560)


if __name__ == "__main__":
    unittest.main()
