// 편집 포인트: 아래 CONTACTS/MESSAGES 배열만 수정하면 화면 내용이 바뀝니다.

const FRIEND_ID = "raego";

const CONTACTS = [
  { id: "c1", name: "생존신고 요망", count: "3", time: "오후 4:51", msg: "설마", avatar: { emoji: "🏝️", bg: "#3a3a3c" } },
  { id: "c2", name: "굴비", time: "오후 4:22", msg: "넹", avatar: { emoji: "🐕", bg: "#d8c9b0" } },
  { id: "c3", name: "카카오톡 지갑", time: "오후 4:20", msg: "카카오 인증서를 발급했어요.", avatar: { emoji: "👛", bg: "#4fa8e0" } },
  { id: "c4", name: "민혁", time: "오후 3:31", msg: "와..", avatar: { emoji: "🌊", bg: "#2b6b6b" } },
  { id: "c5", name: "카카오계정", unread: "1", time: "오후 3:00", msg: "카카오톡 로그인 시도 알림", avatar: { emoji: "🔒", bg: "#ffcd00" } },
  { id: "c6", name: "삼성카드", time: "오후 2:28", msg: "삼성3571승인 오*현 11,500원 일시불...", avatar: { text: "삼성\n카드", bg: "#1428a0" } },
  { id: "c7", name: "카카오페이", time: "오후 2:28", msg: "결제가 완료되었어요.", avatar: { text: "pay", bg: "#ffcd00" } },
  { id: "c8", name: "가족방", count: "4", muted: true, time: "오후 1:25", msg: "삼계탕 끓여 놓음 먹으시오...", avatar: { emoji: "👨‍👩‍👧‍👦", bg: "#48484a" } },
  { id: "c9", name: "6월 팬션 놀쟈야야~", count: "11", muted: true, time: "오후 12:32", msg: "에어컨켜놓고 출근한다", avatar: { emoji: "🐱", bg: "#5a5a5c" } },
  { id: "c10", name: "델쥬아", unread: "1", time: "오전 10:30", msg: "(광고) 델쥬아 정기구독 누적리뷰", avatar: { text: "D", bg: "#ffffff", fg: "#1f7a4d" } },
  { id: "c11", name: "카카오톡 예약하기", time: "오전 10:00", msg: "(광고)[특가] 롯데호텔 월드 라세느", avatar: { emoji: "📅", bg: "#ffcd00" } },
  { id: "c12", name: "드림이", time: "오전 9:56", msg: "[정기적 수신동의 확인 안내] 안녕하세요. 드림이 카카오톡 채널입니다....", avatar: { emoji: "🐭", bg: "#e8e8ea" } },
  { id: "c13", name: "롱블랙", time: "오전 9:30", msg: "게으름의 기술 : 생각 많은 헤르만 헤세의 휴식 노하우", avatar: { text: "LB", bg: "#000000" } },
  { id: FRIEND_ID, name: "라고했을때시켜야짛는데/한되팔렘", time: "오전 12:16", msg: "히필갑자기이런일이", avatar: { img: "assets/friend-avatar.png" }, tappable: true },
  { id: "c15", name: "톡클라우드", time: "어제", msg: "곧 백업 중단! 용량을 확보해 주세요.", avatar: { emoji: "☁️", bg: "#ffcd00" } },
  { id: "c16", name: "여름인데 놀러와!", ad: true, time: "어제", msg: "AD · App Store", avatar: { emoji: "🅰️", bg: "#0a84ff" } },
  { id: "c17", name: "디하클 - (디지털노마드 하이클래스)", unread: "2", muted: true, time: "어제", msg: "(광고) 😱 월 200직장인 -> 월4300만원", avatar: { text: "디하클", bg: "#ffffff", fg: "#111111" } },
  { id: "c18", name: "WSA와인아카데미", time: "어제", msg: "(광고) 지금 오픈 이벤트 진행 중", avatar: { text: "WSA", bg: "#5b3a9e" } },
];

const NOTICE = {
  title: "포항역 도착 - 학교 택시",
  body: "삼촌네 점심 , 학교 속삭...",
};

const MESSAGES = [
  { sender: "them", type: "text", text: "개내고", time: "오후 10:39" },
  { sender: "me", type: "text", text: "ㅠㅠㅠㅠㅠㅠㅠ", time: "오후 10:39" },
  { sender: "me", type: "text", text: "어니오ㅑ", time: "오후 10:39" },
  { sender: "them", type: "text", text: "걍 취소", time: "오후 10:39" },
  { sender: "me", type: "text", text: "갑자기", time: "오후 10:39" },
  { sender: "me", type: "text", text: "뭘해놧는디", time: "오후 10:39" },
  { sender: "me", type: "text", text: "ㄴㅁ친은", time: "오후 10:39" },
  { sender: "me", type: "text", text: "어디감", time: "오후 10:39" },
  { sender: "them", type: "text", text: "남친쓰러짐", time: "오후 10:39" },
  { sender: "them", type: "text", text: "ㅜ", time: "오후 10:39" },
  { sender: "me", type: "text", text: "??", time: "오후 10:39" },
  { sender: "them", type: "text", text: "몸살남", time: "오후 10:39" },
  { sender: "me", type: "text", text: "아", time: "오후 10:39" },
  { sender: "me", type: "text", text: "ㄷㄷ슨....", time: "오후 10:39" },
  { sender: "them", type: "sticker", emoji: "🐹", time: "오후 10:39" },
  { sender: "me", type: "text", text: "무슨", time: "오후 10:39" },
  { sender: "me", type: "text", text: "페스티벌인대", time: "오후 10:39" },
  { sender: "them", type: "text", text: "ㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋ", time: "오후 10:40" },
  { sender: "me", type: "text", text: "아니근데내가진자", time: "오후 10:40" },
  { sender: "me", type: "text", text: "앵간하면", time: "오후 10:40" },
  { sender: "me", type: "text", text: "가겟다", time: "오후 10:40" },
  { sender: "me", type: "text", text: "개헬주간이라", time: "오후 10:40" },
];
