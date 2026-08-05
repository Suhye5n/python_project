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
VISUAL_KEYWORDS = (
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

#: UX · 인터랙션 · 디자인 방법론 신호
UX_KEYWORDS = (
    "ux", "ui design", "user experience", "user interface", "usability",
    "usability testing", "user research", "user testing", "interaction design",
    "product design", "design system", "design token", "component library",
    "wireframe", "prototype", "prototyping", "information architecture",
    "accessibility", "wcag", "a11y", "journey map", "user journey", "persona",
    "design process", "design thinking", "double diamond", "heuristic",
    "ux writing", "microcopy", "onboarding flow", "navigation", "usability heuristics",
    "design critique", "design ops", "handoff",
    "사용성", "사용자 경험", "사용자 조사", "유저 리서치", "인터랙션", "디자인 시스템",
    "프로토타입", "와이어프레임", "정보구조", "접근성", "퍼소나", "페르소나",
    "온보딩", "디자인 프로세스", "디자인 방법론", "사용자 인터페이스", "화면 설계",
)

#: 그룹 이름으로 골라 쓴다. sources.toml 의 `groups` 참고.
KEYWORD_GROUPS = {
    "visual": VISUAL_KEYWORDS,
    "ux": UX_KEYWORDS,
}
DEFAULT_GROUPS = ("visual", "ux")

#: 관심 밖으로 강하게 기우는 신호 (제목에 있으면 탈락).
#: 순수 엔지니어링·마케팅·공간/제품 분야만 넣는다. UX 방법론은 여기 없다.
DEFAULT_EXCLUDE = (
    "architecture", "architect", "interior design", "furniture", "real estate",
    "javascript", "typescript", "css framework", "react", "vue", "backend",
    "devops", "kubernetes", "database", "sql", "compiler", "docker",
    "seo", "growth hacking", "crypto", "blockchain",
    "smartphone review", "laptop", "gadget", "automotive", "electric vehicle",
    "건축", "인테리어", "가구", "부동산", "자바스크립트", "백엔드", "서버 구축",
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

    분야는 `groups` 로 고른다. 시각디자인만 보고 싶으면 `["visual"]`,
    UX 까지 보고 싶으면 `["visual", "ux"]`.
    """

    enabled: bool = False
    #: 쓸 키워드 그룹 (KEYWORD_GROUPS 의 이름)
    groups: tuple[str, ...] = DEFAULT_GROUPS
    #: 그룹에 더할 단어. 그룹을 비우고 이것만 쓸 수도 있다.
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = DEFAULT_EXCLUDE
    #: 소스가 이미 그 분야 전용이면 필터를 건너뛴다 (예: 타이포그래피 전문지)
    always_keep_sources: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        words: list[str] = []
        for name in self.groups:
            words.extend(KEYWORD_GROUPS.get(name, ()))
        words.extend(self.include)
        #: 실제로 쓰이는 포함어 (그룹 + 추가 단어, 중복 제거)
        self.words = tuple(dict.fromkeys(words))
        self._include = _compile(self.words)
        self._exclude = _compile(self.exclude)

    def _spans(self, text: str, words, patterns) -> list[tuple[int, int, str]]:
        """걸린 단어들의 위치 (시작, 끝, 단어)."""
        found = []
        for word, pattern in zip(words, patterns):
            match = pattern.search(text)
            if match:
                found.append((match.start(), match.end(), word))
        return found

    def matched(self, text: str, patterns: list[re.Pattern]) -> str:
        """걸린 단어 하나 (없으면 빈 문자열)."""
        words = self.words if patterns is self._include else self.exclude
        spans = self._spans(text, words, patterns)
        return spans[0][2] if spans else ""

    def _verdict(self, text: str) -> bool | None:
        """한 덩어리의 텍스트로 판정. 판단이 안 서면 None.

        배제어가 포함어 **안에 파묻혀 있으면** 무시한다.
        'information architecture'(UX) 안의 'architecture'(건축)가 그런 경우다.
        반대로 'React component library' 처럼 둘이 서로 다른 자리에서 걸리면
        배제어가 이긴다 — 그건 정말 엔지니어링 글이다.
        """
        includes = self._spans(text, self.words, self._include)
        excludes = self._spans(text, self.exclude, self._exclude)

        excludes = [
            span
            for span in excludes
            if not any(inc[0] <= span[0] and span[1] <= inc[1] for inc in includes)
        ]
        if excludes:
            return False
        if includes:
            return True
        return None

    def keeps(self, article: Article) -> bool:
        """이 글을 리포트에 넣을지."""
        if not self.enabled:
            return True
        if article.source in self.always_keep_sources:
            return True

        # 제목이 우선이다. 제목으로 판정이 나면 본문은 보지 않는다.
        verdict = self._verdict(article.title or "")
        if verdict is not None:
            return verdict

        # 제목이 애매하면 본문을 본다.
        return bool(article.summary) and self._verdict(article.summary) is True

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
        groups=tuple(section.get("groups", DEFAULT_GROUPS)),
        include=tuple(section.get("include", ())),
        exclude=tuple(section.get("exclude", DEFAULT_EXCLUDE)),
        always_keep_sources=tuple(section.get("always_keep_sources", ())),
    )
