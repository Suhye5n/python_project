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
# 이 상태코드는 재시도해도 결과가 달라지지 않으므로 바로 포기한다.
NO_RETRY_STATUSES = {400, 401, 403, 404, 405, 410, 451}


class FetchError(RuntimeError):
    """네트워크 요청이 최종적으로 실패했을 때."""


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
) -> tuple[bytes, dict[str, str]]:
    """URL을 받아 (본문 bytes, 응답 헤더) 를 돌려준다.

    실패하면 지수 백오프로 `retries` 번까지 재시도하고, 그래도 안 되면
    `FetchError` 를 던진다.
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
    for attempt in range(retries + 1):
        request = urllib.request.Request(url, headers=request_headers)
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

    raise FetchError(f"{url} 요청 실패: {last_error}")


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
