"""스크랩 계층 테스트.

실제 사이트 HTML 을 그대로 가져올 수는 없으므로, 각 사이트가 쓰는 **구조**를
본뜬 픽스처로 검증한다. 검증하는 것은 "Behance 가 오늘도 되는가"가 아니라
"이런 모양이면 뽑아낼 수 있는가" 이다.
"""

from __future__ import annotations

import json
import unittest

from design_digest.sources import FeedSource, ScrapeSource
from design_digest.sources.feeds import parse_feed, to_image_items
from design_digest.sources.scrape import (
    autodetect_items,
    dig,
    extract_embedded_json,
    extract_meta,
    find_image,
    parse_count,
    parse_scrape,
    pick_srcset,
)

# Next.js 계열(노트폴리오·비핸스)이 쓰는 모양: script 안에 통째로 JSON
NEXT_DATA_PAGE = """<!DOCTYPE html><html><head>
<meta property="og:image" content="https://cdn.example.com/og-cover.jpg" />
<meta property="og:title" content="디스커버" />
<title>노트폴리오</title></head><body>
<script id="__NEXT_DATA__" type="application/json">
{"props":{"pageProps":{"projects":[
  {"id":1,"title":"브랜드 아이덴티티 리뉴얼","slug":"/i/1",
   "thumbnail":{"url":"https://cdn.example.com/work1.jpg"},"likeCount":"1.2k"},
  {"id":2,"title":"패키지 디자인","slug":"/i/2",
   "thumbnail":{"url":"https://cdn.example.com/work2.jpg"},"likeCount":340},
  {"id":3,"title":"타이포그래피 실험","slug":"/i/3",
   "thumbnail":{"url":"https://cdn.example.com/work3.jpg"},"likeCount":89}
]}}}
</script></body></html>"""

# window 변수에 할당하는 옛날 방식
WINDOW_ASSIGN_PAGE = """<html><head></head><body>
<script>window.__INITIAL_STATE__ = {"gallery":{"items":[
  {"name":"Poster series","url":"/gallery/1","covers":{"original":"https://cdn.b.net/1.jpg"},
   "stats":{"appreciations":2400,"comments":31}},
  {"name":"Editorial layout","url":"/gallery/2","covers":{"original":"https://cdn.b.net/2.jpg"},
   "stats":{"appreciations":880,"comments":12}},
  {"name":"Motion study","url":"/gallery/3","covers":{"original":"https://cdn.b.net/3.jpg"},
   "stats":{"appreciations":150,"comments":3}}
]}};</script></body></html>"""

# Dribbble 류: 카드 그리드 HTML
CARD_GRID_PAGE = """<html><body>
<div class="shot">
  <a href="/shots/111-first-shot" aria-label="First shot">
    <img srcset="https://cdn.d.com/1_small.jpg 400w,
                 https://cdn.d.com/1_mid.jpg 800w,
                 https://cdn.d.com/1_huge.jpg 2400w" alt="First shot" />
  </a>
</div>
<div class="shot">
  <a href="/shots/222-second-shot"><span>Second shot</span></a>
  <img src="https://cdn.d.com/2.jpg" alt="Second" />
</div>
<div class="nav"><a href="/designers"><img src="https://cdn.d.com/icon-logo.png" /></a></div>
<div class="shot">
  <a href="/shots/111-first-shot"><img src="https://cdn.d.com/dup.jpg" /></a>
</div>
</body></html>"""

# RSSHub 가 인스타그램/핀터레스트를 바꿔주는 모양
RSSHUB_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel>
<title>Instagram - somedesigner</title>
<item>
  <title>새 포스터 작업</title>
  <link>https://www.instagram.com/p/ABC123/</link>
  <pubDate>Sat, 25 Jul 2026 09:30:00 +0000</pubDate>
  <description><![CDATA[<img src="https://scontent.example.com/post1.jpg" />캡션]]></description>
</item>
<item>
  <title>텍스트만 있는 글</title>
  <link>https://www.instagram.com/p/DEF456/</link>
  <description>이미지 없음</description>
</item>
</channel></rss>"""


class ValueHelperTests(unittest.TestCase):
    def test_parse_count_handles_korean_site_formats(self):
        self.assertEqual(parse_count("1,234"), 1234)
        self.assertEqual(parse_count("1.2k"), 1200)
        self.assertEqual(parse_count("3.4M"), 3_400_000)
        self.assertEqual(parse_count(880), 880)
        self.assertEqual(parse_count("좋아요"), 0)
        self.assertEqual(parse_count(None), 0)

    def test_dig_walks_dicts_and_lists(self):
        data = {"a": {"b": [{"c": 7}]}}
        self.assertEqual(dig(data, "a.b.0.c"), 7)
        self.assertIsNone(dig(data, "a.b.9.c"))
        self.assertIsNone(dig(data, "a.zzz"))
        self.assertEqual(dig(data, ""), data)

    def test_find_image_prefers_image_like_keys(self):
        node = {"title": "x", "cover": {"url": "https://cdn/x.jpg"}, "author": "https://cdn/y.jpg"}
        self.assertEqual(find_image(node), "https://cdn/x.jpg")

    def test_find_image_ignores_icons(self):
        self.assertEqual(find_image({"image": "https://cdn/logo-icon.png"}), "")

    def test_pick_srcset_respects_target_width(self):
        srcset = "https://a/1.jpg 400w, https://a/2.jpg 800w, https://a/3.jpg 2400w"
        self.assertEqual(pick_srcset(srcset), "https://a/2.jpg")

    def test_autodetect_finds_largest_image_bearing_list(self):
        data = json.loads(NEXT_DATA_PAGE.split(">", 2)[2].split("</script>")[0]) \
            if False else json.loads(
                NEXT_DATA_PAGE.split('type="application/json">')[1].split("</script>")[0]
            )
        found = autodetect_items(data)
        self.assertEqual(len(found), 3)
        self.assertEqual(found[0]["title"], "브랜드 아이덴티티 리뉴얼")


class MetaTests(unittest.TestCase):
    def test_extracts_og_tags_and_title(self):
        meta = extract_meta(NEXT_DATA_PAGE)
        self.assertEqual(meta.image, "https://cdn.example.com/og-cover.jpg")
        self.assertEqual(meta.headline, "디스커버")

    def test_falls_back_to_title_tag(self):
        meta = extract_meta("<html><head><title>월간디자인</title></head><body></body></html>")
        self.assertEqual(meta.headline, "월간디자인")
        self.assertEqual(meta.image, "")


class EmbeddedJsonTests(unittest.TestCase):
    def test_extracts_next_data_by_marker(self):
        blobs = extract_embedded_json(NEXT_DATA_PAGE, "__NEXT_DATA__")
        self.assertEqual(len(blobs), 1)
        self.assertIn("props", blobs[0])

    def test_extracts_window_assignment(self):
        blobs = extract_embedded_json(WINDOW_ASSIGN_PAGE)
        self.assertEqual(len(blobs), 1)
        self.assertIn("gallery", blobs[0])

    def test_ignores_non_json_scripts(self):
        html = "<script>console.log('hi')</script><script>{bad json}</script>"
        self.assertEqual(extract_embedded_json(html), [])


class ScrapeStrategyTests(unittest.TestCase):
    def test_embedded_json_with_autodetect_only(self):
        """필드 매핑을 하나도 안 적어도 구조를 스스로 찾아낸다."""
        source = ScrapeSource(name="노트폴리오", url="https://notefolio.net/discover",
                              base_url="https://notefolio.net",
                              strategy="embedded_json", marker="__NEXT_DATA__")
        items = parse_scrape(NEXT_DATA_PAGE, source)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].title, "브랜드 아이덴티티 리뉴얼")
        self.assertEqual(items[0].image_url, "https://cdn.example.com/work1.jpg")
        self.assertEqual(items[0].source, "노트폴리오")

    def test_embedded_json_with_explicit_fields(self):
        source = ScrapeSource(
            name="Behance", url="https://www.behance.net/galleries/graphic-design",
            base_url="https://www.behance.net", strategy="embedded_json",
            fields={"title": "name", "link": "url", "image": "covers.original",
                    "score": "stats.appreciations", "comments": "stats.comments"},
        )
        items = parse_scrape(WINDOW_ASSIGN_PAGE, source)
        self.assertEqual(len(items), 3)
        top = items[0]
        self.assertEqual(top.title, "Poster series")
        self.assertEqual(top.popularity, 2400)
        self.assertEqual(top.comments, 31)
        # 상대경로가 절대경로로 바뀐다
        self.assertEqual(top.url, "https://www.behance.net/gallery/1")
        self.assertIn("좋아요 2,400", top.popularity_note)

    def test_autodetects_link_and_like_count_without_field_mapping(self):
        """필드명을 몰라도 링크와 좋아요 수를 찾아낸다.

        링크를 못 찾으면 항목들이 전부 페이지 주소로 뭉쳐서 중복 제거에
        잡아먹히기 때문에, 이게 되는지가 중요하다.
        """
        source = ScrapeSource(name="노트폴리오", url="https://notefolio.net/discover",
                              base_url="https://notefolio.net",
                              strategy="embedded_json", marker="__NEXT_DATA__")
        items = parse_scrape(NEXT_DATA_PAGE, source)
        self.assertEqual(
            [i.url for i in items],
            ["https://notefolio.net/i/1", "https://notefolio.net/i/2", "https://notefolio.net/i/3"],
        )
        # "1.2k" 같은 표기도 숫자로
        self.assertEqual([i.popularity for i in items], [1200, 340, 89])

    def test_link_template_builds_page_url_from_id(self):
        """Behance 처럼 항목에 주소 없이 id/slug 만 있을 때.

        이걸 못 만들면 리포트에서 제목을 눌렀을 때 작품 페이지가 아니라
        이미지 파일이 열린다.
        """
        payload = json.dumps([
            {"id": 12345, "slug": "poster-series", "name": "Poster series",
             "covers": {"original": "https://mir-s3-cdn.behance.net/1.jpg"},
             "stats": {"appreciations": 900}},
            {"id": 67890, "slug": "type-specimen", "name": "Type specimen",
             "covers": {"original": "https://mir-s3-cdn.behance.net/2.jpg"},
             "stats": {"appreciations": 400}},
            {"id": 11111, "slug": "brand-book", "name": "Brand book",
             "covers": {"original": "https://mir-s3-cdn.behance.net/3.jpg"},
             "stats": {"appreciations": 120}},
        ])
        source = ScrapeSource(
            name="Behance · 그래픽", url="https://www.behance.net/galleries/graphic-design",
            base_url="https://www.behance.net", strategy="json",
            fields={"title": "name", "score": "stats.appreciations"},
            link_template="https://www.behance.net/gallery/{id}/{slug}",
        )
        items = parse_scrape(payload, source)
        self.assertEqual(items[0].url, "https://www.behance.net/gallery/12345/poster-series")
        self.assertEqual(items[1].url, "https://www.behance.net/gallery/67890/type-specimen")
        # 이미지 파일 주소가 링크로 새어나오면 안 된다
        for item in items:
            self.assertNotIn(".jpg", item.url)

    def test_link_template_ignored_when_keys_missing(self):
        payload = json.dumps([
            {"name": "A", "cover": "https://cdn/1.jpg", "permalink": "/work/a"},
            {"name": "B", "cover": "https://cdn/2.jpg", "permalink": "/work/b"},
            {"name": "C", "cover": "https://cdn/3.jpg", "permalink": "/work/c"},
        ])
        source = ScrapeSource(name="x", url="https://x", base_url="https://x",
                              strategy="json", link_template="https://x/gallery/{id}/{slug}")
        items = parse_scrape(payload, source)
        # 틀이 안 맞으면 키 이름으로 찾은 링크를 쓴다
        self.assertEqual(items[0].url, "https://x/work/a")

    def test_finds_page_link_by_value_shape(self):
        """키 이름이 낯설어도 값 모양으로 페이지 링크를 알아본다."""
        payload = json.dumps([
            {"headline": "작업 A", "media": "https://cdn/1.jpg", "detailPath": "/project/1"},
            {"headline": "작업 B", "media": "https://cdn/2.jpg", "detailPath": "/project/2"},
            {"headline": "작업 C", "media": "https://cdn/3.jpg", "detailPath": "/project/3"},
        ])
        source = ScrapeSource(name="x", url="https://site.example/list",
                              base_url="https://site.example", strategy="json")
        items = parse_scrape(payload, source)
        self.assertEqual(items[0].url, "https://site.example/project/1")

    def test_falls_back_to_image_url_when_no_link_found(self):
        payload = json.dumps([
            {"caption": "작업 1", "cover": "https://cdn/1.jpg"},
            {"caption": "작업 2", "cover": "https://cdn/2.jpg"},
            {"caption": "작업 3", "cover": "https://cdn/3.jpg"},
        ])
        source = ScrapeSource(name="x", url="https://x/gallery", strategy="json")
        items = parse_scrape(payload, source)
        # 전부 같은 URL 이 되면 안 된다 (중복 제거에 사라진다)
        self.assertEqual(len({i.url for i in items}), 3)

    def test_min_popularity_filters_items(self):
        source = ScrapeSource(name="Behance", url="https://b.net", strategy="embedded_json",
                              fields={"score": "stats.appreciations"}, min_popularity=500)
        items = parse_scrape(WINDOW_ASSIGN_PAGE, source)
        self.assertEqual([i.popularity for i in items], [2400, 880])

    def test_html_cards_pairs_links_and_images(self):
        source = ScrapeSource(name="Dribbble", url="https://dribbble.com/shots/popular",
                              base_url="https://dribbble.com", strategy="html",
                              link_pattern="/shots/")
        items = parse_scrape(CARD_GRID_PAGE, source)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].url, "https://dribbble.com/shots/111-first-shot")
        # srcset 에서 목표 폭 이하 최대치를 고른다
        self.assertEqual(items[0].image_url, "https://cdn.d.com/1_mid.jpg")
        self.assertEqual(items[0].title, "First shot")
        # 링크 패턴에 안 맞는 네비게이션 로고는 제외
        self.assertNotIn("icon-logo.png", " ".join(i.image_url for i in items))

    def test_html_cards_picks_sibling_image(self):
        source = ScrapeSource(name="Dribbble", url="https://dribbble.com", strategy="html",
                              link_pattern="/shots/")
        items = parse_scrape(CARD_GRID_PAGE, source)
        second = items[1]
        self.assertEqual(second.image_url, "https://cdn.d.com/2.jpg")
        self.assertEqual(second.title, "Second shot")

    def test_limit_is_applied(self):
        source = ScrapeSource(name="x", url="https://x", strategy="embedded_json", limit=2)
        self.assertEqual(len(parse_scrape(NEXT_DATA_PAGE, source)), 2)

    def test_no_og_fallback_by_default(self):
        """목록을 못 읽었다고 사이트 간판 이미지를 대신 싣지는 않는다."""
        source = ScrapeSource(name="월간디자인", url="https://mdesign.designhouse.co.kr/",
                              strategy="html", link_pattern="/article/")
        self.assertEqual(parse_scrape(NEXT_DATA_PAGE, source), [])

    def test_og_fallback_when_explicitly_enabled(self):
        page = (
            '<html><head><meta property="og:image" '
            'content="https://cdn.example.com/2026/07/exhibition-hero.jpg" />'
            '<meta property="og:title" content="전시 리뷰" /></head><body></body></html>'
        )
        source = ScrapeSource(name="월간디자인", url="https://mdesign.designhouse.co.kr/article/1",
                              strategy="html", link_pattern="/article/", og_fallback=True)
        items = parse_scrape(page, source)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].image_url, "https://cdn.example.com/2026/07/exhibition-hero.jpg")
        self.assertEqual(items[0].title, "전시 리뷰")

    def test_generic_share_image_is_rejected(self):
        """노트폴리오에서 잡히던 'OG Notefolio Standard.jpg' 같은 간판 이미지."""
        page = (
            '<html><head><meta property="og:image" '
            'content="https://cdn.example.kr/static/feature/seo/OG_Notefolio_Standard.jpg" />'
            '<meta property="og:title" content="노트폴리오" /></head><body></body></html>'
        )
        source = ScrapeSource(name="노트폴리오", url="https://notefolio.net/discover",
                              strategy="og", og_fallback=True)
        self.assertEqual(parse_scrape(page, source), [])

    def test_json_strategy_on_plain_api_response(self):
        payload = json.dumps({"data": {"pins": [
            {"title": "무드보드", "image_url": "https://i.pinimg.com/1.jpg", "link": "/pin/1",
             "saves": 3200},
            {"title": "컬러칩", "image_url": "https://i.pinimg.com/2.jpg", "link": "/pin/2",
             "saves": 90},
        ]}})
        source = ScrapeSource(name="Pinterest", url="https://api.example/pins",
                              base_url="https://www.pinterest.com", strategy="json",
                              json_path="data.pins",
                              fields={"title": "title", "image": "image_url", "link": "link",
                                      "score": "saves"})
        items = parse_scrape(payload, source)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].url, "https://www.pinterest.com/pin/1")
        self.assertEqual(items[0].popularity, 3200)

    def test_notefolio_style_api_envelope(self):
        """노트폴리오처럼 화면이 호출하는 API 를 직접 부르는 경우.

        응답 껍데기(data/items 등)를 몰라도 자동 탐색으로 목록을 찾아내고,
        CDN 호스트만 있고 확장자가 없는 이미지 주소도 인식해야 한다.
        """
        payload = json.dumps({
            "code": 200,
            "message": "OK",
            "data": {
                "cursor": "eyJ0YWJsZSI6...",
                "items": [
                    {"id": 897235, "title": "브랜드 리뉴얼 프로젝트", "url": "/i/897235",
                     "thumbnailUrl": "https://cdn-bastani.stunning.kr/portfolio/1.jpg",
                     "likeCount": 1240, "viewCount": "12.3k"},
                    {"id": 897236, "title": "패키지 디자인", "url": "/i/897236",
                     "thumbnailUrl": "https://cdn-bastani.stunning.kr/portfolio/2.jpg",
                     "likeCount": 830, "viewCount": 4100},
                    {"id": 897237, "title": "UI 리디자인", "url": "/i/897237",
                     "thumbnailUrl": "https://cdn-bastani.stunning.kr/portfolio/3.jpg",
                     "likeCount": 502, "viewCount": 2200},
                ],
            },
        })
        source = ScrapeSource(
            name="노트폴리오",
            url="https://api.stunning.kr/api/v1/dantats/curation/-/item?curationType=PortfolioPick",
            base_url="https://notefolio.net",
            strategy="json",
            limit=8,
        )
        items = parse_scrape(payload, source)
        self.assertEqual(len(items), 3)

        top = items[0]
        self.assertEqual(top.title, "브랜드 리뉴얼 프로젝트")
        self.assertEqual(top.image_url, "https://cdn-bastani.stunning.kr/portfolio/1.jpg")
        # 상대 링크가 노트폴리오 주소로 이어져야 한다 (API 호스트가 아니라)
        self.assertEqual(top.url, "https://notefolio.net/i/897235")
        self.assertEqual(top.popularity, 1240)
        # 같은 페이지 URL 로 뭉쳐서 중복 제거에 잡아먹히면 안 된다
        self.assertEqual(len({i.url for i in items}), 3)

    def test_json_path_wrong_still_recovers_by_autodetect(self):
        payload = json.dumps({"data": {"pins": [
            {"title": "무드보드", "image_url": "https://i.pinimg.com/1.jpg"},
            {"title": "컬러칩", "image_url": "https://i.pinimg.com/2.jpg"},
            {"title": "타입", "image_url": "https://i.pinimg.com/3.jpg"},
        ]}})
        source = ScrapeSource(name="Pinterest", url="https://api.example/pins",
                              strategy="json", json_path="data.WRONG_KEY")
        items = parse_scrape(payload, source)
        self.assertEqual(len(items), 3)

    def test_duplicate_images_removed(self):
        page = """<html><body>
          <a href="/shots/1"><img src="https://cdn/x.jpg"></a>
          <a href="/shots/2"><img src="https://cdn/x.jpg"></a>
        </body></html>"""
        source = ScrapeSource(name="d", url="https://d", strategy="html", link_pattern="/shots/")
        self.assertEqual(len(parse_scrape(page, source)), 1)

    def test_empty_page_yields_nothing(self):
        source = ScrapeSource(name="d", url="https://d", strategy="html", link_pattern="/shots/")
        self.assertEqual(parse_scrape("<html><body></body></html>", source), [])


class ChallengeDetectionTests(unittest.TestCase):
    """붙긴 했는데 0장 나올 때, 봇 차단인지 구조 변경인지 구분해준다."""

    def test_detects_cloudflare_interstitial(self):
        from design_digest.cli import _detect_challenge

        page = "<html><head><title>Just a moment...</title></head><body></body></html>"
        self.assertEqual(_detect_challenge(page), "just a moment")

    def test_detects_javascript_requirement(self):
        from design_digest.cli import _detect_challenge

        self.assertTrue(_detect_challenge("<html>Please enable JavaScript to continue</html>"))

    def test_normal_page_is_not_flagged(self):
        from design_digest.cli import _detect_challenge

        self.assertEqual(_detect_challenge(CARD_GRID_PAGE), "")

    def test_blocked_page_yields_no_items(self):
        source = ScrapeSource(name="Dribbble", url="https://dribbble.com/shots/popular",
                              strategy="html", link_pattern="/shots/")
        page = "<html><head><title>Just a moment...</title></head><body>Checking your browser</body></html>"
        self.assertEqual(parse_scrape(page, source), [])


class ImageFeedTests(unittest.TestCase):
    def test_rsshub_feed_becomes_image_items(self):
        source = FeedSource(name="Instagram · somedesigner",
                            url="http://localhost:1200/instagram/user/somedesigner",
                            kind="image", weight=1.5)
        self.assertTrue(source.is_image_feed)

        items = to_image_items(parse_feed(RSSHUB_FEED, source), source)
        # 이미지가 없는 항목은 빠진다
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.title, "새 포스터 작업")
        self.assertEqual(item.image_url, "https://scontent.example.com/post1.jpg")
        self.assertEqual(item.url, "https://www.instagram.com/p/ABC123/")
        self.assertEqual(item.source, "Instagram · somedesigner")
        self.assertIsNotNone(item.published)


if __name__ == "__main__":
    unittest.main()
