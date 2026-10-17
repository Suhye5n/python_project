"""클립 분석: 장면 전환, 선명도, 화면 속 글자, 제품이 보이는 정도.

분석은 출력과 같은 9:16 구도로 자른 화면(가로·세로 절반 크기)에서 한다.
결과는 `<작업폴더>/.cache` 에 저장해 두고, 같은 클립을 다시 돌릴 때 재사용한다.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from . import media
from .config import Config

log = logging.getLogger("shorts_maker")

CACHE_VERSION = 2
ANALYSIS_SCALE = 2  # 분석 화면은 출력의 1/2 크기
OCR_WIDTH = 360  # 글자 감지는 더 작은 화면에서 (속도 2배 이상, 자막 크기 글자는 충분히 잡힌다)
SHOT_HIST_THRESHOLD = 0.45
SHOT_GRAY_THRESHOLD = 10.0


@dataclass
class ClipAnalysis:
    name: str
    path: str
    src_width: int
    src_height: int
    frames: int  # 출력 fps 기준 전체 프레임 수
    shots: list[list[int]] = field(default_factory=list)  # [시작, 끝) 프레임
    sample_frames: list[int] = field(default_factory=list)
    product: list[float] = field(default_factory=list)
    sharpness: list[float] = field(default_factory=list)
    text_area: list[float] = field(default_factory=list)  # 화면 대비 글자 면적
    text_height: list[float] = field(default_factory=list)  # 가장 큰 글자 높이 / 화면 높이
    # 글자 감지 결과: [프레임, [[x0, y0, x1, y1], ...]] (출력 좌표, 1080x1920 기준)
    ocr: list[list] = field(default_factory=list)


# ---------------------------------------------------------------- 제품 점수


class ClipProductScorer:
    """CLIP 이미지 임베딩으로 '제품 사진과 얼마나 비슷한 장면인지' 계산."""

    name = "clip-vit-b32"

    def __init__(self, refs: list[Image.Image]):
        import open_clip
        import torch

        self.torch = torch
        if torch.cuda.is_available():
            self.device = "cuda"
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
        model, _, preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="laion2b_s34b_b79k"
        )
        self.model = model.to(self.device).eval()
        self.preprocess = preprocess
        self.refs = self._embed(refs)

    def _embed(self, images: list[Image.Image]):
        torch = self.torch
        with torch.no_grad():
            batch = torch.stack([self.preprocess(im) for im in images]).to(self.device)
            emb = self.model.encode_image(batch).float()
        return emb / emb.norm(dim=-1, keepdim=True)

    def score(self, frames: list[np.ndarray]) -> list[float]:
        out: list[float] = []
        for i in range(0, len(frames), 32):
            emb = self._embed([Image.fromarray(f) for f in frames[i : i + 32]])
            out.extend((emb @ self.refs.T).max(dim=1).values.cpu().tolist())
        return out


class FeatureProductScorer:
    """CLIP 을 못 쓸 때의 대안: 특징점(ORB) 매칭 + 색 분포 비교."""

    name = "orb-hist"

    def __init__(self, refs: list[Image.Image]):
        self.orb = cv2.ORB_create(nfeatures=1500)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        self.ref_desc = []
        self.ref_hist = []
        for im in refs:
            arr = np.asarray(im.convert("RGB"))
            scale = 720 / max(arr.shape[:2])
            if scale < 1:
                arr = cv2.resize(arr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            _, desc = self.orb.detectAndCompute(cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY), None)
            if desc is not None:
                self.ref_desc.append(desc)
            self.ref_hist.append(_hsv_hist(arr))

    def score(self, frames: list[np.ndarray]) -> list[float]:
        out = []
        for f in frames:
            _, desc = self.orb.detectAndCompute(cv2.cvtColor(f, cv2.COLOR_RGB2GRAY), None)
            good = 0
            if desc is not None and len(desc) >= 2:
                for ref in self.ref_desc:
                    pairs = self.matcher.knnMatch(ref, desc, k=2)
                    n = sum(1 for p in pairs if len(p) == 2 and p[0].distance < 0.75 * p[1].distance)
                    good = max(good, n)
            hist = _hsv_hist(f)
            color = max(cv2.compareHist(h, hist, cv2.HISTCMP_CORREL) for h in self.ref_hist)
            out.append(min(good, 60) / 60 + 0.3 * max(0.0, color))
        return out


class NullProductScorer:
    name = "none"

    def score(self, frames: list[np.ndarray]) -> list[float]:
        return [0.0] * len(frames)


def make_product_scorer(product_images: list[Path]):
    if not product_images:
        log.warning("product/ 폴더에 제품 사진이 없어 '제품이 보이는 장면' 점수는 빼고 고릅니다.")
        return NullProductScorer()
    refs = [Image.open(p).convert("RGB") for p in product_images]
    try:
        return ClipProductScorer(refs)
    except Exception as exc:  # 모델 다운로드 실패, 패키지 없음 등
        log.warning("CLIP 모델을 쓸 수 없어 특징점 매칭으로 대신합니다 (%s)", exc)
        return FeatureProductScorer(refs)


# ---------------------------------------------------------------- 글자 감지


class TextDetector:
    def __init__(self) -> None:
        import easyocr

        # 인식(무슨 글자인지)은 필요 없고 위치만 찾으면 되므로 감지 모델만 쓴다
        self.reader = easyocr.Reader(["ko", "en"], gpu=False, recognizer=False, verbose=False)

    def detect(self, frame: np.ndarray) -> list[list[int]]:
        horizontal, free = self.reader.detect(frame, min_size=8, text_threshold=0.6)
        boxes = [[int(b[0]), int(b[2]), int(b[1]), int(b[3])] for b in horizontal[0]]
        for poly in free[0]:
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            boxes.append([int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))])
        return boxes


# ---------------------------------------------------------------- 분석


def _hsv_hist(rgb: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256])
    return cv2.normalize(hist, hist).flatten()


def _sharpness(rgb: np.ndarray) -> float:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    return math.log1p(float(cv2.Laplacian(gray, cv2.CV_64F).var()))


def detect_shots(hist_diff: list[float], gray_diff: list[float], fps: int) -> list[list[int]]:
    """프레임 간 차이가 크게 튀는 곳을 장면 전환으로 본다."""
    n = len(hist_diff)
    cuts = [0]
    min_len = max(2, fps // 4)
    for i in range(1, n):
        if hist_diff[i] > SHOT_HIST_THRESHOLD and gray_diff[i] > SHOT_GRAY_THRESHOLD:
            if i - cuts[-1] >= min_len:
                cuts.append(i)
    cuts.append(n)
    return [[a, b] for a, b in zip(cuts, cuts[1:]) if b > a]


def _union_area(boxes: list[list[int]], w: int, h: int) -> float:
    if not boxes:
        return 0.0
    mask = np.zeros((h // 8 + 1, w // 8 + 1), dtype=bool)
    for x0, y0, x1, y1 in boxes:
        mask[max(0, y0) // 8 : y1 // 8 + 1, max(0, x0) // 8 : x1 // 8 + 1] = True
    return float(mask.mean())


def analyze_clip(path: Path, cfg: Config, scorer, detector: TextDetector) -> ClipAnalysis:
    fps = cfg.video.fps
    aw, ah = cfg.video.width // ANALYSIS_SCALE, cfg.video.height // ANALYSIS_SCALE
    sw, sh = media.video_size(path)
    sample_every = max(1, round(cfg.score.sample_step * fps))
    ocr_every = max(1, round(cfg.score.ocr_step * fps))

    hist_diff: list[float] = []
    gray_diff: list[float] = []
    prev_hist = prev_gray = None
    samples: list[np.ndarray] = []
    a = ClipAnalysis(name=path.name, path=str(path), src_width=sw, src_height=sh, frames=0)
    ocr_frames: list[int] = []
    ocr_boxes: list[list[list[int]]] = []

    for idx, buf in enumerate(media.read_frames(path, aw, ah, fps)):
        frame = np.frombuffer(buf, dtype=np.uint8).reshape(ah, aw, 3)
        small = cv2.resize(frame, (90, 160), interpolation=cv2.INTER_AREA)
        hist = _hsv_hist(small)
        gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY).astype(np.float32)
        if prev_hist is None:
            hist_diff.append(0.0)
            gray_diff.append(0.0)
        else:
            hist_diff.append(1.0 - float(cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)))
            gray_diff.append(float(np.abs(gray - prev_gray).mean()))
        prev_hist, prev_gray = hist, gray

        if idx % sample_every == 0:
            a.sample_frames.append(idx)
            a.sharpness.append(_sharpness(frame))
            samples.append(frame.copy())
        if idx % ocr_every == 0:
            k = cfg.video.width / OCR_WIDTH
            small_ocr = cv2.resize(frame, (OCR_WIDTH, round(ah * OCR_WIDTH / aw)), interpolation=cv2.INTER_AREA)
            boxes = [
                [round(x0 * k), round(y0 * k), round(x1 * k), round(y1 * k)]
                for x0, y0, x1, y1 in detector.detect(small_ocr)
            ]
            ocr_frames.append(idx)
            ocr_boxes.append(boxes)
        a.frames = idx + 1

    if a.frames == 0:
        raise media.MediaError(f"{path.name} 에서 프레임을 읽지 못했습니다.")

    a.shots = detect_shots(hist_diff, gray_diff, fps)
    a.product = scorer.score(samples)
    a.ocr = [[f, b] for f, b in zip(ocr_frames, ocr_boxes)]
    W, H = cfg.video.width, cfg.video.height
    for f in a.sample_frames:
        j = min(range(len(ocr_frames)), key=lambda k: abs(ocr_frames[k] - f))
        boxes = ocr_boxes[j]
        a.text_area.append(_union_area(boxes, W, H))
        a.text_height.append(max(((b[3] - b[1]) / H for b in boxes), default=0.0))
    return a


def _cache_key(path: Path, product_images: list[Path], scorer_name: str, cfg: Config) -> str:
    h = hashlib.sha1()
    for p in [path, *product_images]:
        st = p.stat()
        h.update(f"{p.name}|{st.st_size}|{int(st.st_mtime)}|".encode())
    h.update(
        f"{CACHE_VERSION}|{scorer_name}|{cfg.video.fps}|{cfg.video.width}x{cfg.video.height}"
        f"|{cfg.score.sample_step}|{cfg.score.ocr_step}".encode()
    )
    return h.hexdigest()[:16]


def analyze_all(
    clips: list[Path], product_images: list[Path], cfg: Config, cache_dir: Path
) -> list[ClipAnalysis]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    scorer = detector = None
    # 모델 로딩은 느리므로, 이전 분석 결과가 있으면 모델 없이 그대로 쓴다
    if product_images:
        names = [ClipProductScorer.name, FeatureProductScorer.name]
    else:
        names = [NullProductScorer.name]
    results = []
    for i, clip in enumerate(clips, 1):
        candidates = [
            cache_dir / f"{clip.stem}-{_cache_key(clip, product_images, n, cfg)}.json"
            for n in ([scorer.name] if scorer else names)
        ]
        cached = next((c for c in candidates if c.exists()), None)
        if cached:
            log.info("[%d/%d] %s (이전 분석 결과 사용)", i, len(clips), clip.name)
            results.append(ClipAnalysis(**json.loads(cached.read_text(encoding="utf-8"))))
            continue
        if detector is None:
            log.info("분석 모델을 불러오는 중… (처음 실행할 때는 모델을 내려받느라 몇 분 걸립니다)")
            scorer = make_product_scorer(product_images)
            detector = TextDetector()
        log.info("[%d/%d] %s 분석 중…", i, len(clips), clip.name)
        a = analyze_clip(clip, cfg, scorer, detector)
        out = cache_dir / f"{clip.stem}-{_cache_key(clip, product_images, scorer.name, cfg)}.json"
        out.write_text(json.dumps(asdict(a), ensure_ascii=False), encoding="utf-8")
        results.append(a)
    return results
