"""스타일 설정.

기본값은 지금까지 만든 쇼츠(1080x1920, 30fps)를 측정해서 정했다.
바꾸고 싶은 값만 `shorts_maker.toml` 에 적으면 된다 (`shorts_maker.example.toml` 참고).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
DEFAULT_CONFIG_PATH = PROJECT_DIR / "shorts_maker.toml"


@dataclass
class VideoConfig:
    width: int = 1080
    height: int = 1920
    fps: int = 30
    crf: int = 17  # 낮을수록 고화질 (17이면 눈으로 원본과 구분이 어렵다)
    preset: str = "medium"


@dataclass
class CutConfig:
    max_speed: float = 2.5  # 배속 상한
    per_source_limit: float = 5.0  # 한 원본 영상에서 가져다 쓸 수 있는 화면 시간 합계(초)
    # 장면(샷)이 자막 구간보다 길 때:
    #   "fit"     장면이 max_speed 안에서 통째로 들어가면 배속해서 전부 보여주고,
    #             더 길면 가장 좋은 부분만 1배속으로 잘라 쓴다.
    #   "natural" 항상 1배속으로 가장 좋은 부분만 잘라 쓴다.
    long_shot: str = "fit"
    shot_margin: float = 0.07  # 장면 전환 직후/직전 프레임은 피한다(초)


@dataclass
class ScoreConfig:
    product: float = 1.0  # 제품이 잘 보이는 정도
    sharpness: float = 0.5  # 선명도
    text: float = 1.5  # 화면 속 글자 (클수록 글자 있는 장면을 더 피한다)
    resolution: float = 0.5  # 원본 해상도가 낮은 클립 감점
    sample_step: float = 0.25  # 분석 간격(초)
    ocr_step: float = 0.5  # 글자 감지 간격(초)


@dataclass
class AudioConfig:
    gain_db: float = 15.0
    limiter: bool = True  # 소리가 깨지지 않도록 리미터 적용
    bitrate: str = "192k"


@dataclass
class BlurConfig:
    enabled: bool = True
    sigma: float = 22.0  # 블러 세기
    padding: int = 16  # 감지된 글자 상자를 넓히는 여유(px)
    # 컷 안에서 이 비율 이상 같은 자리에 있는 글자만 '자막'으로 보고 가린다.
    # (제품에 인쇄된 로고처럼 움직이는 글자는 가리지 않기 위함)
    min_persistence: float = 0.35


@dataclass
class SubtitleConfig:
    font: str = "fonts/subtitle.ttf"
    glyph_height: int = 64  # 한글 글자 높이(px). 캡컷 15pt 를 측정한 값
    center_y: int = 505  # 자막 세로 중심(px, 위에서부터)
    max_width: int = 1000  # 이 폭을 넘으면 자막을 다시 달라고 알린다
    color: str = "#FFFFFF"
    shadow_color: str = "#000000"
    shadow_stroke: int = 3  # 그림자를 글자 바깥으로 넓히는 정도
    shadow_blur: float = 5.0  # 그림자 번짐
    shadow_strength: float = 1.6  # 그림자 진하기


@dataclass
class ThumbnailConfig:
    font: str = "fonts/thumbnail.ttf"
    glyph_height: int = 140
    center_y: int = 548  # 텍스트 묶음의 세로 중심
    line_spacing: int = 188  # 줄 간격(줄 중심 사이 거리)
    color: str = "#FFFFFF"
    highlight_color: str = "#FDF7AE"  # *강조* 로 감싼 단어 색
    stroke: int = 11
    stroke_color: str = "#000000"
    max_width: int = 1000
    # "auto": 제품이 가장 잘 보이는 프레임 / 아니면 배경으로 쓸 이미지 파일 경로
    background: str = "auto"


@dataclass
class AdTagConfig:
    enabled: bool = True
    text: str = "[광고]"
    font: str = ""  # 비우면 자막 폰트
    glyph_height: int = 40
    center_x: int = 928
    center_y: int = 240
    color: str = "#FFFFFF"
    stroke: int = 2
    stroke_color: str = "#3A3A3A"


@dataclass
class Config:
    video: VideoConfig = field(default_factory=VideoConfig)
    cut: CutConfig = field(default_factory=CutConfig)
    score: ScoreConfig = field(default_factory=ScoreConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    blur: BlurConfig = field(default_factory=BlurConfig)
    subtitle: SubtitleConfig = field(default_factory=SubtitleConfig)
    thumbnail: ThumbnailConfig = field(default_factory=ThumbnailConfig)
    ad_tag: AdTagConfig = field(default_factory=AdTagConfig)
    base_dir: Path = PROJECT_DIR  # 폰트 등 상대 경로의 기준

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        cfg = cls()
        path = path or DEFAULT_CONFIG_PATH
        if path.exists():
            with path.open("rb") as fh:
                _apply(cfg, tomllib.load(fh), "")
            cfg.base_dir = path.resolve().parent
        return cfg

    def resolve(self, raw: str) -> Path:
        p = Path(raw).expanduser()
        return p if p.is_absolute() else self.base_dir / p


def _apply(target: Any, data: dict[str, Any], prefix: str) -> None:
    known = {f.name: f for f in fields(target)}
    for key, value in data.items():
        if key not in known or key == "base_dir":
            raise ValueError(f"설정 파일에 모르는 항목이 있습니다: {prefix}{key}")
        current = getattr(target, key)
        if is_dataclass(current):
            if not isinstance(value, dict):
                raise ValueError(f"[{prefix}{key}] 는 표(table)여야 합니다.")
            _apply(current, value, f"{prefix}{key}.")
        else:
            if isinstance(current, float) and isinstance(value, int):
                value = float(value)
            if type(value) is not type(current):
                raise ValueError(
                    f"{prefix}{key} 의 값 형식이 맞지 않습니다: {value!r}"
                )
            setattr(target, key, value)
