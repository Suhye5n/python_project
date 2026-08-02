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
| `REDDIT_CLIENT_ID` | (선택) Reddit 앱 id — §3-1 | |
| `REDDIT_CLIENT_SECRET` | (선택) Reddit 앱 secret | |

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
메일을 보냅니다. Actions 탭에서 `Run workflow` 로 수동 실행도 되고, 이때 모드를 고를 수 있습니다
(`run` 발송 / `preview` 리포트만 / `check` 소스 점검 / `sources` 목록). 로컬에 파이썬을 깔지
않아도 여기서 전부 확인할 수 있습니다.

> ⚠️ **예약 실행은 기본 브랜치(master)에서만 동작합니다.** GitHub 규칙이라, 작업 브랜치에
> 워크플로가 있어도 매일 자동으로 돌지 않습니다. PR을 머지해야 스케줄이 살아납니다.

시간을 바꾸려면 워크플로의 cron을 고치세요. cron은 UTC 기준이라 **원하는 KST 시각 − 9시간**입니다.

```yaml
- cron: "0 22 * * *"   # KST 07:00
- cron: "0 0 * * *"    # KST 09:00
```

수집 이력(SQLite)은 `actions/cache` 로 실행 간에 보존됩니다. 캐시가 만료돼 초기화되면
하루치 정도 예전 글이 다시 올 수 있는데, 큰 문제는 아닙니다.

## 3-1. Reddit 인증 (Actions에서 돌린다면 사실상 필수)

Reddit은 **데이터센터 IP에서 오는 공개 `.json` 요청을 막습니다.** GitHub Actions 러너가 정확히
여기 해당해서, 인증 없이 돌리면 서브레딧 8곳이 전부 `403 Blocked`로 실패합니다.
(내 컴퓨터에서 돌릴 때는 대체로 그냥 됩니다.)

앱을 등록하면 정식 API로 붙습니다. 2분 걸립니다.

1. https://www.reddit.com/prefs/apps → 맨 아래 **create another app...**
2. 이름 아무거나, 타입은 **script** 선택, redirect uri는 `http://localhost:8080`
3. 만들고 나면 앱 이름 아래 짧은 문자열이 **client id**, `secret` 항목이 **client secret**

이 둘을 Secrets에 추가합니다.

| Name | Secret |
| --- | --- |
| `REDDIT_CLIENT_ID` | 앱 이름 아래 문자열 |
| `REDDIT_CLIENT_SECRET` | secret 값 |

넣으면 `oauth.reddit.com`으로, 없으면 기존 공개 주소로 자동 폴백합니다. 코드 수정은 없습니다.

## 4. 무엇을 어떻게 모으나

### 글

`sources.toml` 에 적힌 RSS/Atom 피드 20곳을 병렬로 읽습니다. Dezeen, NN/g, Smashing Magazine,
A List Apart, Design Observer, 요즘IT 등 트렌드 · 방법론 · 철학이 고루 섞여 있습니다.

수집한 글은 제목/본문 키워드로 세 갈래로 분류합니다.

| 카테고리 | 신호가 되는 말 |
| --- | --- |
| 📈 최신 디자인 트렌드 | trend, rebrand, palette, 브루탈리즘, 리브랜딩, 2026 … |
| 🧭 디자인 방법론 | design system, usability, research, 프로세스, 접근성, 체크리스트 … |
| 🌱 디자인 철학 · 관점 | philosophy, ethics, craft, 본질, 태도, 비평 … |

키워드가 약하면 그 매체의 기본 성격(`sources.toml` 의 `category`)을 따릅니다.

### 이미지

네 갈래에서 모읍니다.

| 갈래 | 어디 | 인기 근거 |
| --- | --- | --- |
| 공개 JSON | Reddit 디자인 서브레딧 8곳 | 업보트·댓글 수 |
| 스크랩 | Behance, Dribbble, 노트폴리오, 월간디자인 | 좋아요 수(있으면) |
| 이미지 피드 | Instagram, Pinterest (RSSHub 경유) | 없음 — 자리 보장으로 노출 |
| 글에서 추출 | 오늘 많이 언급된 글의 대표 이미지 | HN 점수 |

이미지는 내려받아 메일에 **인라인 첨부(cid)** 합니다. 원격 링크로만 걸면 메일 앱이 이미지를 막아
빈칸으로 보이기 때문입니다. 총 8MB를 넘으면 넘치는 이미지는 링크로 대체합니다.

### 순위

글은 `인기도(로그 스케일) + 신선도 + 매체 가중치` 로 점수를 매기고, 한 매체가 리포트를
독차지하지 않도록 매체당 3편까지만 뽑습니다.

이미지는 여기에 **자리 보장**이 하나 더 붙습니다. 점수만으로 뽑으면 업보트 수천 개짜리 Reddit이
자리를 다 가져가고, 좋아요 수를 못 읽어오는 Behance·노트폴리오·Instagram은 매일 밀려납니다.
그래서 소스마다 최소 1장은 먼저 확보하고 남은 자리를 점수순으로 채웁니다
(`guaranteed_images_per_source`, 0으로 두면 순수 점수순).

## 4-1. API가 없는 곳 붙이기 (Behance · Dribbble · 노트폴리오 · 월간디자인)

이 네 곳은 공개 API가 없거나 닫혔습니다. Behance는 2020년에 공개 API를 내렸고, Dribbble API v2는
OAuth를 받아도 인기 샷 목록을 안 줍니다. 그래서 **사이트가 브라우저에 내려주는 데이터를 그대로
읽습니다.** 대신 사이트별 파이썬 코드는 쓰지 않습니다 — 추출 방식만 `sources.toml`에 적습니다.

```toml
[[scrape]]
name = "Dribbble"
url = "https://dribbble.com/shots/popular"
base_url = "https://dribbble.com"
strategy = "html"          # json | embedded_json | html | og
link_pattern = "/shots/"   # 이 조각이 들어간 링크를 항목으로 본다
weight = 1.4
```

| 전략 | 언제 쓰나 |
| --- | --- |
| `json` | 주소가 JSON을 그대로 내려줄 때 |
| `embedded_json` | HTML 안 `<script>`에 데이터가 박혀 있을 때 (Next.js 계열) |
| `html` | 카드 그리드를 `<a>`/`<img>` 짝으로 훑을 때 |
| `og` | 대표 이미지 한 장만 필요할 때 |

**필드 위치를 몰라도 됩니다.** `fields`를 비워두면 이미지가 들어 있는 배열을 스스로 찾고,
제목·링크·좋아요 수도 이름이 그럴듯한 키에서 알아서 가져옵니다(`likeCount`, `appreciations`,
`saves` 등, `"1.2k"` 표기도 숫자로). 설정한 경로가 사이트 개편으로 어긋나도 자동 탐색으로
넘어가고, 그마저 실패하면 최소한 페이지 대표 이미지(og:image)는 건집니다.

### 깨졌을 때 고치는 법

사이트 구조가 바뀌면 `check`에서 ❌ 또는 `0장`으로 나옵니다. 그때:

```bash
python -m design_digest debug --source Behance
```

응답 크기, og 태그, `<script>` 안 JSON 덩어리 개수, 자동 탐색이 찾아낸 항목 수와 **실제 키 이름**을
보여줍니다. 거기 보이는 키 이름을 `fields`에 적어주면 끝입니다. `--save`를 붙이면 받은 원본을
파일로 남깁니다.

### 인스타그램 · 핀터레스트

이 둘은 로그인 없이는 어떤 방법으로도 안정적으로 읽히지 않습니다. 공식 API는 둘 다 본인 계정의
콘텐츠만 주고 앱 심사가 필요합니다. 현실적인 길은 **RSSHub를 직접 띄우는 것**입니다.

```bash
docker run -d -p 1200:1200 diygod/rsshub
```

띄운 뒤 `sources.toml`의 주석을 풀면 됩니다.

```toml
[[feed]]
name = "Instagram · 팔로우 중인 디자이너"
url = "http://localhost:1200/instagram/user/계정이름"
kind = "image"       # 항목을 글이 아니라 작업물로 취급
weight = 1.5
```

`kind = "image"`가 붙은 피드는 글 섹션이 아니라 이미지 섹션으로 갑니다. 로그인 쿠키가 필요한
경로라면 `cookie_env = "IG_COOKIE"` 처럼 **환경변수 이름**을 적어두세요 (값이 아니라 이름입니다).

몇 가지 현실적인 주의점:
- GitHub Actions에서 돌리면 클라우드 IP라 일부 사이트가 막을 수 있습니다. 그럴 땐 이 소스만
  로컬에서 돌리거나 RSSHub를 본인 서버에 띄우는 편이 낫습니다.
- 인스타그램에 본인 세션 쿠키를 쓰면 계정이 제한될 가능성이 있습니다. 부계정을 권합니다.
- 요청은 하루 한 번, 소스당 한 번뿐이라 부담을 주는 수준은 아닙니다.

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
| `guaranteed_images_per_source` | `DIGEST_GUARANTEED_IMAGES_PER_SOURCE` | 1 | 이미지 소스별 보장 장수 |
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
| `debug --source Behance` | 스크랩 소스가 실제로 뭘 내려주는지 확인 (셀렉터 고칠 때) |
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
│   ├── scrape.py      API 없는 사이트용 범용 추출기
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

102개 테스트 모두 네트워크를 타지 않습니다. 파서·스크랩 전략·분류·랭킹·중복제거·렌더링·
메일 조립을 고정된 픽스처로 검증합니다.

스크랩 테스트가 확인하는 것은 "Behance가 오늘도 되는가"가 아니라 "이런 구조면 뽑아낼 수
있는가"입니다. 실제 사이트 상태는 `check`로 확인하세요.

## 10. 알아둘 점

- **소스 가용성**: `sources.toml` 의 피드 주소는 공개 RSS 기준으로 적어둔 것이라, 매체가 주소를
  바꿨다면 `check` 에서 ❌ 가 납니다. 그때 URL만 고치면 됩니다.
- **스크랩 소스는 깨질 수 있습니다**: Behance·Dribbble·노트폴리오·월간디자인은 사이트 개편에
  영향을 받습니다. 자동 탐색과 og:image 폴백으로 한 번에 죽지는 않게 해뒀지만, 0장이 나오면
  `debug --source 이름` 으로 키 이름을 확인해 `fields` 에 적어주세요. 코드 수정은 필요 없습니다.
- **Reddit**: 클라우드 IP에서는 공개 JSON이 막힙니다(§3-1 참고). 인증을 넣지 않으면 Actions
  실행에서 서브레딧이 전부 실패하지만, 글 리포트와 나머지 이미지 소스는 정상 동작합니다.
- **방화벽에 막히는 매체**: 일부 사이트는 RSS 리더가 아닌 요청을 405/415로 거절합니다.
  그런 응답을 받으면 브라우저처럼 보이는 헤더로 한 번 더 시도합니다(요즘IT, CSS-Tricks가
  이 경우였습니다).
- **요약**: 피드가 주는 본문 앞부분을 발췌하는 방식입니다. LLM 요약이 필요하면 `pipeline.py` 의
  분류 단계 뒤에 붙이면 됩니다.
