"""SMTP 발송.

`multipart/alternative` (텍스트 + HTML) 안에 `multipart/related` 로 이미지를
인라인 첨부한다. Gmail 은 2단계 인증 계정이면 '앱 비밀번호'가 필요하다.
"""

from __future__ import annotations

import dataclasses
import logging
import mimetypes
import smtplib
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path

from .config import Config, MailConfig
from .models import Digest
from .render import inline_attachments, render_html, render_text, subject_line

log = logging.getLogger(__name__)

SENDER_NAME = "디자인 다이제스트"


class MailError(RuntimeError):
    """메일을 만들거나 보내지 못했을 때."""


def _attach_images(message: EmailMessage, digest: Digest) -> int:
    """HTML 파트에 이미지를 related 로 붙인다."""
    pairs = inline_attachments(digest)
    if not pairs:
        return 0

    html_part = message.get_payload()[-1]
    attached = 0
    for cid, path in pairs:
        mime_type, _ = mimetypes.guess_type(str(path))
        maintype, _, subtype = (mime_type or "image/jpeg").partition("/")
        try:
            data = Path(path).read_bytes()
        except OSError as exc:
            log.warning("첨부 실패 %s: %s", path, exc)
            continue
        html_part.add_related(
            data,
            maintype=maintype,
            subtype=subtype or "jpeg",
            cid=f"<{cid}>",
            filename=Path(path).name,
        )
        attached += 1
    return attached


def fit_inline_budget(digest: Digest, budget: int) -> Digest:
    """인라인 첨부 총량을 예산 안으로 맞춘다.

    이미지는 점수 순으로 정렬돼 있으니 앞에서부터 채우고, 예산을 넘는 이미지는
    로컬 경로를 비워 원격 링크로 렌더링되게 한다. (원본은 건드리지 않는다)
    """
    total = 0
    images = []
    for item in digest.images:
        size = 0
        if item.local_path:
            path = Path(item.local_path)
            size = path.stat().st_size if path.exists() else 0
        if size and total + size <= budget:
            total += size
            images.append(item)
        else:
            if size:
                log.debug("인라인 예산 초과로 링크 처리: %s", item.image_url)
            images.append(dataclasses.replace(item, local_path=""))
    return dataclasses.replace(digest, images=images)


def build_message(digest: Digest, config: Config) -> EmailMessage:
    """발송할 메일 객체를 만든다."""
    mail = config.mail
    digest = fit_inline_budget(digest, config.max_inline_total_bytes)
    message = EmailMessage()
    message["Subject"] = subject_line(digest, mail.subject_prefix)
    message["From"] = formataddr((SENDER_NAME, mail.from_address))
    message["To"] = ", ".join(mail.recipients)
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain="design-digest.local")

    # 이미지를 인라인으로 넣을 수 있으면 cid, 아니면 원격 URL 로 떨어뜨린다.
    mode = "cid" if any(item.local_path for item in digest.images) else "remote"
    message.set_content(render_text(digest, config.timezone))
    message.add_alternative(
        render_html(digest, timezone=config.timezone, mode=mode), subtype="html"
    )
    if mode == "cid":
        _attach_images(message, digest)
    return message


def send_message(message: EmailMessage, mail: MailConfig) -> None:
    """SMTP 로 실제 발송."""
    missing = mail.missing_fields()
    if missing:
        raise MailError("메일 설정이 비어 있습니다: " + ", ".join(missing))

    try:
        if mail.use_ssl:
            server: smtplib.SMTP = smtplib.SMTP_SSL(mail.host, mail.port, timeout=30)
        else:
            server = smtplib.SMTP(mail.host, mail.port, timeout=30)
        with server:
            server.ehlo()
            if mail.use_starttls and not mail.use_ssl:
                server.starttls()
                server.ehlo()
            if mail.username:
                server.login(mail.username, mail.password)
            server.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise MailError(f"메일 발송 실패: {exc}") from exc

    log.info("메일 발송 완료 -> %s", ", ".join(mail.recipients))


def send_digest(digest: Digest, config: Config) -> None:
    send_message(build_message(digest, config), config.mail)


def send_test_mail(config: Config) -> None:
    """설정이 제대로 됐는지 확인용 짧은 메일."""
    mail = config.mail
    missing = mail.missing_fields()
    if missing:
        raise MailError("메일 설정이 비어 있습니다: " + ", ".join(missing))

    message = EmailMessage()
    message["Subject"] = f"{mail.subject_prefix} 발송 테스트"
    message["From"] = formataddr((SENDER_NAME, mail.from_address))
    message["To"] = ", ".join(mail.recipients)
    message["Date"] = formatdate(localtime=True)
    message.set_content(
        "이 메일이 보이면 SMTP 설정이 정상입니다.\n"
        "이제 `python -m design_digest run` 이 매일 리포트를 보낼 수 있어요."
    )
    send_message(message, mail)
