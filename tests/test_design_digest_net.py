"""네트워크 계층과 회복 동작 테스트.

실제 실행 로그에서 나온 실패들을 그대로 재현한다.
로컬 HTTP 서버를 띄워서 검증하므로 외부 네트워크는 쓰지 않는다.
"""

from __future__ import annotations

import http.server
import json
import threading
import unittest

from design_digest.config import Config
from design_digest.net import BROWSER_USER_AGENT, FetchError, fetch_bytes, fetch_json, fetch_text
from design_digest.sources import FeedSource, RedditSource
from design_digest.sources.feeds import FeedError, _strip_preamble, parse_feed
from design_digest.sources import reddit as reddit_module

VALID_RSS = (
    b'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
    b"<title>T</title><item><title>A</title><link>https://e.com/a</link></item>"
    b"</channel></rss>"
)


class _Handler(http.server.BaseHTTPRequestHandler):
    """요청 헤더에 따라 다르게 답하는 테스트 서버."""

    requests: list[tuple[str, str, str]] = []  # (path, method, user-agent)

    def log_message(self, *args):  # 조용히
        pass

    def _respond(self, status: int, body: bytes = b"", content_type: str = "application/xml"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        agent = self.headers.get("User-Agent", "")
        _Handler.requests.append((self.path, "GET", agent))

        if self.path == "/ok":
            return self._respond(200, VALID_RSS)

        # 요즘IT(405) / CSS-Tricks(415) 재현: 브라우저 UA 일 때만 통과시킨다.
        if self.path in ("/waf-405", "/waf-415"):
            if agent == BROWSER_USER_AGENT:
                return self._respond(200, VALID_RSS)
            return self._respond(405 if self.path == "/waf-405" else 415)

        if self.path == "/blocked":  # 무엇을 해도 막히는 경우 (레딧 403)
            return self._respond(403)

        # API 가 거절 사유를 본문에 적어주는 경우
        if self.path.startswith("/api-rejects"):
            body = json.dumps({"message": "cursor parameter is required"}).encode()
            return self._respond(400, body, "application/json")

        if self.path.startswith("/oauth/"):
            if self.headers.get("Authorization", "").startswith("Bearer test-token"):
                payload = {"data": {"children": [{"data": {
                    "title": "인증으로 받은 게시물", "permalink": "/r/Design/comments/x/",
                    "url_overridden_by_dest": "https://i.redd.it/x.jpg",
                    "post_hint": "image", "score": 500, "num_comments": 10,
                }}]}}
                return self._respond(200, json.dumps(payload).encode(), "application/json")
            return self._respond(403)

        return self._respond(404)

    def do_POST(self):
        _Handler.requests.append((self.path, "POST", self.headers.get("User-Agent", "")))
        if self.path == "/token":
            if not self.headers.get("Authorization", "").startswith("Basic "):
                return self._respond(401)
            body = json.dumps({"access_token": "test-token", "expires_in": 3600}).encode()
            return self._respond(200, body, "application/json")
        return self._respond(404)


class ServerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.port = cls.server.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        _Handler.requests.clear()
        self.config = Config()
        self.config.http_retries = 0


class BrowserRetryTests(ServerTestCase):
    def test_405_is_retried_with_browser_headers(self):
        """요즘IT 가 405 를 돌려주던 경우."""
        body, _ = fetch_bytes(f"{self.base}/waf-405", retries=0)
        self.assertIn(b"<rss", body)
        agents = [agent for _, _, agent in _Handler.requests]
        self.assertEqual(len(agents), 2)
        self.assertEqual(agents[1], BROWSER_USER_AGENT)

    def test_415_is_retried_with_browser_headers(self):
        """CSS-Tricks 가 415 를 돌려주던 경우."""
        body, _ = fetch_bytes(f"{self.base}/waf-415", retries=0)
        self.assertIn(b"<rss", body)

    def test_browser_retry_happens_only_once(self):
        with self.assertRaises(FetchError):
            fetch_bytes(f"{self.base}/blocked", retries=0)
        # 원래 요청 + 브라우저 재시도 = 2회. 무한히 반복하지 않는다.
        self.assertEqual(len(_Handler.requests), 2)

    def test_browser_retry_can_be_disabled(self):
        with self.assertRaises(FetchError):
            fetch_bytes(f"{self.base}/blocked", retries=0, allow_browser_retry=False)
        self.assertEqual(len(_Handler.requests), 1)

    def test_404_is_not_retried(self):
        with self.assertRaises(FetchError):
            fetch_bytes(f"{self.base}/missing", retries=2)
        self.assertEqual(len(_Handler.requests), 1)

    def test_error_body_is_included_in_message(self):
        """API 가 왜 거절했는지는 상태코드가 아니라 본문에 적혀 있다."""
        long_url = f"{self.base}/api-rejects?" + "&".join(f"p{i}=value{i}" for i in range(20))
        with self.assertRaises(FetchError) as caught:
            fetch_bytes(long_url, retries=0)
        message = str(caught.exception)
        self.assertIn("cursor parameter is required", message)
        # 이유가 URL 앞에 와야 로그에서 잘려도 원인이 보인다.
        self.assertLess(message.index("400"), message.index("api-rejects"))

    def test_normal_response_makes_one_request(self):
        text = fetch_text(f"{self.base}/ok")
        self.assertIn("<rss", text)
        self.assertEqual(len(_Handler.requests), 1)


class RedditAuthTests(ServerTestCase):
    def setUp(self):
        super().setUp()
        reddit_module._token_cache = None
        self._saved = (
            reddit_module.TOKEN_URL,
            reddit_module.OAUTH_TEMPLATE,
            reddit_module.API_TEMPLATE,
        )
        reddit_module.TOKEN_URL = f"{self.base}/token"
        reddit_module.OAUTH_TEMPLATE = self.base + "/oauth/{subreddit}?limit={limit}"
        reddit_module.API_TEMPLATE = self.base + "/blocked?sub={subreddit}&limit={limit}"

    def tearDown(self):
        (
            reddit_module.TOKEN_URL,
            reddit_module.OAUTH_TEMPLATE,
            reddit_module.API_TEMPLATE,
        ) = self._saved
        reddit_module._token_cache = None
        for key in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"):
            import os

            os.environ.pop(key, None)

    def _set_credentials(self):
        import os

        os.environ["REDDIT_CLIENT_ID"] = "id"
        os.environ["REDDIT_CLIENT_SECRET"] = "secret"

    def test_uses_oauth_when_credentials_present(self):
        self._set_credentials()
        items = reddit_module.collect_subreddit(RedditSource(subreddit="Design", min_score=10),
                                                self.config)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "인증으로 받은 게시물")
        paths = [path for path, method, _ in _Handler.requests if method == "POST"]
        self.assertEqual(paths, ["/token"])

    def test_token_is_reused_across_subreddits(self):
        self._set_credentials()
        source = RedditSource(subreddit="Design", min_score=10)
        reddit_module.collect_subreddit(source, self.config)
        reddit_module.collect_subreddit(source, self.config)
        token_calls = [p for p, method, _ in _Handler.requests if method == "POST"]
        self.assertEqual(len(token_calls), 1)

    def test_falls_back_to_public_endpoint_without_credentials(self):
        # 자격증명이 없으면 토큰을 받지 않고 공개 주소로 간다 (여기선 403 이라 실패)
        with self.assertRaises(FetchError):
            reddit_module.collect_subreddit(RedditSource(subreddit="Design"), self.config)
        self.assertFalse([p for p, method, _ in _Handler.requests if method == "POST"])

    def test_access_token_returns_empty_without_credentials(self):
        self.assertEqual(reddit_module.access_token(self.config), "")


class XmlPreambleTests(unittest.TestCase):
    """Dezeen 이 'XML declaration not at start of entity' 로 죽던 경우."""

    def setUp(self):
        self.source = FeedSource(name="Dezeen", url="https://www.dezeen.com/feed/")

    def test_leading_whitespace_is_tolerated(self):
        payload = b"\n\n  " + VALID_RSS
        articles = parse_feed(payload, self.source)
        self.assertEqual(len(articles), 1)

    def test_utf8_bom_is_stripped(self):
        articles = parse_feed(b"\xef\xbb\xbf" + VALID_RSS, self.source)
        self.assertEqual(len(articles), 1)

    def test_junk_before_declaration_is_dropped(self):
        payload = b"<!-- cached -->\n" + VALID_RSS
        # 주석이 앞에 오는 것은 XML 로도 유효하므로 그대로 파싱된다
        self.assertEqual(len(parse_feed(payload, self.source)), 1)

    def test_php_warning_before_declaration(self):
        payload = b"Warning: something in /var/www/feed.php on line 3\n" + VALID_RSS
        self.assertEqual(len(parse_feed(payload, self.source)), 1)

    def test_str_input_also_cleaned(self):
        self.assertEqual(len(parse_feed("﻿\n" + VALID_RSS.decode(), self.source)), 1)

    def test_strip_preamble_leaves_clean_payload_untouched(self):
        self.assertEqual(_strip_preamble(VALID_RSS), VALID_RSS)

    def test_still_raises_on_real_garbage(self):
        with self.assertRaises(FeedError):
            parse_feed(b"totally not xml at all", self.source)


if __name__ == "__main__":
    unittest.main()
