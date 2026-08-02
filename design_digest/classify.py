"""글을 트렌드 / 방법론 / 철학으로 분류.

LLM 없이 키워드 가중치로 판정한다. 제목에 걸린 단어를 본문보다 크게 친다.
어느 쪽도 확실치 않으면 소스에 지정된 기본 카테고리를 따른다.
"""

from __future__ import annotations

import re

from .models import (
    CATEGORY_GENERAL,
    CATEGORY_METHODOLOGY,
    CATEGORY_PHILOSOPHY,
    CATEGORY_TREND,
    Article,
)

TITLE_WEIGHT = 3
BODY_WEIGHT = 1
#: 이 점수를 넘겨야 소스 기본값을 뒤집는다.
DECISION_THRESHOLD = 4

KEYWORDS: dict[str, tuple[str, ...]] = {
    CATEGORY_TREND: (
        "trend", "trends", "2026", "2027", "aesthetic", "brutalism", "brutalist",
        "minimalism", "maximalism", "retro", "y2k", "glassmorphism", "skeuomorph",
        "gradient", "palette", "color of the year", "rebrand", "redesign", "unveil",
        "launch", "collection", "exhibition", "showcase", "installation", "concept",
        "inspiration", "roundup", "best of", "new logo", "identity", "spatial",
        "generative", "ai-generated", "motion", "3d",
        "트렌드", "유행", "리브랜딩", "리뉴얼", "출시", "공개", "전시", "컬렉션", "감성",
    ),
    CATEGORY_METHODOLOGY: (
        "method", "methodology", "process", "framework", "workflow", "system",
        "design system", "design token", "component", "guideline", "research",
        "usability", "accessibility", "wcag", "a11y", "user testing", "user research",
        "heuristic", "prototype", "prototyping", "wireframe", "atomic design",
        "double diamond", "design thinking", "jobs to be done", "journey map",
        "persona", "how to", "how i", "tutorial", "step by step", "checklist",
        "best practice", "case study", "metrics", "a/b test", "information architecture",
        "ux writing", "handoff", "documentation",
        "방법론", "프로세스", "워크플로", "디자인 시스템", "리서치", "사용성", "접근성",
        "가이드", "설계", "실무", "사례", "정리", "노하우", "체크리스트",
    ),
    CATEGORY_PHILOSOPHY: (
        "philosophy", "manifesto", "ethic", "ethics", "meaning", "why design",
        "craft", "critique", "criticism", "essay", "reflection", "taste", "beauty",
        "value", "values", "responsibility", "sustainable", "sustainability",
        "humane", "human-centered", "future of design", "role of design",
        "what design", "opinion", "rethinking", "lessons", "legacy", "culture",
        "interview",
        "철학", "관점", "본질", "태도", "가치", "비평", "에세이", "성찰", "생각", "인터뷰",
        "지속가능", "윤리",
    ),
}

# 단어 경계를 쓰되, 한글에는 \b 가 잘 안 먹으므로 ASCII 단어일 때만 적용한다.
_COMPILED = {
    category: [
        re.compile(rf"\b{re.escape(word)}\b" if word.isascii() else re.escape(word), re.IGNORECASE)
        for word in words
    ]
    for category, words in KEYWORDS.items()
}


def score_categories(title: str, body: str = "") -> dict[str, int]:
    """카테고리별 키워드 점수."""
    scores: dict[str, int] = {}
    for category, patterns in _COMPILED.items():
        total = 0
        for pattern in patterns:
            if pattern.search(title):
                total += TITLE_WEIGHT
            elif body and pattern.search(body):
                total += BODY_WEIGHT
        scores[category] = total
    return scores


def matched_keywords(title: str, body: str = "", limit: int = 4) -> list[str]:
    """리포트에 태그로 보여줄 매칭 키워드."""
    found: list[str] = []
    text_title, text_body = title, body
    for category, words in KEYWORDS.items():
        for word, pattern in zip(words, _COMPILED[category]):
            if pattern.search(text_title) or (text_body and pattern.search(text_body)):
                if word not in found:
                    found.append(word)
    return found[:limit]


def classify(article: Article, default_category: str = CATEGORY_GENERAL) -> str:
    """글 하나의 카테고리를 정한다."""
    body = article.summary or ""
    scores = score_categories(article.title, body)
    best_category, best_score = max(scores.items(), key=lambda kv: kv[1])

    if best_score >= DECISION_THRESHOLD:
        return best_category

    # 키워드가 약하면 매체 성격을 따른다.
    fallback = article.category if article.category != CATEGORY_GENERAL else default_category
    if fallback != CATEGORY_GENERAL:
        return fallback
    return best_category if best_score > 0 else CATEGORY_GENERAL


def apply(articles: list[Article]) -> list[Article]:
    """목록 전체에 분류와 키워드 태그를 채워 넣는다."""
    for article in articles:
        article.category = classify(article)
        article.keywords = matched_keywords(article.title, article.summary)
    return articles
