"""앱 설정.

우선순위는 `환경변수 > TOML 설정파일 > 기본값` 이다.
비밀값(SMTP 비밀번호 등)은 파일에 적지 말고 환경변수/GitHub Secrets로 넣는다.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
DEFAULT_SOURCES_PATH = PACKAGE_DIR / "sources.toml"
DEFAULT_CONFIG_PATH = PROJECT_DIR / "design_digest.toml"

USER_AGENT = (
    "design-digest/1.0 (daily design trend collector; "
    "+https://github.com/suhye5n/python_project)"
)


def _env_str(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _split_list(raw: str) -> list[str]:
    """쉼표/줄바꿈으로 구분된 문자열을 리스트로."""
    parts = [p.strip() for chunk in raw.splitlines() for p in chunk.split(",")]
    return [p for p in parts if p]


@dataclass
class MailConfig:
    host: str = "smtp.gmail.com"
    port: int = 587
    username: str = ""
    password: str = ""
    sender: str = ""
    recipients: list[str] = field(default_factory=list)
    use_starttls: bool = True
    use_ssl: bool = False
    subject_prefix: str = "[디자인 다이제스트]"

    @property
    def from_address(self) -> str:
        return self.sender or self.username

    @property
    def is_configured(self) -> bool:
        return bool(self.host and self.password and self.from_address and self.recipients)

    def missing_fields(self) -> list[str]:
        missing = []
        if not self.host:
            missing.append("SMTP_HOST")
        if not self.from_address:
            missing.append("SMTP_USER 또는 MAIL_SENDER")
        if not self.password:
            missing.append("SMTP_PASSWORD")
        if not self.recipients:
            missing.append("MAIL_TO")
        return missing


@dataclass
class Config:
    mail: MailConfig = field(default_factory=MailConfig)

    #: 리포트에 찍히는 기준 시간대
    timezone: str = "Asia/Seoul"
    #: 몇 시간 이내에 올라온 글/이미지를 "오늘치"로 볼지
    lookback_hours: int = 30
    #: 카테고리당 최대 글 수
    max_articles_per_category: int = 6
    #: 리포트에 담을 최대 이미지 수
    max_images: int = 12
    #: 같은 매체에서 한 번에 담을 최대 글 수 (한 곳이 도배하는 것 방지)
    max_per_source: int = 3
    #: 이미지 소스마다 최소 몇 장은 자리를 보장할지.
    #: 0 으로 두면 순수 점수순이 되어 인기 수치가 없는 소스는 잘 안 보인다.
    guaranteed_images_per_source: int = 1
    #: 이전에 이미 보고한 항목을 건너뛸지
    skip_seen: bool = True

    http_timeout: int = 20
    http_retries: int = 2
    max_workers: int = 8
    user_agent: str = USER_AGENT

    #: 이미지를 내려받아 메일에 인라인 첨부할지 (끄면 링크만)
    download_images: bool = True
    #: 이미지 한 장의 최대 크기
    max_image_bytes: int = 2 * 1024 * 1024
    #: 메일에 인라인으로 넣을 이미지 총량. 넘치는 이미지는 원격 링크로 떨어진다.
    #: (base64 인코딩으로 실제 메일은 1.4배쯤 커지므로 여유를 둔다)
    max_inline_total_bytes: int = 8 * 1024 * 1024

    data_dir: Path = PROJECT_DIR / "design_digest_data"
    sources_path: Path = DEFAULT_SOURCES_PATH

    @property
    def reports_dir(self) -> Path:
        return self.data_dir / "reports"

    @property
    def images_dir(self) -> Path:
        return self.data_dir / "images"

    @property
    def archive_dir(self) -> Path:
        return self.data_dir / "archive"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "digest.db"

    def ensure_dirs(self) -> None:
        for path in (self.data_dir, self.reports_dir, self.images_dir, self.archive_dir):
            path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 로딩
    # ------------------------------------------------------------------
    @classmethod
    def load(cls, config_path: Path | None = None) -> "Config":
        """TOML 파일(있으면)을 읽고 환경변수로 덮어써서 설정을 만든다."""
        config = cls()
        path = config_path or DEFAULT_CONFIG_PATH
        if path and Path(path).exists():
            config._apply_toml(tomllib.loads(Path(path).read_text(encoding="utf-8")))
        config._apply_env()
        return config

    def _apply_toml(self, data: dict[str, Any]) -> None:
        digest = data.get("digest", {})
        for key in (
            "timezone",
            "lookback_hours",
            "max_articles_per_category",
            "max_images",
            "max_per_source",
            "guaranteed_images_per_source",
            "skip_seen",
            "http_timeout",
            "http_retries",
            "max_workers",
            "user_agent",
            "download_images",
            "max_image_bytes",
            "max_inline_total_bytes",
        ):
            if key in digest:
                setattr(self, key, digest[key])
        if "data_dir" in digest:
            self.data_dir = Path(digest["data_dir"]).expanduser()
        if "sources_path" in digest:
            self.sources_path = Path(digest["sources_path"]).expanduser()

        mail = data.get("mail", {})
        for key in ("host", "port", "username", "sender", "use_starttls", "use_ssl", "subject_prefix"):
            if key in mail:
                setattr(self.mail, key, mail[key])
        if "recipients" in mail:
            value = mail["recipients"]
            self.mail.recipients = value if isinstance(value, list) else _split_list(str(value))

    def _apply_env(self) -> None:
        self.timezone = _env_str("DIGEST_TIMEZONE", self.timezone)
        self.lookback_hours = _env_int("DIGEST_LOOKBACK_HOURS", self.lookback_hours)
        self.max_articles_per_category = _env_int(
            "DIGEST_MAX_ARTICLES_PER_CATEGORY", self.max_articles_per_category
        )
        self.max_images = _env_int("DIGEST_MAX_IMAGES", self.max_images)
        self.max_per_source = _env_int("DIGEST_MAX_PER_SOURCE", self.max_per_source)
        self.guaranteed_images_per_source = _env_int(
            "DIGEST_GUARANTEED_IMAGES_PER_SOURCE", self.guaranteed_images_per_source
        )
        self.skip_seen = _env_bool("DIGEST_SKIP_SEEN", self.skip_seen)
        self.http_timeout = _env_int("DIGEST_HTTP_TIMEOUT", self.http_timeout)
        self.http_retries = _env_int("DIGEST_HTTP_RETRIES", self.http_retries)
        self.max_workers = _env_int("DIGEST_MAX_WORKERS", self.max_workers)
        self.download_images = _env_bool("DIGEST_DOWNLOAD_IMAGES", self.download_images)
        self.max_image_bytes = _env_int("DIGEST_MAX_IMAGE_BYTES", self.max_image_bytes)
        self.max_inline_total_bytes = _env_int(
            "DIGEST_MAX_INLINE_TOTAL_BYTES", self.max_inline_total_bytes
        )

        data_dir = os.environ.get("DIGEST_DATA_DIR")
        if data_dir:
            self.data_dir = Path(data_dir).expanduser()
        sources_path = os.environ.get("DIGEST_SOURCES_PATH")
        if sources_path:
            self.sources_path = Path(sources_path).expanduser()

        self.mail.host = _env_str("SMTP_HOST", self.mail.host)
        self.mail.port = _env_int("SMTP_PORT", self.mail.port)
        self.mail.username = _env_str("SMTP_USER", self.mail.username)
        self.mail.password = os.environ.get("SMTP_PASSWORD", self.mail.password)
        self.mail.sender = _env_str("MAIL_SENDER", self.mail.sender)
        self.mail.use_starttls = _env_bool("SMTP_STARTTLS", self.mail.use_starttls)
        self.mail.use_ssl = _env_bool("SMTP_SSL", self.mail.use_ssl)
        self.mail.subject_prefix = _env_str("MAIL_SUBJECT_PREFIX", self.mail.subject_prefix)
        recipients = os.environ.get("MAIL_TO")
        if recipients:
            self.mail.recipients = _split_list(recipients)
