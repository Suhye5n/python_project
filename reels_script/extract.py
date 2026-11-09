"""인스타 릴스 URL -> 대본(.txt) 추출기.

토큰 0 설계: 다운로드·음성인식을 전부 로컬에서 처리하고,
결과는 텍스트 파일로만 남긴다. LLM에는 최종 대본(필요할 때만)만 넘긴다.

사용법:
    python -m reels_script.extract URL [URL ...] [-m small] [-o reels_out]
"""
import argparse
import re
import sys
import tempfile
from pathlib import Path


def download_audio(url: str, workdir: Path, cookies: str | None) -> tuple[Path, dict]:
    import yt_dlp

    opts = {
        "format": "bestaudio/best",          # 영상 대신 오디오만 → 빠르고 가벼움
        "outtmpl": str(workdir / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }
    if cookies:
        opts["cookiefile"] = cookies         # 로그인 필요 시 브라우저에서 내보낸 cookies.txt
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info)), info


def transcribe(audio: Path, model, lang: str | None) -> str:
    segments, _ = model.transcribe(
        str(audio), language=lang, vad_filter=True, beam_size=1
    )
    lines = [s.text.strip() for s in segments if s.text.strip()]
    # 연속 중복 문장 제거(whisper 반복 환각 방지)
    out = [l for i, l in enumerate(lines) if i == 0 or l != lines[i - 1]]
    return "\n".join(out)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="인스타 릴스 대본 추출")
    p.add_argument("urls", nargs="+")
    p.add_argument("-m", "--model", default="small",
                   help="whisper 모델: tiny/base/small/medium/large-v3 (기본 small)")
    p.add_argument("-l", "--lang", default="ko", help="언어 코드, 자동감지는 'auto'")
    p.add_argument("-o", "--out", default="reels_out", help="출력 폴더")
    p.add_argument("--cookies", help="cookies.txt 경로 (비공개/로그인 필요 시)")
    p.add_argument("--caption", action="store_true", help="게시물 캡션도 함께 저장")
    a = p.parse_args(argv)

    from faster_whisper import WhisperModel

    model = WhisperModel(a.model, device="auto", compute_type="int8")
    lang = None if a.lang == "auto" else a.lang
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    fails = 0
    for url in a.urls:
        try:
            with tempfile.TemporaryDirectory() as td:
                audio, info = download_audio(url, Path(td), a.cookies)
                text = transcribe(audio, model, lang)
            vid = re.sub(r"[^\w-]", "_", info.get("id") or "reel")
            body = text
            if a.caption and info.get("description"):
                body = f"[캡션]\n{info['description']}\n\n[대본]\n{text}"
            path = out / f"{vid}.txt"
            path.write_text(body + "\n", encoding="utf-8")
            print(f"OK  {url} -> {path}")
        except Exception as e:  # 하나 실패해도 나머지 계속
            fails += 1
            print(f"ERR {url}: {e}", file=sys.stderr)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
