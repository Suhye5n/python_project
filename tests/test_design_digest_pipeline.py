"""분류·랭킹·저장·렌더링·파이프라인 테스트 (전부 오프라인)."""

from __future__ import annotations

import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from design_digest import classify, rank
from design_digest.config import Config
from design_digest.models import (
    CATEGORY_GENERAL,
    CATEGORY_METHODOLOGY,
    CATEGORY_PHILOSOPHY,
    CATEGORY_TREND,
    Article,
    Digest,
    ImageItem,
)
from design_digest.pipeline import build_digest, dedupe_articles, enrich_with_popularity
from design_digest.render import render_html, render_text, save_report, subject_line
from design_digest.sources import FeedSource, HackerNewsSource, RedditSource, SourceSet
from design_digest.storage import SeenStore, load_archive, save_archive

NOW = dt.datetime(2026, 7, 26, 9, 0, tzinfo=dt.timezone.utc)

# 테스트용 1x1 PNG
PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000a49444154789c6300010000050001" "0d0a2db4" "0000000049454e44ae426082"
)


def make_article(**kwargs) -> Article:
    defaults = dict(
        title="Untitled",
        url="https://example.com/a",
        source="Test",
        published=NOW - dt.timedelta(hours=2),
    )
    defaults.update(kwargs)
    return Article(**defaults)


class ClassifyTests(unittest.TestCase):
    def test_detects_methodology_from_title(self):
        article = make_article(title="A practical guide to design system tokens and usability testing")
        self.assertEqual(classify.classify(article), CATEGORY_METHODOLOGY)

    def test_detects_trend(self):
        article = make_article(title="2026 컬러 트렌드: 브루탈리즘의 귀환")
        self.assertEqual(classify.classify(article), CATEGORY_TREND)

    def test_detects_philosophy(self):
        article = make_article(
            title="The ethics of craft",
            summary="An essay on why design carries responsibility and meaning.",
        )
        self.assertEqual(classify.classify(article), CATEGORY_PHILOSOPHY)

    def test_falls_back_to_source_category(self):
        article = make_article(title="Studio visit: Amsterdam", category=CATEGORY_TREND)
        self.assertEqual(classify.classify(article), CATEGORY_TREND)

    def test_no_signal_stays_general(self):
        article = make_article(title="Untitled 42", category=CATEGORY_GENERAL)
        self.assertEqual(classify.classify(article), CATEGORY_GENERAL)

    def test_apply_fills_keywords(self):
        articles = [make_article(title="Design thinking과 접근성 체크리스트")]
        classify.apply(articles)
        self.assertEqual(articles[0].category, CATEGORY_METHODOLOGY)
        self.assertTrue(articles[0].keywords)


class RankTests(unittest.TestCase):
    def test_popular_and_fresh_ranks_higher(self):
        old_quiet = make_article(title="a", url="https://e.com/1", published=NOW - dt.timedelta(hours=28))
        fresh_hot = make_article(
            title="b", url="https://e.com/2", published=NOW - dt.timedelta(minutes=30), popularity=300
        )
        ranked = rank.rank_articles([old_quiet, fresh_hot], now=NOW)
        self.assertEqual(ranked[0].url, "https://e.com/2")
        self.assertGreater(ranked[0].score, ranked[1].score)

    def test_source_weight_applies(self):
        base = make_article(title="a", url="https://e.com/1", source="Plain")
        boosted = make_article(title="a", url="https://e.com/2", source="Trusted")
        ranked = rank.rank_articles([base, boosted], weights={"Trusted": 2.0}, now=NOW)
        self.assertEqual(ranked[0].source, "Trusted")

    def test_select_respects_per_category_and_per_source_caps(self):
        articles = [
            make_article(title=f"t{i}", url=f"https://e.com/{i}", source="Same", category=CATEGORY_TREND)
            for i in range(10)
        ]
        ranked = rank.rank_articles(articles, now=NOW)
        picked = rank.select_articles(ranked, per_category=5, per_source=2)
        self.assertEqual(len(picked), 2)

    def test_select_images_limits_per_source(self):
        images = [
            ImageItem(title=f"i{i}", url=f"https://e.com/{i}", image_url=f"https://cdn/{i}.jpg",
                      source="r/Design", popularity=100 + i, published=NOW)
            for i in range(8)
        ]
        ranked = rank.rank_images(images, now=NOW)
        picked = rank.select_images(ranked, limit=10, per_source=3)
        self.assertEqual(len(picked), 3)

    def test_image_source_weight_orders_comparable_items(self):
        plain = ImageItem(title="a", url="u1", image_url="i1", source="r/Design",
                          popularity=100, published=NOW)
        favored = ImageItem(title="b", url="u2", image_url="i2", source="Behance",
                            popularity=100, published=NOW)
        ranked = rank.rank_images([plain, favored], weights={"Behance": 1.5}, now=NOW)
        self.assertEqual(ranked[0].source, "Behance")

    def test_curated_sources_get_a_guaranteed_slot(self):
        """업보트 수천 개짜리 레딧이 자리를 다 먹어도 보고 싶은 곳은 들어가야 한다."""
        crowd = [
            ImageItem(title=f"레딧 {i}", url=f"u{i}", image_url=f"i{i}", source="r/Design",
                      popularity=5000 + i, published=NOW)
            for i in range(10)
        ]
        curated = [
            ImageItem(title="노트폴리오 작업", url="n1", image_url="ni", source="노트폴리오",
                      published=NOW),
            ImageItem(title="인스타 포스트", url="g1", image_url="gi", source="Instagram",
                      published=NOW),
        ]
        ranked = rank.rank_images(crowd + curated, now=NOW)

        # 매체 상한이 넉넉해도 자리 보장이 있으면 세 소스가 모두 들어온다.
        picked = rank.select_images(ranked, limit=4, per_source=4, guarantee=1)
        self.assertEqual({item.source for item in picked}, {"r/Design", "노트폴리오", "Instagram"})

        # 보장을 끄면 인기 순수 경쟁이 되어 레딧이 자리를 다 가져간다.
        without = rank.select_images(ranked, limit=4, per_source=4, guarantee=0)
        self.assertEqual({item.source for item in without}, {"r/Design"})

    def test_selected_images_stay_sorted_by_score(self):
        items = [
            ImageItem(title="a", url="u1", image_url="i1", source="A", popularity=10, published=NOW),
            ImageItem(title="b", url="u2", image_url="i2", source="B", popularity=900, published=NOW),
        ]
        ranked = rank.rank_images(items, now=NOW)
        picked = rank.select_images(ranked, limit=5, guarantee=1)
        self.assertEqual([i.score for i in picked], sorted((i.score for i in picked), reverse=True))

    def test_comments_boost_image_score(self):
        quiet = ImageItem(title="a", url="u1", image_url="i1", source="s", popularity=500, published=NOW)
        talked = ImageItem(title="b", url="u2", image_url="i2", source="s", popularity=500,
                           comments=400, published=NOW)
        self.assertGreater(rank.score_image(talked, now=NOW), rank.score_image(quiet, now=NOW))


class DedupeTests(unittest.TestCase):
    def test_dedupe_keeps_most_popular_and_merges_image(self):
        plain = make_article(url="https://example.com/x", image_url="https://cdn/x.jpg")
        popular = make_article(url="https://www.example.com/x/?utm_source=hn", popularity=120)
        merged = dedupe_articles([plain, popular])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].popularity, 120)
        self.assertEqual(merged[0].image_url, "https://cdn/x.jpg")

    def test_enrich_with_popularity_matches_normalized_urls(self):
        article = make_article(url="https://example.com/post/")
        story = make_article(url="http://www.example.com/post", popularity=88,
                             popularity_note="HN 88점 · 댓글 4개")
        matched = enrich_with_popularity([article], [story])
        self.assertEqual(matched, 1)
        self.assertEqual(article.popularity, 88)
        self.assertIn("HN 88점", article.popularity_note)


class SeenStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = SeenStore(Path(self.tmp.name) / "seen.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_filter_new_excludes_marked_urls(self):
        first = make_article(url="https://example.com/1")
        second = make_article(url="https://example.com/2")
        self.assertEqual(len(self.store.filter_new([first, second])), 2)

        self.store.mark_seen([first], "article")
        remaining = self.store.filter_new([first, second])
        self.assertEqual([a.url for a in remaining], ["https://example.com/2"])

    def test_filter_new_drops_duplicates_within_batch(self):
        items = [make_article(url="https://example.com/x"),
                 make_article(url="https://example.com/x/?utm_source=a")]
        self.assertEqual(len(self.store.filter_new(items)), 1)

    def test_images_sharing_a_page_url_are_kept_apart(self):
        """갤러리 페이지 하나에 걸린 여러 작업물이 한 장으로 뭉치면 안 된다."""
        items = [
            ImageItem(title="작업 1", url="https://site/gallery", image_url="https://cdn/1.jpg",
                      source="s"),
            ImageItem(title="작업 2", url="https://site/gallery", image_url="https://cdn/2.jpg",
                      source="s"),
        ]
        self.assertEqual(len(self.store.filter_new(items)), 2)

        self.store.mark_seen(items[:1], "image")
        remaining = self.store.filter_new(items)
        self.assertEqual([i.title for i in remaining], ["작업 2"])

    def test_prune_removes_old_rows(self):
        self.store.mark_seen([make_article(url="https://example.com/old")], "article")
        self.assertEqual(self.store.count(), 1)
        self.assertEqual(self.store.prune(keep_days=0), 1)
        self.assertEqual(self.store.count(), 0)


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.digest = Digest(
            date=dt.date(2026, 7, 26),
            generated_at=NOW,
            articles=[
                make_article(title="디자인 시스템 운영기", url="https://example.com/ds",
                             category=CATEGORY_METHODOLOGY, summary="요약입니다.",
                             popularity=120, popularity_note="HN 120점", keywords=["design system"]),
                make_article(title="<script>alert(1)</script>", url="https://example.com/xss",
                             category=CATEGORY_TREND),
            ],
            images=[ImageItem(title="포스터", url="https://reddit.com/p", image_url="https://cdn/p.jpg",
                              source="r/Design", popularity=900, popularity_note="업보트 900")],
            failures=[("Dead Feed", "404")],
            stats={"collected_articles": 40, "elapsed_sec": 3.2, "sources_total": 20},
        )

    def test_html_contains_sections_and_escapes_titles(self):
        html = render_html(self.digest)
        self.assertIn("디자인 시스템 운영기", html)
        self.assertIn("디자인 방법론", html)
        self.assertIn("오늘 사람들이 많이 본 디자인", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("Dead Feed", html)

    def test_html_uses_remote_url_when_no_local_file(self):
        self.assertIn("https://cdn/p.jpg", render_html(self.digest))

    def test_cid_mode_used_only_for_downloaded_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.png"
            path.write_bytes(PNG_BYTES)
            self.digest.images[0].local_path = str(path)
            html = render_html(self.digest, mode="cid")
            self.assertIn("cid:digest-image-0", html)

    def test_empty_digest_renders_notice(self):
        empty = Digest(date=dt.date(2026, 7, 26), generated_at=NOW)
        self.assertIn("찾지 못했어요", render_html(empty))

    def test_text_version_lists_urls(self):
        text = render_text(self.digest)
        self.assertIn("https://example.com/ds", text)
        self.assertIn("[디자인 방법론]", text)

    def test_subject_line_has_counts(self):
        subject = subject_line(self.digest, "[디자인 다이제스트]")
        self.assertIn("07월 26일", subject)
        self.assertIn("글 2편", subject)

    def test_save_report_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = save_report(self.digest, Path(tmp))
            self.assertTrue(path.exists())
            self.assertEqual(path.name, "2026-07-26.html")


class ArchiveTests(unittest.TestCase):
    def test_round_trip(self):
        digest = Digest(
            date=dt.date(2026, 7, 26),
            generated_at=NOW,
            articles=[make_article(title="t", keywords=["ux"], popularity=3)],
            images=[ImageItem(title="i", url="u", image_url="iu", source="s", published=NOW)],
            failures=[("x", "boom")],
            stats={"a": 1},
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = save_archive(digest, Path(tmp))
            restored = load_archive(path)
        self.assertEqual(restored.date, digest.date)
        self.assertEqual(restored.articles[0].title, "t")
        self.assertEqual(restored.articles[0].published, digest.articles[0].published)
        self.assertEqual(restored.images[0].image_url, "iu")
        self.assertEqual(restored.failures, [("x", "boom")])


class PipelineTests(unittest.TestCase):
    """수집기를 가짜로 바꿔치기해서 조립 로직만 검증한다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = Config()
        self.config.data_dir = Path(self.tmp.name)
        self.config.download_images = False
        self.config.ensure_dirs()
        self.sources = SourceSet(
            feeds=[FeedSource(name="Feed A", url="https://a/feed", category=CATEGORY_TREND, weight=1.0)],
            reddits=[RedditSource(subreddit="Design", min_score=10)],
            hackernews=HackerNewsSource(enabled=True),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, feed_articles, hn_stories=(), images=(), store=None, sources=None,
             feed_images=(), scraped=()):
        with mock.patch("design_digest.pipeline.collect_feed", return_value=list(feed_articles)), \
             mock.patch("design_digest.pipeline.collect_stories", return_value=list(hn_stories)), \
             mock.patch("design_digest.pipeline.collect_subreddit", return_value=list(images)), \
             mock.patch("design_digest.pipeline.collect_image_feed", return_value=list(feed_images)), \
             mock.patch("design_digest.pipeline.collect_scrape", return_value=list(scraped)):
            return build_digest(self.config, sources=sources or self.sources, store=store, now=NOW)

    def test_image_feeds_and_scrapers_join_the_image_section(self):
        from design_digest.sources import ScrapeSource

        sources = SourceSet(
            feeds=[
                FeedSource(name="Feed A", url="https://a/feed", category=CATEGORY_TREND),
                FeedSource(name="Instagram", url="http://localhost:1200/instagram/x",
                           kind="image", weight=3.0),
            ],
            reddits=[RedditSource(subreddit="Design", min_score=10)],
            scrapes=[ScrapeSource(name="노트폴리오", url="https://notefolio.net/discover",
                                  weight=3.0)],
            hackernews=HackerNewsSource(enabled=False),
        )
        digest = self._run(
            [],
            images=[ImageItem(title="레딧 인기글", url="https://r/1", image_url="https://cdn/r.jpg",
                              source="r/Design", popularity=5000, published=NOW)],
            feed_images=[ImageItem(title="인스타 포스트", url="https://ig/1",
                                   image_url="https://cdn/ig.jpg", source="Instagram",
                                   published=NOW)],
            scraped=[ImageItem(title="노트폴리오 작업", url="https://nf/1",
                               image_url="https://cdn/nf.jpg", source="노트폴리오",
                               published=NOW)],
            sources=sources,
        )
        self.assertEqual(
            {i.source for i in digest.images}, {"r/Design", "Instagram", "노트폴리오"}
        )

    def test_image_feed_is_not_collected_as_article(self):
        sources = SourceSet(
            feeds=[FeedSource(name="Instagram", url="http://localhost:1200/instagram/x",
                              kind="image")],
            hackernews=HackerNewsSource(enabled=False),
        )
        digest = self._run(
            [make_article(title="이건 글로 오면 안 됨", url="https://a/1")],
            feed_images=[ImageItem(title="포스트", url="https://ig/1",
                                   image_url="https://cdn/ig.jpg", source="Instagram",
                                   published=NOW)],
            sources=sources,
        )
        self.assertEqual(digest.articles, [])
        self.assertEqual(len(digest.images), 1)

    def test_builds_digest_and_sorts_by_popularity(self):
        digest = self._run(
            [
                make_article(title="조용한 글", url="https://a/1"),
                make_article(title="화제의 글", url="https://a/2"),
            ],
            hn_stories=[make_article(title="화제의 글", url="https://a/2", popularity=250,
                                     popularity_note="HN 250점")],
        )
        self.assertEqual(len(digest.articles), 2)
        self.assertEqual(digest.articles[0].title, "화제의 글")
        self.assertEqual(digest.articles[0].popularity, 250)
        self.assertEqual(digest.stats["selected_articles"], 2)

    def test_drops_articles_outside_lookback_window(self):
        digest = self._run([
            make_article(title="어제 글", url="https://a/1", published=NOW - dt.timedelta(hours=2)),
            make_article(title="옛날 글", url="https://a/2", published=NOW - dt.timedelta(days=5)),
        ])
        self.assertEqual([a.title for a in digest.articles], ["어제 글"])

    def test_keeps_undated_articles(self):
        digest = self._run([make_article(title="날짜 없음", url="https://a/1", published=None)])
        self.assertEqual(len(digest.articles), 1)

    def test_seen_items_are_skipped_next_run(self):
        store = SeenStore(self.config.db_path)
        articles = [make_article(title="한 번만", url="https://a/1")]
        first = self._run(articles, store=store)
        self.assertEqual(len(first.articles), 1)

        second = self._run([make_article(title="한 번만", url="https://a/1")], store=store)
        self.assertEqual(second.articles, [])
        store.close()

    def test_popular_article_image_joins_image_section(self):
        digest = self._run(
            [make_article(title="표지 있는 글", url="https://a/1", image_url="https://cdn/a.jpg",
                          popularity=90)],
            images=[ImageItem(title="레딧", url="https://r/1", image_url="https://cdn/r.jpg",
                              source="r/Design", popularity=800, published=NOW)],
        )
        image_urls = {item.image_url for item in digest.images}
        self.assertEqual(image_urls, {"https://cdn/a.jpg", "https://cdn/r.jpg"})
        # 업보트가 훨씬 높은 레딧 이미지가 앞에 온다.
        self.assertEqual(digest.images[0].image_url, "https://cdn/r.jpg")

    def test_source_failure_is_recorded_not_raised(self):
        from design_digest.net import FetchError

        with mock.patch("design_digest.pipeline.collect_feed", side_effect=FetchError("timeout")), \
             mock.patch("design_digest.pipeline.collect_stories", return_value=[]), \
             mock.patch("design_digest.pipeline.collect_subreddit", return_value=[]):
            digest = build_digest(self.config, sources=self.sources, now=NOW)

        self.assertEqual(digest.failures[0][0], "Feed A")
        self.assertIn("timeout", digest.failures[0][1])
        self.assertTrue(digest.is_empty)


class MailerTests(unittest.TestCase):
    def test_build_message_has_text_html_and_inline_image(self):
        from design_digest.mailer import build_message

        config = Config()
        config.mail.username = "me@example.com"
        config.mail.password = "secret"
        config.mail.recipients = ["me@example.com"]

        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "p.png"
            image_path.write_bytes(PNG_BYTES)
            digest = Digest(
                date=dt.date(2026, 7, 26),
                generated_at=NOW,
                articles=[make_article(title="글", url="https://example.com/1")],
                images=[ImageItem(title="이미지", url="https://r/1", image_url="https://cdn/p.jpg",
                                  source="r/Design", popularity=100, local_path=str(image_path))],
            )
            message = build_message(digest, config)

        self.assertIn("디자인 다이제스트", message["Subject"])
        self.assertEqual(message["To"], "me@example.com")
        types = {part.get_content_type() for part in message.walk()}
        self.assertIn("text/plain", types)
        self.assertIn("text/html", types)
        self.assertIn("image/png", types)

    def test_inline_budget_falls_back_to_remote_links(self):
        from design_digest.mailer import fit_inline_budget

        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for name in ("a.png", "b.png"):
                path = Path(tmp) / name
                path.write_bytes(PNG_BYTES * 200)  # 한 장에 약 14KB
                paths.append(path)
            digest = Digest(
                date=dt.date(2026, 7, 26),
                generated_at=NOW,
                images=[
                    ImageItem(title=str(i), url=f"u{i}", image_url=f"https://cdn/{i}.png",
                              source="s", local_path=str(path))
                    for i, path in enumerate(paths)
                ],
            )
            trimmed = fit_inline_budget(digest, budget=paths[0].stat().st_size)

        # 첫 장만 인라인, 두 번째는 원격 링크로
        self.assertTrue(trimmed.images[0].local_path)
        self.assertEqual(trimmed.images[1].local_path, "")
        # 원본 다이제스트는 그대로여야 한다
        self.assertTrue(digest.images[1].local_path)

    def test_send_refuses_without_settings(self):
        from design_digest.mailer import MailError, send_test_mail

        config = Config()
        config.mail.password = ""
        config.mail.recipients = []
        with self.assertRaises(MailError):
            send_test_mail(config)


if __name__ == "__main__":
    unittest.main()
