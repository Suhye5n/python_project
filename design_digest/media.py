"""이미지 내려받기.

메일에 이미지를 인라인(CID)으로 넣으려면 파일이 로컬에 있어야 한다.
외부 링크로만 걸어두면 메일 클라이언트가 원격 이미지를 막아서 보통 안 보인다.
"""

from __future__ import annotations

import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .config import Config
from .models import ImageItem
from .net import FetchError, fetch_bytes

log = logging.getLogger(__name__)

CONTENT_TYPE_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/avif": ".avif",
}
KNOWN_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif")


def _filename(url: str, content_type: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    extension = CONTENT_TYPE_EXT.get(content_type.split(";")[0].strip().lower(), "")
    if not extension:
        lowered = url.lower()
        extension = next((ext for ext in KNOWN_EXTENSIONS if ext in lowered), ".jpg")
    return f"{digest}{extension}"


def download_image(item: ImageItem, target_dir: Path, config: Config) -> bool:
    """이미지 한 장을 받아 `item.local_path` 를 채운다. 성공하면 True."""
    url = item.image_url
    if not url.startswith("http"):
        return False

    try:
        body, headers = fetch_bytes(
            url,
            timeout=config.http_timeout,
            retries=1,
            user_agent=config.user_agent,
            accept="image/*",
            max_bytes=config.max_image_bytes,
        )
    except FetchError as exc:
        log.debug("이미지 실패 %s: %s", url, exc)
        return False

    content_type = headers.get("Content-Type", "")
    if content_type and not content_type.lower().startswith("image/"):
        log.debug("이미지가 아님(%s): %s", content_type, url)
        return False
    if len(body) < 1024:  # 깨진 파일/플레이스홀더
        return False

    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / _filename(url, content_type)
    path.write_bytes(body)
    item.local_path = str(path)
    return True


def download_all(items: list[ImageItem], target_dir: Path, config: Config) -> int:
    """여러 장을 동시에 받는다. 받은 개수를 돌려준다."""
    if not items:
        return 0
    workers = max(1, min(config.max_workers, len(items)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda item: download_image(item, target_dir, config), items))
    return sum(1 for ok in results if ok)
