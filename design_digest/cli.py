"""커맨드라인 인터페이스.

    python -m design_digest run        # 수집 + 리포트 저장 + 메일 발송
    python -m design_digest preview    # 수집 + 리포트 저장 (메일 안 보냄)
    python -m design_digest check      # 소스가 살아있는지 점검
    python -m design_digest sources    # 설정된 소스 목록
    python -m design_digest test-mail  # SMTP 설정 확인용 메일 1통
    python -m design_digest render --date 2026-07-26   # 아카이브 다시 렌더링
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

from .config import Config
from .mailer import MailError, send_digest, send_test_mail
from .models import CATEGORY_LABELS
from .pipeline import build_digest
from .render import render_text, save_report
from .sources import load_sources
from .sources.feeds import collect_feed, collect_image_feed
from .sources.hackernews import collect_stories
from .sources.reddit import collect_subreddit
from .sources.scrape import collect_scrape
from .storage import SeenStore, load_archive, save_archive

log = logging.getLogger("design_digest")


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )


def _config_from_args(args: argparse.Namespace) -> Config:
    config = Config.load(Path(args.config) if args.config else None)
    if getattr(args, "lookback", None):
        config.lookback_hours = args.lookback
    if getattr(args, "max_images", None) is not None:
        config.max_images = args.max_images
    if getattr(args, "no_image_download", False):
        config.download_images = False
    if getattr(args, "include_seen", False):
        config.skip_seen = False
    config.ensure_dirs()
    return config


def _print_summary(digest, report_path: Path | None = None) -> None:
    stats = digest.stats
    print()
    print(f"📅 {digest.date} 다이제스트")
    print(f"   글 {len(digest.articles)}편 · 이미지 {len(digest.images)}장 "
          f"(후보 {stats.get('candidates', 0)}건에서 선별, {stats.get('elapsed_sec', 0)}초)")
    for category, articles in digest.by_category().items():
        print(f"   - {CATEGORY_LABELS.get(category, category)}: {len(articles)}편")
    if digest.stats.get("downloaded_images"):
        print(f"   - 내려받은 이미지: {stats['downloaded_images']}장")
    if digest.failures:
        print(f"   ⚠️  못 읽은 소스 {len(digest.failures)}곳:")
        for name, reason in digest.failures[:8]:
            print(f"      · {name}: {reason[:90]}")
    if report_path:
        print(f"   📄 리포트: {report_path}")
    print()


# ------------------------------------------------------------------ 명령


def cmd_collect(args: argparse.Namespace, *, send: bool) -> int:
    config = _config_from_args(args)
    sources = load_sources(config.sources_path)
    log.info("소스 %d곳에서 수집 시작", len(sources))

    with SeenStore(config.db_path) as store:
        digest = build_digest(config, sources=sources, store=store)
        store.prune()

    report_path = save_report(digest, config.reports_dir, timezone=config.timezone)
    save_archive(digest, config.archive_dir)
    _print_summary(digest, report_path)

    if not send:
        return 0

    if digest.is_empty and not args.send_empty:
        log.info("내용이 없어 메일을 보내지 않았습니다 (--send-empty 로 강제 발송 가능)")
        return 0

    try:
        send_digest(digest, config)
    except MailError as exc:
        log.error("%s", exc)
        return 1
    print(f"✉️  {', '.join(config.mail.recipients)} 로 발송했습니다.")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """모든 소스에 실제로 붙어보고 결과를 표로 보여준다."""
    config = _config_from_args(args)
    sources = load_sources(config.sources_path)
    results: list[tuple[str, bool, str]] = []

    # 각 작업은 (건수, 설명) 을 돌려준다. 건수를 따로 받아야 0건을 실패로 판정할 수 있다.
    jobs: list[tuple[str, Callable[[], tuple[int, str]]]] = [
        (feed.name, lambda f=feed: (lambda n: (n, f"{n}개 항목"))(len(collect_feed(f, config))))
        for feed in sources.article_feeds
    ]
    jobs += [
        (feed.name, lambda f=feed: (lambda n: (n, f"이미지 {n}장"))(len(collect_image_feed(f, config))))
        for feed in sources.image_feeds
    ]
    jobs += [
        (sub.label, lambda s=sub: (lambda n: (n, f"이미지 {n}장"))(len(collect_subreddit(s, config))))
        for sub in sources.reddits
    ]
    jobs += [
        (
            scrape.name,
            lambda s=scrape: (lambda n: (n, f"이미지 {n}장 ({s.strategy})"))(
                len(collect_scrape(s, config))
            ),
        )
        for scrape in sources.scrapes
        if scrape.enabled
    ]
    if sources.hackernews.enabled:
        hn = sources.hackernews
        jobs.append(
            ("Hacker News", lambda: (lambda n: (n, f"{n}개 스토리"))(len(collect_stories(hn, config))))
        )

    with ThreadPoolExecutor(max_workers=config.max_workers) as pool:
        futures = {pool.submit(job): name for name, job in jobs}
        for future in as_completed(futures):
            name = futures[future]
            try:
                count, note = future.result()
                # 붙긴 했는데 0건이면 주소나 셀렉터가 어긋난 것이다.
                if count == 0:
                    note += "  ← 접속은 되는데 아무것도 못 뽑았습니다"
                results.append((name, count > 0, note))
            except Exception as exc:
                results.append((name, False, str(exc)[:160]))

    results.sort(key=lambda row: (row[1], row[0]))
    ok_count = sum(1 for _, ok, _ in results if ok)
    print()
    for name, ok, note in results:
        mark = "✅" if ok else "❌"
        print(f" {mark} {name:<32} {note}")
    print(f"\n 정상 {ok_count} / 전체 {len(results)}")
    if ok_count < len(results):
        print(" 실패한 스크랩 소스는 `debug --source 이름` 으로 구조를 확인하세요.\n")
    else:
        print()
    return 0 if ok_count else 1


def cmd_debug(args: argparse.Namespace) -> int:
    """스크랩 소스가 실제로 무엇을 내려주는지 들여다본다.

    사이트가 개편돼서 0장이 나올 때, 어떤 전략/경로로 고쳐야 하는지
    바로 보이도록 응답을 요약해서 보여준다.
    """
    config = _config_from_args(args)
    sources = load_sources(config.sources_path)
    target = next((s for s in sources.scrapes if s.name == args.source), None)
    if target is None:
        names = ", ".join(s.name for s in sources.scrapes) or "(없음)"
        log.error("그런 스크랩 소스가 없습니다: %s (있는 것: %s)", args.source, names)
        return 1

    import json

    from .net import FetchError, fetch_text
    from .sources.scrape import (
        HTML_ACCEPT,
        autodetect_items,
        extract_embedded_json,
        extract_meta,
        find_image,
        parse_scrape,
    )
    from .util import strip_html

    print(f"\n▸ {target.name} — {target.url}\n  전략: {target.strategy}")
    try:
        text = fetch_text(
            target.url,
            timeout=config.http_timeout,
            retries=config.http_retries,
            user_agent=config.user_agent,
            accept=HTML_ACCEPT,
            max_bytes=12 * 1024 * 1024,
        )
    except FetchError as exc:
        # 여기서 죽으면 원인을 못 보므로, 서버가 뭐라고 했는지 그대로 보여준다.
        print(f"\n  ❌ 요청 자체가 실패했습니다.\n     {exc}\n")
        return 1
    print(f"  응답 크기: {len(text):,}자")

    challenge = _detect_challenge(text)
    if challenge:
        print(f"  ⚠️  봇 차단 페이지로 보입니다 ({challenge}).")
        print("      이 소스는 클라우드 IP 에서 못 읽습니다. 로컬 실행을 쓰세요.")

    # 응답이 JSON 이면 (API 를 직접 부르는 경우) 그대로 구조를 본다.
    payload = None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        pass

    if payload is not None:
        print("  응답 형식: JSON")
        if isinstance(payload, dict):
            print(f"  최상위 키: {', '.join(sorted(payload)[:12])}")
        found = autodetect_items(payload)
        print(f"  자동탐색 항목: {len(found)}개")
        if found:
            print(f"  항목 키: {', '.join(sorted(found[0])[:14])}")
            print(f"  첫 항목 이미지 후보: {find_image(found[0]) or '(못 찾음)'}")
    else:
        meta = extract_meta(text)
        print(f"  og:image: {meta.image or '(없음)'}")
        print(f"  og:title: {meta.headline or '(없음)'}")
        print(f"  <a> 태그 수: {text.count('<a ')} · <img> 태그 수: {text.count('<img')}")
        if target.link_pattern:
            print(f"  '{target.link_pattern}' 가 들어간 링크: {text.count(target.link_pattern)}개")

        blobs = extract_embedded_json(text, target.marker)
        print(f"  script 안 JSON 덩어리: {len(blobs)}개")
        for index, blob in enumerate(blobs[:3]):
            found = autodetect_items(blob)
            keys = sorted(found[0].keys())[:12] if found else []
            print(f"    [{index}] 자동탐색 항목 {len(found)}개 · 키: {', '.join(keys) or '(없음)'}")

    items = parse_scrape(text, target)
    print(f"\n  현재 설정으로 뽑힌 이미지: {len(items)}장")
    for item in items[:5]:
        print(f"    · {item.title[:50]}")
        print(f"      {item.image_url[:100]}")

    if not items:
        # 무엇을 받았는지 눈으로 확인할 수 있게 앞부분을 보여준다.
        preview = " ".join(strip_html(text[:4000]).split())[:600]
        print(f"\n  받은 내용 앞부분:\n    {preview or '(텍스트 없음)'}")

    if args.save:
        path = config.data_dir / f"debug-{target.name}.html"
        path.write_text(text, encoding="utf-8")
        print(f"\n  원본 저장: {path}")
    print()
    return 0 if items else 1


#: 봇 차단/자바스크립트 요구 페이지에서 흔히 나오는 문구
_CHALLENGE_HINTS = (
    "just a moment",
    "cf-browser-verification",
    "cf_chl",
    "enable javascript",
    "checking your browser",
    "captcha",
    "access denied",
    "are you a robot",
)


def _detect_challenge(text: str) -> str:
    lowered = text[:6000].lower()
    for hint in _CHALLENGE_HINTS:
        if hint in lowered:
            return hint
    return ""


def cmd_sources(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    sources = load_sources(config.sources_path)
    print(f"\n설정 파일: {config.sources_path}\n")
    print(f"[글 소스 {len(sources.feeds)}곳]")
    for feed in sources.feeds:
        label = CATEGORY_LABELS.get(feed.category, feed.category)
        print(f"  · {feed.name:<28} {label:<16} weight={feed.weight}")
    image_feeds = sources.image_feeds
    print(f"\n[이미지 소스 {len(sources.reddits) + len(image_feeds) + len(sources.scrapes)}곳]")
    for sub in sources.reddits:
        print(f"  · {sub.label:<28} 최소 {sub.min_score}점 · weight={sub.weight}")
    for feed in image_feeds:
        print(f"  · {feed.name:<28} 이미지 피드 · weight={feed.weight}")
    for scrape in sources.scrapes:
        state = "" if scrape.enabled else " (꺼짐)"
        print(f"  · {scrape.name:<28} 스크랩({scrape.strategy}) · weight={scrape.weight}{state}")
    hn = sources.hackernews
    print(f"\n[인기 신호] Hacker News {'사용' if hn.enabled else '미사용'} "
          f"· 검색어 {', '.join(hn.queries)} · {hn.min_points}점 이상\n")
    return 0


def cmd_test_mail(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    try:
        send_test_mail(config)
    except MailError as exc:
        log.error("%s", exc)
        return 1
    print(f"✉️  테스트 메일을 {', '.join(config.mail.recipients)} 로 보냈습니다.")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    """저장해 둔 아카이브 JSON 을 다시 HTML 로."""
    config = _config_from_args(args)
    date = args.date or dt.date.today().isoformat()
    path = config.archive_dir / f"{date}.json"
    if not path.exists():
        log.error("아카이브가 없습니다: %s", path)
        return 1

    digest = load_archive(path)
    if args.text:
        print(render_text(digest, config.timezone))
        return 0
    report_path = save_report(digest, config.reports_dir, timezone=config.timezone)
    print(f"📄 {report_path}")
    return 0


# ------------------------------------------------------------------ 파서


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="design_digest",
        description="매일 한 번 디자인 트렌드·방법론·철학 글과 인기 디자인 이미지를 모아 보고합니다.",
    )
    parser.add_argument("-c", "--config", help="설정 TOML 경로")
    parser.add_argument("-v", "--verbose", action="store_true", help="디버그 로그")

    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_collect_options(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--lookback", type=int, help="몇 시간 이내 글까지 볼지 (기본 30)")
        sub.add_argument("--max-images", type=int, help="이미지 최대 장수")
        sub.add_argument("--no-image-download", action="store_true",
                         help="이미지를 내려받지 않고 링크만 사용")
        sub.add_argument("--include-seen", action="store_true",
                         help="이미 보고했던 항목도 포함")

    run_parser = subparsers.add_parser("run", help="수집하고 메일로 보고")
    add_collect_options(run_parser)
    run_parser.add_argument("--send-empty", action="store_true",
                            help="수집 결과가 없어도 메일 보내기")

    preview_parser = subparsers.add_parser("preview", help="수집해서 리포트만 저장 (발송 안 함)")
    add_collect_options(preview_parser)

    subparsers.add_parser("check", help="소스가 살아있는지 점검")
    subparsers.add_parser("sources", help="설정된 소스 목록 보기")
    subparsers.add_parser("test-mail", help="SMTP 설정 확인용 메일 발송")

    debug_parser = subparsers.add_parser("debug", help="스크랩 소스의 응답 구조 들여다보기")
    debug_parser.add_argument("--source", required=True, help="스크랩 소스 이름 (예: Behance)")
    debug_parser.add_argument("--save", action="store_true", help="받은 원본을 파일로 저장")

    render_parser = subparsers.add_parser("render", help="아카이브를 다시 렌더링")
    render_parser.add_argument("--date", help="YYYY-MM-DD (기본: 오늘)")
    render_parser.add_argument("--text", action="store_true", help="텍스트로 출력")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    handlers = {
        "run": lambda a: cmd_collect(a, send=True),
        "preview": lambda a: cmd_collect(a, send=False),
        "check": cmd_check,
        "sources": cmd_sources,
        "test-mail": cmd_test_mail,
        "render": cmd_render,
        "debug": cmd_debug,
    }
    try:
        return handlers[args.command](args)
    except KeyboardInterrupt:
        print("\n중단했습니다.", file=sys.stderr)
        return 130
