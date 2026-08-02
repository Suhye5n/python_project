"""수집·파싱 계층 테스트 (네트워크를 타지 않는다)."""

from __future__ import annotations

import datetime as dt
import unittest

from design_digest.models import CATEGORY_TREND
from design_digest.sources import FeedSource, RedditSource, load_sources
from design_digest.sources.feeds import FeedError, parse_feed
from design_digest.sources.hackernews import parse_hits, popularity_index
from design_digest.sources.reddit import parse_listing
from design_digest.util import (
    humanize_age,
    normalize_url,
    parse_datetime,
    shorten,
    strip_html,
    summarize,
)
from design_digest.config import DEFAULT_SOURCES_PATH

RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>Design Weekly</title>
    <item>
      <title><![CDATA[2026 컬러 트렌드 리포트]]></title>
      <link>https://example.com/color-trends-2026?utm_source=rss</link>
      <pubDate>Sat, 25 Jul 2026 09:30:00 +0000</pubDate>
      <dc:creator>김디자</dc:creator>
      <description><![CDATA[<p>올해의 팔레트는 <b>흙빛</b>이다. 두 번째 문장. 세 번째 문장.</p>]]></description>
      <media:content url="https://cdn.example.com/hero.jpg" medium="image" />
    </item>
    <item>
      <title>Design system governance in practice</title>
      <link>https://example.com/governance</link>
      <pubDate>Fri, 24 Jul 2026 22:00:00 +0000</pubDate>
      <content:encoded><![CDATA[<img src="https://cdn.example.com/tracking/pixel.gif" />
        <img src="https://cdn.example.com/real.png" /> 본문입니다.]]></content:encoded>
      <enclosure url="https://cdn.example.com/audio.mp3" type="audio/mpeg" />
    </item>
    <item>
      <title>링크 없는 항목</title>
    </item>
  </channel>
</rss>
"""

ATOM_SAMPLE = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Essays</title>
  <entry>
    <title>What design owes the people who use it</title>
    <link rel="edit" href="https://example.org/edit/1" />
    <link rel="alternate" href="https://example.org/essays/owes" />
    <updated>2026-07-25T04:00:00Z</updated>
    <author><name>Jane Doe</name></author>
    <summary>An essay about responsibility and craft.</summary>
  </entry>
</feed>
"""


class UtilTests(unittest.TestCase):
    def test_normalize_url_strips_tracking_and_www(self):
        self.assertEqual(
            normalize_url("https://WWW.Example.com/post/?utm_source=rss&id=3"),
            "https://example.com/post?id=3",
        )

    def test_normalize_url_treats_trailing_slash_as_same(self):
        self.assertEqual(
            normalize_url("https://example.com/a/"), normalize_url("http://example.com/a")
        )

    def test_strip_html_removes_scripts_and_entities(self):
        raw = "<div>hello <script>alert(1)</script>&amp; bye</div>"
        self.assertEqual(strip_html(raw), "hello & bye")

    def test_summarize_keeps_sentence_boundaries(self):
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        summary = summarize(text, max_chars=200, max_sentences=2)
        self.assertEqual(summary, "First sentence. Second sentence.")

    def test_shorten_adds_ellipsis(self):
        self.assertTrue(shorten("a" * 50, 10).endswith("…"))
        self.assertEqual(len(shorten("a" * 50, 10)), 10)

    def test_parse_datetime_handles_rfc822_and_iso(self):
        rfc = parse_datetime("Sat, 25 Jul 2026 09:30:00 +0000")
        iso = parse_datetime("2026-07-25T09:30:00Z")
        self.assertEqual(rfc, iso)
        self.assertEqual(rfc.tzinfo, dt.timezone.utc)

    def test_parse_datetime_returns_none_for_garbage(self):
        self.assertIsNone(parse_datetime("어제쯤?"))
        self.assertIsNone(parse_datetime(None))

    def test_humanize_age(self):
        now = dt.datetime(2026, 7, 26, 12, 0, tzinfo=dt.timezone.utc)
        self.assertEqual(humanize_age(now - dt.timedelta(minutes=5), now), "5분 전")
        self.assertEqual(humanize_age(now - dt.timedelta(hours=3), now), "3시간 전")
        self.assertEqual(humanize_age(now - dt.timedelta(days=2), now), "2일 전")


class FeedParsingTests(unittest.TestCase):
    def setUp(self):
        self.source = FeedSource(name="Design Weekly", url="https://example.com/feed", category=CATEGORY_TREND)

    def test_parses_rss_items(self):
        articles = parse_feed(RSS_SAMPLE, self.source)
        # 링크 없는 항목은 버려진다.
        self.assertEqual(len(articles), 2)

        first = articles[0]
        self.assertEqual(first.title, "2026 컬러 트렌드 리포트")
        self.assertEqual(first.source, "Design Weekly")
        self.assertEqual(first.author, "김디자")
        self.assertEqual(first.category, CATEGORY_TREND)
        self.assertEqual(first.image_url, "https://cdn.example.com/hero.jpg")
        self.assertIn("흙빛", first.summary)
        self.assertEqual(first.published.year, 2026)

    def test_skips_tracking_pixels_and_non_image_enclosures(self):
        articles = parse_feed(RSS_SAMPLE, self.source)
        second = articles[1]
        self.assertEqual(second.image_url, "https://cdn.example.com/real.png")

    def test_parses_atom_entries(self):
        articles = parse_feed(ATOM_SAMPLE, FeedSource(name="Essays", url="x"))
        self.assertEqual(len(articles), 1)
        entry = articles[0]
        # rel="alternate" 링크를 골라야 한다.
        self.assertEqual(entry.url, "https://example.org/essays/owes")
        self.assertEqual(entry.author, "Jane Doe")
        self.assertEqual(entry.summary, "An essay about responsibility and craft.")

    def test_broken_xml_raises_feed_error(self):
        with self.assertRaises(FeedError):
            parse_feed("<rss><channel>", self.source)

    def test_empty_feed_returns_empty_list(self):
        empty = '<?xml version="1.0"?><rss version="2.0"><channel><title>x</title></channel></rss>'
        self.assertEqual(parse_feed(empty, self.source), [])


class RedditParsingTests(unittest.TestCase):
    def setUp(self):
        self.source = RedditSource(subreddit="Design", min_score=50)
        self.payload = {
            "data": {
                "children": [
                    {"data": {
                        "title": "Brutalist poster series",
                        "permalink": "/r/Design/comments/abc/brutalist/",
                        "url_overridden_by_dest": "https://i.redd.it/abc.jpg",
                        "score": 1200, "num_comments": 45,
                        "created_utc": 1785000000, "author": "someone",
                    }},
                    {"data": {  # 점수 미달
                        "title": "low score", "permalink": "/r/Design/comments/d/",
                        "url": "https://i.redd.it/d.png", "score": 3,
                        "created_utc": 1785000000,
                    }},
                    {"data": {  # 고정글
                        "title": "sticky", "stickied": True, "score": 5000,
                        "url": "https://i.redd.it/e.png", "permalink": "/x/",
                    }},
                    {"data": {  # 이미지 없음 (텍스트 글)
                        "title": "discussion", "is_self": True, "score": 900,
                        "permalink": "/y/",
                    }},
                    {"data": {  # preview 로만 이미지가 있는 링크 글
                        "title": "linked article", "permalink": "/r/Design/comments/f/",
                        "url": "https://example.com/article", "score": 300,
                        "num_comments": 10, "created_utc": 1785000000,
                        "preview": {"images": [{"source": {"url": "https://preview.redd.it/f.jpg"}}]},
                    }},
                ]
            }
        }

    def test_filters_and_maps_posts(self):
        items = parse_listing(self.payload, self.source)
        self.assertEqual([i.title for i in items], ["Brutalist poster series", "linked article"])

        top = items[0]
        self.assertEqual(top.image_url, "https://i.redd.it/abc.jpg")
        self.assertEqual(top.url, "https://www.reddit.com/r/Design/comments/abc/brutalist/")
        self.assertEqual(top.popularity, 1200)
        self.assertEqual(top.author, "u/someone")
        self.assertIn("1,200", top.popularity_note)

    def test_uses_preview_image_for_link_posts(self):
        items = parse_listing(self.payload, self.source)
        self.assertEqual(items[1].image_url, "https://preview.redd.it/f.jpg")

    def test_prefers_resized_preview_over_full_size_original(self):
        payload = {"data": {"children": [{"data": {
            "title": "huge poster", "permalink": "/h/", "score": 700,
            "post_hint": "image", "url": "https://i.redd.it/huge.png",
            "preview": {"images": [{
                "source": {"url": "https://preview.redd.it/huge.png", "width": 4000},
                "resolutions": [
                    {"url": "https://preview.redd.it/w320.jpg", "width": 320},
                    {"url": "https://preview.redd.it/w960.jpg", "width": 960},
                    {"url": "https://preview.redd.it/w2000.jpg", "width": 2000},
                ],
            }]},
        }}]}}
        items = parse_listing(payload, self.source)
        # 목표 폭(1080)을 넘지 않는 가장 큰 리사이즈본
        self.assertEqual(items[0].image_url, "https://preview.redd.it/w960.jpg")

    def test_gallery_post_uses_first_media(self):
        payload = {"data": {"children": [{"data": {
            "title": "gallery", "permalink": "/g/", "score": 500,
            "url": "https://www.reddit.com/gallery/g",
            "media_metadata": {"k1": {"s": {"u": "https://i.redd.it/gallery1.jpg"}}},
        }}]}}
        items = parse_listing(payload, self.source)
        self.assertEqual(items[0].image_url, "https://i.redd.it/gallery1.jpg")


class HackerNewsTests(unittest.TestCase):
    def test_parse_hits_filters_by_points(self):
        payload = {"hits": [
            {"title": "A new design system", "url": "https://example.com/ds",
             "points": 140, "num_comments": 30, "objectID": "1", "created_at_i": 1785000000},
            {"title": "meh", "url": "https://example.com/meh", "points": 5, "objectID": "2"},
            {"title": "Ask HN: design career", "points": 60, "objectID": "3",
             "num_comments": 12, "created_at_i": 1785000000},
        ]}
        articles = parse_hits(payload, min_points=20)
        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0].popularity, 140)
        self.assertIn("HN 140점", articles[0].popularity_note)
        # url 이 없는 Ask HN 글은 토론 링크로 대체된다.
        self.assertEqual(articles[1].url, "https://news.ycombinator.com/item?id=3")

    def test_popularity_index_normalizes_urls(self):
        payload = {"hits": [{"title": "t", "url": "https://www.example.com/ds/?utm_source=hn",
                             "points": 90, "objectID": "9"}]}
        index = popularity_index(parse_hits(payload, 10))
        self.assertIn(normalize_url("https://example.com/ds"), index)


class SourcesConfigTests(unittest.TestCase):
    def test_bundled_sources_file_loads(self):
        sources = load_sources(DEFAULT_SOURCES_PATH)
        self.assertGreater(len(sources.feeds), 10)
        self.assertTrue(sources.hackernews.enabled)
        # 모든 피드에 카테고리가 붙어 있어야 분류 폴백이 동작한다.
        for feed in sources.feeds:
            self.assertIn(feed.category, {"trend", "methodology", "philosophy", "general"})
            self.assertTrue(feed.url.startswith("https://"))

    def test_bundled_file_has_working_image_sources(self):
        """Reddit 을 꺼두었으므로 이미지는 스크랩 소스가 책임진다."""
        sources = load_sources(DEFAULT_SOURCES_PATH)
        enabled = [s for s in sources.scrapes if s.enabled]
        # 클라우드 IP 에서 실제로 동작하는 것만 켜둔다 (자바스크립트 봇 검증에
        # 막히는 곳은 enabled = false).
        self.assertGreaterEqual(len(enabled), 2)
        for scrape in enabled:
            self.assertIn(scrape.strategy, {"json", "embedded_json", "html", "og"})
            self.assertTrue(scrape.url.startswith("https://"))
            # html 전략은 어떤 링크를 항목으로 볼지 지정해야 의미가 있다.
            if scrape.strategy == "html":
                self.assertTrue(scrape.link_pattern)

    def test_reddit_label_defaults_to_subreddit(self):
        self.assertEqual(RedditSource(subreddit="typography").label, "r/typography")


if __name__ == "__main__":
    unittest.main()
