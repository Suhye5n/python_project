"""주제 좁히기.

소스를 아무리 골라도 매체 하나가 여러 분야를 다룬다. Dezeen 은 건축이 절반이고
Smashing Magazine 은 대부분 웹 개발이다. 그래서 소스 단위가 아니라 **글 단위**로
관심 분야를 거른다.

기본값은 시각디자인(그래픽 · 타이포그래피 · 폰트 · 일러스트 · 브랜딩 · 편집 · 패키지)이고,
키워드 목록은 `sources.toml` 의 `[focus]` 에서 바꾼다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .models import Article

#: 시각디자인으로 볼 신호
DEFAULT_INCLUDE = (
    # 그래픽 · 편집 · 브랜딩
    "graphic design", "graphic designer", "visual identity", "brand identity", "rebrand",
    "branding", "logo", "logotype", "wordmark", "editorial design", "layout", "poster",
    "packaging", "book cover", "album art", "print design", "signage", "art direction",
    # 타이포그래피 · 폰트
    "typography", "typographic", "typeface", "type design", "type designer", "font",
    "fonts", "lettering", "calligraphy", "monospace", "serif", "sans-serif", "glyph",
    "variable font", "typesetting",
    # 일러스트 · 이미지
    "illustration", "illustrator", "drawing", "collage", "risograph", "screen print",
    "printmaking", "comic", "zine", "artwork", "mural",
    # 색 · 형태
    "color palette", "colour palette", "pantone", "color of the year", "grid system",
    "moodboard",
    # 한국어
    "그래픽", "시각디자인", "타이포", "타이포그래피", "서체", "폰트", "글꼴", "레터링",
    "일러스트", "삽화", "포스터", "브랜딩", "브랜드 아이덴티티", "로고", "편집디자인",
    "패키지", "패키징", "인쇄", "출판", "굿즈", "리브랜딩", "비주얼", "아트디렉션",
    "컬러", "색채", "전시", "작업물", "포트폴리오",
)

#: 시각디자인이 아닌 쪽으로 강하게 기우는 신호 (제목에 있으면 탈락)
DEFAULT_EXCLUDE = (
    "architecture", "architect", "interior design", "furniture", "real estate",
    "javascript", "typescript", "css framework", "react", "vue", "api", "backend",
    "devops", "kubernetes", "database", "server", "sql",
    "seo", "growth hacking", "conversion rate", "a/b test",
    "smartphone review", "laptop", "gadget", "automotive", "electric vehicle",
    "건축", "인테리어", "가구", "부동산", "자바스크립트", "백엔드", "서버",
)


def _compile(words) -> list[re.Pattern]:
    return [
        re.compile(rf"\b{re.escape(w)}\b" if w.isascii() else re.escape(w), re.IGNORECASE)
        for w in words
    ]


@dataclass
class Focus:
    """관심 분야 필터.

    기본값은 '끔'이다. 켜는 것은 `sources.toml` 의 `[focus]` 이고, 코드에서
    그냥 만든 Focus() 가 조용히 글을 걸러내는 일은 없어야 한다.
    """

    enabled: bool = False
    include: tuple[str, ...] = DEFAULT_INCLUDE
    exclude: tuple[str, ...] = DEFAULT_EXCLUDE
    #: 소스가 이미 그 분야 전용이면 필터를 건너뛴다 (예: 타이포그래피 전문지)
    always_keep_sources: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self._include = _compile(self.include)
        self._exclude = _compile(self.exclude)

    def matched(self, text: str, patterns: list[re.Pattern]) -> str:
        for word, pattern in zip(self.include if patterns is self._include else self.exclude, patterns):
            if pattern.search(text):
                return word
        return ""

    def keeps(self, article: Article) -> bool:
        """이 글을 리포트에 넣을지."""
        if not self.enabled:
            return True
        if article.source in self.always_keep_sources:
            return True

        title = article.title or ""
        body = article.summary or ""

        # 제목이 다른 분야를 가리키면 본문에 뭐가 있든 뺀다.
        if self.matched(title, self._exclude):
            return False
        if self.matched(title, self._include):
            return True
        # 제목만으로 판단이 안 되면 본문을 본다. 단 본문에도 배제어가 있으면 뺀다.
        if body and self.matched(body, self._include) and not self.matched(body, self._exclude):
            return True
        return False

    def apply(self, articles: list[Article]) -> tuple[list[Article], int]:
        """통과한 글 목록과 걸러진 개수."""
        if not self.enabled:
            return articles, 0
        kept = [a for a in articles if self.keeps(a)]
        return kept, len(articles) - len(kept)


def from_toml(data: dict) -> Focus:
    """sources.toml 의 `[focus]` 섹션을 읽는다.

    섹션이 아예 없으면 필터를 걸지 않는다. 섹션이 있으면 기본은 켜짐.
    """
    # 섹션을 아예 안 쓴 것과 빈 섹션을 써둔 것은 다르다.
    declared = "focus" in data
    section = data.get("focus", {})
    return Focus(
        enabled=bool(section.get("enabled", declared)),
        include=tuple(section.get("include", DEFAULT_INCLUDE)),
        exclude=tuple(section.get("exclude", DEFAULT_EXCLUDE)),
        always_keep_sources=tuple(section.get("always_keep_sources", ())),
    )
