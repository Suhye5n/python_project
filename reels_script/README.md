# reels_script — 인스타 릴스 대본 추출 (토큰 0)

URL만 주면 **로컬에서** 오디오 다운로드(yt-dlp) → 음성인식(faster-whisper) → `.txt` 저장.
영상·오디오는 LLM에 절대 안 들어가므로 토큰이 들지 않는다.

## 설치
```bash
pip install -r reels_script/requirements.txt
```
ffmpeg 필요 (`brew install ffmpeg` / `apt install ffmpeg`).

## 사용
```bash
python -m reels_script.extract "https://www.instagram.com/reel/XXXX/"
```
여러 개 한 번에 / 캡션 포함 / 모델 변경:
```bash
python -m reels_script.extract URL1 URL2 --caption -m medium
```
결과: `reels_out/<릴스ID>.txt`

| 옵션 | 설명 |
|---|---|
| `-m` | `tiny`(빠름) ~ `large-v3`(정확). 한국어는 `small`~`medium` 권장 |
| `-l` | 언어, 기본 `ko`, 자동감지는 `auto` |
| `--cookies` | 로그인 필요할 때 브라우저에서 내보낸 cookies.txt |
| `--caption` | 게시물 설명글도 함께 저장 |

## Claude와 같이 쓸 때 토큰 아끼는 법
- Claude에게 "릴스 대본 뽑아줘"라고 시키지 말고, 위 명령을 직접 실행 → 필요한 `.txt`만 붙여넣기.
- 요약·수정이 필요할 때만 대본 텍스트를 넘긴다 (30초 릴스 ≈ 100~300 토큰).
