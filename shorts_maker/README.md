# shorts_maker — 매일 쇼츠 자동 편집

매일 넣어주는 **클립·목소리(mp3)·자막(srt)** 으로, 지금까지 만들던 스타일 그대로 쇼츠를 만듭니다.

- 자막 구간마다 **제품이 잘 보이고, 선명하고, 화면 속 글자가 적은 장면**을 골라 컷 편집
- 장면이 자막 구간보다 길면 최대 **2.5배속**까지 빠르게 해서 맞춤 (느리게 늘리지 않음)
- 같은 장면 재사용 없음, 한 원본 영상에서는 **합계 5초까지**
- 원본 영상에 박힌 자막은 **블러로 가림**
- 9:16 이 아닌 영상은 꽉 차게 확대
- 원본 소리 음소거, 목소리 **+15dB** (소리 깨짐 방지 리미터)
- 자막: 흰색 + 검은 그림자(거리 0), 한 줄, 화면 위쪽
- 맨 앞 **1프레임 썸네일** + 오른쪽 위 `[광고]` 표시

## 1. 처음 한 번만: 설치 (맥)

```bash
# Homebrew 가 없다면 https://brew.sh 의 설치 명령을 먼저 실행
brew install python ffmpeg

cd ~/python_project            # 이 저장소를 받은 위치
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-shorts.txt
```

폰트 파일을 `fonts/` 폴더에 넣고, 설정 파일을 만듭니다.

```bash
mkdir -p fonts
cp shorts_maker.example.toml shorts_maker.toml
# shorts_maker.toml 의 font 경로를 실제 폰트 파일 이름으로 고치기
#   자막:   온글잎 밑미체
#   썸네일: 낼나 리지체
```

## 2. 매일 할 일

작업폴더 하나에 재료를 넣습니다 (폴더 이름이 결과 파일 이름이 됩니다).

```
2026-10-17/
├── clips/          원본 클립 10~20개 (mp4, mov …)
├── product/        제품 사진 1~3장 (제품이 잘 보이는 사진)
├── voice.mp3       목소리 (이름은 자유, 1개)
├── subs.srt        자막 (이름은 자유, 1개, 항상 한 줄 길이로)
└── thumbnail.txt   썸네일 문구
```

`thumbnail.txt` 는 보이는 그대로 줄을 나눠 적고, 노란색으로 강조할 부분은 `*` 로 감쌉니다.

```
*세탁소* 하시면
보지 마세요
```

실행:

```bash
source .venv/bin/activate
python -m shorts_maker ~/Desktop/2026-10-17
```

결과는 작업폴더의 `result/` 에 생깁니다.

| 파일 | 내용 |
| --- | --- |
| `result/2026-10-17.mp4` | 완성 영상 |
| `result/thumbnail.png` | 썸네일 프레임 |
| `result/plan.txt` | 컷마다 어떤 원본의 몇 초를 몇 배속으로 썼는지 |

### 미리 확인하는 옵션

```bash
python -m shorts_maker 작업폴더 --preview     # 자막·썸네일 문구 모양만 PNG 로 (몇 초)
python -m shorts_maker 작업폴더 --plan-only   # 컷 계획만 보고 영상은 안 만듦
```

클립 분석 결과는 작업폴더의 `.cache/` 에 저장돼서, srt 나 썸네일 문구만 고쳐서 다시 돌릴 때는 금방 끝납니다.

## 3. 이런 메시지가 나오면

- **한 줄에 다 들어가지 않는 자막이 있습니다** → 알려준 번호의 자막을 짧게 고쳐서 다시 실행
- **N번 자막 구간에 쓸 장면이 부족합니다** → 그 길이 이상 이어지는 장면이 있는 클립을 더 넣기
  (한 영상당 5초 제한 때문에 클립 수가 적으면 생깁니다)
- **CLIP 모델을 쓸 수 없어 특징점 매칭으로 대신합니다** → 인터넷 연결을 확인 (처음 한 번 모델을 내려받습니다)

## 4. 스타일 조정

`shorts_maker.toml` 에서 자막 크기·위치, 그림자, 블러 세기, 배속 상한, 장면 고르는 기준 등을 바꿀 수 있습니다.
각 항목 설명은 `shorts_maker.example.toml` 에 있습니다.
