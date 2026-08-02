"""표준 라이브러리만으로 만든 HTTP 클라이언트.

`requests` 같은 외부 패키지 없이 돌아가야 어디서든(특히 GitHub Actions에서
설치 단계 없이) 바로 실행할 수 있다. gzip/deflate 해제, 재시도, 응답 크기
제한 정도만 챙긴다.
"""

from __future__ import annotations

import gzip
import json
import logging
import time
import urllib.error
import urllib.request
import zlib
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 20
# 이 상태코드는 같은 요청을 반복해도 결과가 달라지지 않으므로 바로 포기한다.
NO_RETRY_STATUSES = {400, 401, 403, 404, 405, 410, 451}
# 다만 이 코드들은 '이 요청은 못 받겠다'는 뜻이라, 헤더를 바꾸면 통과하는 경우가 있다.
# 실제로 요즘IT 는 405, CSS-Tricks 는 415 를 돌려줬는데 둘 다 정상 서비스 중이었다.
# 방화벽이 브라우저가 아닌 요청을 걸러낸 것이다.
HEADER_RETRY_STATUSES = {403, 405, 406, 415, 429}
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
BROWSER_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"


class FetchError(RuntimeError):
    """네트워크 요청이 최종적으로 실패했을 때."""


def _error_snippet(exc: urllib.error.HTTPError) -> str:
    """오류 응답 본문 앞부분.

    API 는 대개 왜 거절했는지를 본문에 적어준다
    (`{"message":"cursor is required"}` 같은 것). 상태코드만 보면 알 수 없다.
    """
    try:
        body = exc.read(400)
    except Exception:
        return ""
    text = body.decode("utf-8", errors="replace").strip()
    return " ".join(text.split())[:200]


def _decompress(raw: bytes, encoding: str) -> bytes:
    encoding = (encoding or "").lower()
    try:
        if encoding == "gzip":
            return gzip.decompress(raw)
        if encoding == "deflate":
            try:
                return zlib.decompress(raw)
            except zlib.error:
                return zlib.decompress(raw, -zlib.MAX_WBITS)
    except (OSError, zlib.error):
        # 압축 헤더만 붙어 있고 실제로는 평문인 서버도 있다.
        return raw
    return raw


def fetch_bytes(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = 2,
    user_agent: str = "design-digest/1.0",
    headers: dict[str, str] | None = None,
    accept: str = "*/*",
    max_bytes: int | None = None,
    data: bytes | None = None,
    allow_browser_retry: bool = True,
) -> tuple[bytes, dict[str, str]]:
    """URL을 받아 (본문 bytes, 응답 헤더) 를 돌려준다.

    실패하면 지수 백오프로 `retries` 번까지 재시도하고, 그래도 안 되면
    `FetchError` 를 던진다. 방화벽이 헤더를 보고 막은 것 같으면 브라우저처럼
    보이는 헤더로 한 번 더 시도한다.
    """
    request_headers = {
        "User-Agent": user_agent,
        "Accept": accept,
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en,ko;q=0.8",
    }
    if headers:
        request_headers.update(headers)

    last_error: Exception | None = None
    last_detail = ""
    browser_retry_done = False
    attempt = 0
    while attempt <= retries:
        request = urllib.request.Request(url, headers=request_headers, data=data)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if max_bytes:
                    # 상한을 1바이트 넘겨 읽어서 잘렸는지 판별한다.
                    raw = response.read(max_bytes + 1)
                    if len(raw) > max_bytes:
                        raise FetchError(f"응답이 너무 큼(>{max_bytes}B): {url}")
                else:
                    raw = response.read()
                body = _decompress(raw, response.headers.get("Content-Encoding", ""))
                return body, dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            last_error = exc
            last_detail = _error_snippet(exc) or last_detail
            # 헤더 때문에 막힌 것으로 보이면 브라우저 흉내로 딱 한 번 더.
            if (
                allow_browser_retry
                and not browser_retry_done
                and exc.code in HEADER_RETRY_STATUSES
                and request_headers["User-Agent"] != BROWSER_USER_AGENT
            ):
                browser_retry_done = True
                request_headers["User-Agent"] = BROWSER_USER_AGENT
                request_headers["Accept"] = BROWSER_ACCEPT
                log.debug("%s: %s 응답, 브라우저 헤더로 재시도", url, exc.code)
                continue
            if exc.code in NO_RETRY_STATUSES:
                break
        except FetchError:
            raise
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            last_error = exc

        if attempt < retries:
            delay = 2**attempt
            log.debug("요청 실패(%s), %s초 뒤 재시도: %s", last_error, delay, url)
            time.sleep(delay)
        attempt += 1

    # 이유를 앞에 둔다. URL 이 길면 로그에서 정작 원인이 잘려나간다.
    message = f"{last_error}"
    if last_detail:
        message += f" | 응답: {last_detail}"
    raise FetchError(f"{message} — {url}")


def fetch_text(url: str, **kwargs: Any) -> str:
    body, headers = fetch_bytes(url, **kwargs)
    charset = "utf-8"
    content_type = headers.get("Content-Type", "")
    if "charset=" in content_type:
        charset = content_type.split("charset=", 1)[1].split(";")[0].strip().strip('"') or "utf-8"
    try:
        return body.decode(charset, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def fetch_json(url: str, **kwargs: Any) -> Any:
    kwargs.setdefault("accept", "application/json")
    text = fetch_text(url, **kwargs)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise FetchError(f"{url} JSON 파싱 실패: {exc}") from exc
