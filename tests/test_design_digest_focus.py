"""관심 분야 필터 (시각디자인으로 좁히기) 테스트."""

from __future__ import annotations

import unittest

from design_digest.focus import Focus, from_toml
from design_digest.models import Article
from design_digest.config import DEFAULT_SOURCES_PATH
from design_digest.sources import load_sources


def article(title: str, summary: str = "", source: str = "테스트") -> Article:
    return Article(title=title, url="https://e.com/x", source=source, summary=summary)


class FocusTests(unittest.TestCase):
    def setUp(self):
        self.focus = Focus(enabled=True)

    def test_keeps_typography_and_font_articles(self):
        for title in (
            "The typeface that defined a decade",
            "A new variable font for editorial work",
            "타이포그래피로 읽는 브랜드",
            "새 서체 출시",
        ):
            self.assertTrue(self.focus.keeps(article(title)), title)

    def test_keeps_graphic_illustration_branding(self):
        for title in (
            "Studio unveils new visual identity for a museum",
            "An illustrator's process, from sketch to risograph",
            "포스터 시리즈 작업기",
            "패키지 디자인 리뉴얼",
        ):
            self.assertTrue(self.focus.keeps(article(title)), title)

    def test_drops_architecture_and_interior(self):
        for title in (
            "House in the woods by a Tokyo architecture studio",
            "Interior design trends for small apartments",
            "건축가가 말하는 공간",
        ):
            self.assertFalse(self.focus.keeps(article(title)), title)

    def test_drops_web_development(self):
        for title in (
            "How to use CSS framework grid utilities",
            "Building a React component library",
            "A guide to server side rendering",
        ):
            self.assertFalse(self.focus.keeps(article(title)), title)

    def test_exclude_in_title_beats_include_in_body(self):
        item = article(
            "New apartment interior design revealed",
            summary="The branding and typography of the building signage is lovely.",
        )
        self.assertFalse(self.focus.keeps(item))

    def test_body_can_rescue_an_ambiguous_title(self):
        item = article(
            "Studio profile: 스튜디오 방문기",
            summary="이번 작업은 전시 포스터와 브랜딩 작업을 함께 진행했다.",
        )
        self.assertTrue(self.focus.keeps(item))

    def test_unrelated_article_is_dropped(self):
        self.assertFalse(self.focus.keeps(article("Quarterly earnings report")))

    def test_always_keep_sources_bypass_filter(self):
        focus = Focus(enabled=True, always_keep_sources=("Typographica",))
        item = article("Reviews of 2026", source="Typographica")
        self.assertTrue(focus.keeps(item))
        self.assertFalse(focus.keeps(article("Reviews of 2026", source="다른 매체")))

    def test_disabled_filter_keeps_everything(self):
        focus = Focus(enabled=False)
        self.assertTrue(focus.keeps(article("House by an architecture studio")))

    def test_apply_reports_filtered_count(self):
        items = [
            article("New typeface released"),
            article("Interior design trends"),
            article("Brand identity for a bakery"),
        ]
        kept, dropped = self.focus.apply(items)
        self.assertEqual(len(kept), 2)
        self.assertEqual(dropped, 1)

    def test_custom_keyword_lists(self):
        focus = Focus(enabled=True, include=("모션그래픽",), exclude=("인쇄",))
        self.assertTrue(focus.keeps(article("모션그래픽 작업 공개")))
        self.assertFalse(focus.keeps(article("인쇄 공정 이야기")))
        self.assertFalse(focus.keeps(article("타이포그래피")))  # include 에 없으면 탈락


class FocusConfigTests(unittest.TestCase):
    def test_no_focus_section_means_no_filtering(self):
        """설정에 [focus] 가 없으면 조용히 걸러내지 않는다."""
        self.assertFalse(from_toml({}).enabled)

    def test_empty_focus_section_turns_it_on(self):
        focus = from_toml({"focus": {}})
        self.assertTrue(focus.enabled)
        self.assertIn("typography", focus.include)

    def test_from_toml_overrides(self):
        focus = from_toml({"focus": {"enabled": False, "include": ["a"], "exclude": ["b"]}})
        self.assertFalse(focus.enabled)
        self.assertEqual(focus.include, ("a",))

    def test_bundled_sources_enable_visual_focus(self):
        sources = load_sources(DEFAULT_SOURCES_PATH)
        self.assertTrue(sources.focus.enabled)
        # 전문지는 필터를 건너뛰도록 지정되어 있어야 한다
        self.assertIn("Typographica", sources.focus.always_keep_sources)

    def test_bundled_feeds_are_visual_design_oriented(self):
        """UX·개발 중심 매체가 꺼져 있는지 확인."""
        sources = load_sources(DEFAULT_SOURCES_PATH)
        names = {feed.name for feed in sources.feeds}
        for off_topic in ("CSS-Tricks", "UX Planet", "Nielsen Norman Group", "Yanko Design"):
            self.assertNotIn(off_topic, names)


if __name__ == "__main__":
    unittest.main()
