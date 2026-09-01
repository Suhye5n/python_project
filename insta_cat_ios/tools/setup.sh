#!/bin/sh
# 번들 ID 와 App Group 을 본인 것으로 한 번에 바꿉니다.
#
#   ./tools/setup.sh com.mingyu
#
# 그러면 이렇게 바뀝니다:
#   앱          com.example.InstaCat        -> com.mingyu.InstaCat
#   확장 4개    com.example.InstaCat.Monitor -> com.mingyu.InstaCat.Monitor  (…등)
#   App Group   group.com.example.instacat  -> group.com.mingyu.instacat
set -e

PREFIX="$1"
if [ -z "$PREFIX" ]; then
    echo "사용법: ./tools/setup.sh <번들 ID 앞부분>"
    echo "예시:   ./tools/setup.sh com.mingyu"
    exit 1
fi

cd "$(dirname "$0")/.."

# project.yml 과 AppGroup.swift 에 흩어진 com.example 을 전부 바꿉니다.
# group.com.example.instacat 도 com.example 을 품고 있어 같이 바뀝니다.
for f in project.yml Sources/Shared/AppGroup.swift; do
    sed -i.bak "s/com\.example/$PREFIX/g" "$f"
    rm -f "$f.bak"
done

echo "번들 ID 를 $PREFIX.* 로 바꿨습니다."
echo

if command -v xcodegen >/dev/null 2>&1; then
    xcodegen generate
    echo
    echo "다음: open InstaCat.xcodeproj"
    echo "     Xcode 에서 타깃 5개의 Signing & Capabilities > Team 을 본인 계정으로 지정하세요."
else
    echo "xcodegen 이 없습니다. 먼저 설치하세요:"
    echo "    brew install xcodegen"
    echo "그 다음: xcodegen generate"
fi
