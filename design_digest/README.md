# design_digest — 매일 아침 오는 디자인 브리핑

디자인 트렌드 · 방법론 · 철학에 관한 **글**과, 사람들이 많이 보고 많이 언급한 **디자인 이미지**를
하루 한 번 모아 HTML 메일로 보내주는 앱입니다.

- 파이썬 **3.11 표준 라이브러리만** 사용합니다. `pip install` 할 것이 없습니다.
- 매일 실행은 GitHub Actions 워크플로가 담당합니다 (`.github/workflows/design-digest.yml`).
- 한 번 보고한 글은 다시 보내지 않습니다.

---

## 1. 빠른 시작

```bash
# 소스 목록 확인
python -m design_digest sources

# 소스가 살아있는지 점검 (죽은 피드 찾기)
python -m design_digest check

# 수집해서 HTML 리포트만 만들기 (메일 안 보냄)
python -m design_digest preview
#   -> design_digest_data/reports/2026-07-26.html

# 수집 + 메일 발송
python -m design_digest run
```

`preview` 로 만든 HTML을 브라우저에서 열어보고, 마음에 들면 메일 설정을 넣고 `run` 하면 됩니다.

## 2. 메일 설정

비밀값은 파일이 아니라 **환경변수**로 넣습니다.

| 환경변수 | 설명 | 예시 |
| --- | --- | --- |
| `SMTP_HOST` | SMTP 서버 | `smtp.gmail.com` |
| `SMTP_PORT` | 포트 | `587` |
| `SMTP_USER` | 계정 | `sy1599@gmail.com` |
| `SMTP_PASSWORD` | 비밀번호 (Gmail은 **앱 비밀번호**) | `abcd efgh ijkl mnop` |
| `MAIL_TO` | 받는 사람 (쉼표로 여러 명) | `sy1599@gmail.com` |

Gmail을 쓴다면 계정 비밀번호가 아니라 앱 비밀번호가 필요합니다.
[Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호](https://myaccount.google.com/apppasswords)에서
16자리를 발급받아 `SMTP_PASSWORD` 에 넣으세요.

설정이 맞는지 먼저 확인:

```bash
export SMTP_USER=sy1599@gmail.com SMTP_PASSWORD='앱비밀번호' MAIL_TO=sy1599@gmail.com
python -m design_digest test-mail
```

## 3. 매일 자동 실행 (GitHub Actions)

저장소 **Settings → Secrets and variables → Actions** 에 다음 Secret을 등록합니다.

```
SMTP_HOST      smtp.gmail.com
SMTP_PORT      587
SMTP_USER      본인 Gmail 주소
SMTP_PASSWORD  앱 비밀번호 16자리
MAIL_TO        받을 주소
```

등록하면 `.github/workflows/design-digest.yml` 이 **매일 한국시간 07:00**(UTC 22:00)에 돌면서
메일을 보냅니다. Actions 탭에서 `Run workflow` 로 수동 실행도 됩니다.

시간을 바꾸려면 워크플로의 cron을 고치세요. cron은 UTC 기준이라 **원하는 KST 시각 − 9시간**입니다.

```yaml
- cron: "0 22 * * *"   # KST 07:00
- cron: "0 0 * * *"    # KST 09:00
```

수집 이력(SQLite)은 `actions/cache` 로 실행 간에 보존됩니다. 캐시가 만료돼 초기화되면
하루치 정도 예전 글이 다시 올 수 있는데, 큰 문제는 아닙니다.

## 4. 무엇을 어떻게 모으나

### 글

`sources.toml` 에 적힌 RSS/Atom 피드 22곳을 병렬로 읽습니다. Dezeen, NN/g, Smashing Magazine,
A List Apart, Design Observer, AIGA Eye on Design, 요즘IT 등 트렌드 · 방법론 · 철학이 고루 섞여 있습니다.

수집한 글은 제목/본문 키워드로 세 갈래로 분류합니다.

| 카테고리 | 신호가 되는 말 |
| --- | --- |
| 📈 최신 디자인 트렌드 | trend, rebrand, palette, 브루탈리즘, 리브랜딩, 2026 … |
| 🧭 디자인 방법론 | design system, usability, research, 프로세스, 접근성, 체크리스트 … |
| 🌱 디자인 철학 · 관점 | philosophy, ethics, craft, 본질, 태도, 비평 … |

키워드가 약하면 그 매체의 기본 성격(`sources.toml` 의 `category`)을 따릅니다.

### 이미지

- **Reddit** 디자인 서브레딧 8곳의 그날 상위 게시물 — 업보트/댓글 수가 곧 인기의 근거입니다.
- **오늘 많이 언급된 글의 대표 이미지** — Hacker News에서 점수를 많이 받은 글의 히어로 이미지.

이미지는 내려받아 메일에 **인라인 첨부(cid)** 합니다. 원격 링크로만 걸면 메일 앱이 이미지를 막아
빈칸으로 보이기 때문입니다. 총 8MB를 넘으면 넘치는 이미지는 링크로 대체합니다.

### 순위

`인기도(로그 스케일) + 신선도 + 매체 가중치` 로 점수를 매기고, 한 매체가 리포트를 독차지하지
않도록 매체당 3편까지만 뽑습니다.

## 5. 소스 추가/삭제

`design_digest/sources.toml` 만 고치면 됩니다. 코드는 건드릴 필요 없습니다.

```toml
[[feed]]
name = "새로운 매체"
url = "https://example.com/feed/"
category = "methodology"   # trend | methodology | philosophy
weight = 1.2               # 높을수록 위로 (기본 1.0)

[[reddit]]
subreddit = "logodesign"
min_score = 100            # 이 점수 미만은 무시
```

고친 뒤 `python -m design_digest check` 로 실제로 읽히는지 확인하세요.
피드 주소가 바뀌거나 서비스가 문을 닫으면 여기서 ❌ 로 표시됩니다.
소스 한 곳이 죽어도 그날 리포트는 정상 발송되고, 메일 하단에 "오늘 못 읽은 소스"로 적힙니다.

## 6. 세부 설정

프로젝트 루트에 `design_digest.toml` 을 두면 읽습니다 (`design_digest.example.toml` 참고).
환경변수가 항상 우선합니다.

| 설정 | 환경변수 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `lookback_hours` | `DIGEST_LOOKBACK_HOURS` | 30 | 몇 시간 이내 글까지 볼지 |
| `max_articles_per_category` | `DIGEST_MAX_ARTICLES_PER_CATEGORY` | 6 | 카테고리당 글 수 |
| `max_images` | `DIGEST_MAX_IMAGES` | 12 | 이미지 장수 |
| `max_per_source` | `DIGEST_MAX_PER_SOURCE` | 3 | 한 매체당 최대 글 수 |
| `download_images` | `DIGEST_DOWNLOAD_IMAGES` | true | 끄면 링크만 사용 |
| `timezone` | `DIGEST_TIMEZONE` | Asia/Seoul | 리포트 기준 시간대 |

## 7. 명령어

| 명령 | 하는 일 |
| --- | --- |
| `run` | 수집 → 리포트 저장 → 메일 발송 |
| `preview` | 수집 → 리포트 저장 (발송 안 함) |
| `check` | 모든 소스에 붙어보고 정상/실패 표시 |
| `sources` | 설정된 소스 목록 |
| `test-mail` | SMTP 설정 확인용 메일 1통 |
| `render --date 2026-07-26` | 저장된 아카이브를 다시 HTML로 |

공통 옵션: `--lookback 48`, `--max-images 20`, `--include-seen`, `--no-image-download`, `-v`

## 8. 구조

```
design_digest/
├── cli.py          명령어 처리
├── pipeline.py     수집 → 분류 → 랭킹 → 다이제스트 조립
├── sources/
│   ├── feeds.py       RSS/Atom 파서 (직접 구현)
│   ├── reddit.py      인기 이미지
│   └── hackernews.py  인기·언급량 신호
├── classify.py     트렌드/방법론/철학 분류
├── rank.py         점수 계산과 선별
├── render.py       HTML·텍스트 리포트
├── mailer.py       SMTP 발송
├── storage.py      중복 방지 SQLite + JSON 아카이브
├── media.py        이미지 다운로드
├── net.py          HTTP (표준 라이브러리)
└── sources.toml    소스 목록
```

산출물은 `design_digest_data/` 아래에 쌓입니다 (`reports/`, `images/`, `archive/`, `digest.db`).

## 9. 테스트

```bash
python -m unittest discover -s tests -t . -v
```

54개 테스트 모두 네트워크를 타지 않습니다. 파서·분류·랭킹·중복제거·렌더링·메일 조립을
고정된 픽스처로 검증합니다.

## 10. 알아둘 점

- **소스 가용성**: `sources.toml` 의 피드 주소는 공개 RSS 기준으로 적어둔 것이라, 매체가 주소를
  바꿨다면 `check` 에서 ❌ 가 납니다. 그때 URL만 고치면 됩니다.
- **Reddit**: 로그인 없는 공개 JSON을 쓰기 때문에 가끔 429(요청 제한)가 날 수 있습니다.
  그날 이미지 수집만 건너뛰고 글 리포트는 정상 발송됩니다.
- **요약**: 피드가 주는 본문 앞부분을 발췌하는 방식입니다. LLM 요약이 필요하면 `pipeline.py` 의
  분류 단계 뒤에 붙이면 됩니다.
