"""수집 이력 저장소.

매일 도는 앱이라 같은 글/이미지를 며칠씩 다시 보고하면 금방 질린다.
한 번 보고한 항목의 URL을 SQLite에 남겨 두고 다음 날 걸러낸다.
다이제스트 전체는 JSON으로도 아카이브해 두어 나중에 다시 렌더링할 수 있다.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import sqlite3
from pathlib import Path
from typing import Iterable, Sequence, TypeVar

from .models import Digest
from .util import normalize_url, utc_now

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS seen (
    key        TEXT PRIMARY KEY,
    url        TEXT NOT NULL,
    kind       TEXT NOT NULL,
    title      TEXT,
    first_seen TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_seen_first_seen ON seen (first_seen);
"""

# .url 속성을 가진 항목이면 무엇이든 받는다 (Article / ImageItem).
ItemT = TypeVar("ItemT")


def url_key(url: str) -> str:
    return hashlib.sha1(normalize_url(url).encode("utf-8")).hexdigest()


class SeenStore:
    """이미 보고한 URL 기록."""

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def __enter__(self) -> "SeenStore":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()

    def is_seen(self, url: str) -> bool:
        row = self._conn.execute("SELECT 1 FROM seen WHERE key = ?", (url_key(url),)).fetchone()
        return row is not None

    def filter_new(self, items: Sequence[ItemT]) -> list[ItemT]:
        """아직 보고한 적 없는 항목만 남긴다 (이번 목록 안의 중복도 제거)."""
        if not items:
            return []
        keys = {url_key(getattr(item, "url", "")) for item in items}
        placeholders = ",".join("?" * len(keys))
        rows = self._conn.execute(
            f"SELECT key FROM seen WHERE key IN ({placeholders})", tuple(keys)
        ).fetchall()
        known = {row[0] for row in rows}

        fresh: list[ItemT] = []
        for item in items:
            key = url_key(getattr(item, "url", ""))
            if not key or key in known:
                continue
            known.add(key)  # 같은 실행 안에서의 중복도 막는다
            fresh.append(item)
        return fresh

    def mark_seen(self, items: Iterable[ItemT], kind: str) -> int:
        now = utc_now().isoformat()
        rows = []
        for item in items:
            url = getattr(item, "url", "")
            if not url:
                continue
            rows.append((url_key(url), url, kind, getattr(item, "title", "")[:300], now))
        if not rows:
            return 0
        self._conn.executemany(
            "INSERT OR IGNORE INTO seen (key, url, kind, title, first_seen) VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        self._conn.commit()
        return len(rows)

    def prune(self, keep_days: int = 180) -> int:
        """오래된 기록 정리. 그쯤 지난 글은 다시 떠도 새 글이나 마찬가지다."""
        cutoff = (utc_now() - dt.timedelta(days=keep_days)).isoformat()
        cursor = self._conn.execute("DELETE FROM seen WHERE first_seen < ?", (cutoff,))
        self._conn.commit()
        return cursor.rowcount

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM seen").fetchone()[0]


def save_archive(digest: Digest, archive_dir: Path) -> Path:
    """다이제스트를 JSON으로 저장하고 경로를 돌려준다."""
    archive_dir.mkdir(parents=True, exist_ok=True)
    path = archive_dir / f"{digest.date.isoformat()}.json"
    path.write_text(
        json.dumps(digest.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def load_archive(path: Path) -> Digest:
    return Digest.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
