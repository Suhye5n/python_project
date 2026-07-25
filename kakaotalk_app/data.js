// 편집 포인트: ROWS 배열의 time/msg 값과 MESSAGES 배열만 고치면 화면 내용이 바뀝니다.
// (나머지 대화상대는 실제 스크린샷을 잘라 만든 이미지라서 코드로 수정할 수 없습니다.)

const FRIEND_ID = "friend";

const ROWS = [
  { id: "oh-suhyeon", img: "rows/row-01-oh-suhyeon.jpg" },
  { id: "gulbi", editable: true, img: "rows/row-02-gulbi-masked.jpg", time: "오후 4:22", msg: "넹" },
  { id: "family", img: "rows/row-03-family.jpg" },
  { id: "survival", img: "rows/row-04-survival.jpg" },
  { id: "wallet", img: "rows/row-05-wallet.jpg" },
  { id: "account", img: "rows/row-06-account.jpg" },
  { id: "samsungcard", img: "rows/row-07-samsungcard.jpg" },
  { id: "kakaopay", img: "rows/row-08-kakaopay.jpg" },
  { id: "june-pension", img: "rows/row-09-june-pension.jpg" },
  { id: "deljoie", img: "rows/row-10-deljoie.jpg" },
  { id: "reserve", img: "rows/row-11-reserve.jpg" },
  { id: "dreami", img: "rows/row-12-dreami.jpg" },
  { id: "longblack", img: "rows/row-13-longblack.jpg" },
  {
    id: FRIEND_ID,
    editable: true,
    tappable: true,
    img: "rows/row-14-friend-masked.jpg",
    time: "오전 12:16",
    msg: "히필갑자기이런일이",
    roomTitle: "라고했을때시켜야짛는데/한되팔렘",
  },
  { id: "talkcloud", img: "rows/row-15-talkcloud.jpg" },
  { id: "dihacle", img: "rows/row-16-dihacle.jpg" },
  { id: "wsa", img: "rows/row-17-wsa.jpg" },
  { id: "fastcampus", img: "rows/row-18-fastcampus.jpg" },
];

const NOTICE = {
  title: "포항역 도착 - 학교 택시",
  body: "삼촌네 점심 , 학교 속삭...",
};

function block(sender, time, lines) {
  return lines.map((text) => ({ sender, type: "text", text, time }));
}

const MESSAGES = [
  { type: "date", label: "2026년 7월 23일 목요일" },
  ...block("them", "오후 8:22", ["님아…", "하 ㅅㅍ", "님아 카톡좀"]),
  ...block("me", "오후 8:23", ["애", "왜", "웨", "우ㅔ"]),
  ...block("them", "오후 8:24", ["그때", "그 여행갓다가 오고나서", "전호ㅏ한거", "그내용 결국 남친이 꺼냇음"]),
  ...block("me", "오후 8:25", ["ㅎㄷㄷㄷ", "머래그래서"]),
  ...block("them", "오후 8:26", [
    "자기가 이태까지 부담한ㅜ것들이 너무 부담스럽다 앞으로도 계속 그런식으로 우리가 만나고 데이트하면 더이상 만나기 힘들거같다고",
    "본인이 먼저 헤어지자는 뉭아스로",
    "말꺼냄",
  ]),
  ...block("me", "오후 8:27", ["ㅁㅊ", "개에바;", "아니", "ㄹㅇ로?"]),
  ...block("them", "오후 8:28", [
    "지금 심장진짜 개두근두근뛰고 심신미약임ㅠ",
    "하..",
    "ㅜㅠㅠㅠㅠㅠㅠㅠ",
    "차라리 내가 먼저 꺼낼껄 싶기도 하면서도",
    "정리가 안된 상태에서 갑자기 이렇게 되니까 심장이 너무ㅜ아픔",
  ]),
  ...block("me", "오후 8:29", ["님아", "낼", "조우가능?", "이거는 카톡으로 안될듯 나지금 전화가안돼서"]),
  ...block("them", "오후 8:30", ["ㄱㄴ…", "근데 내 심장 상태 보고", "몇시?"]),
  ...block("me", "오후 8:31", ["7 ㄱㄱ", "일단", "님 멘탈 나가면 밥 못먹나", "맛잇는거좀 맥이고"]),
  ...block("them", "오후 8:32", ["일단 ㅇㅋ,,"]),

  { type: "date", label: "2026년 7월 24일 금요일" },
  ...block("me", "오후 5:32", ["님", "ㅇㄷ", "ㅇㄷ", "ㅇㄷ임"]),
  ...block("them", "오후 5:33", ["나 인제 끝"]),
  ...block("me", "오후 5:34", ["ㄱㄱ가능?", "이럴땐 오히려", "밥좀 먹고 술좀 먹고", "해야함"]),
  ...block("them", "오후 5:35", [
    "근데 님아 나",
    "개뜬금없긴 한데",
    "더현서에서 머 사야될거 있는데",
    "선임님 생일선물",
    "사줘야함",
  ]),
  ...block("me", "오후 5:36", ["그때 너가 얘기했던 그", "관심남??"]),
  ...block("them", "오후 5:37", ["ㄴㄴㄴ 걔 아님", "2번선임"]),
  ...block("me", "오후 5:38", ["아 ㅇㅋㅇㅋ", "글면", "더현서에서 걍", "아무거나 좋은거 내가 골라감"]),
  ...block("them", "오후 5:39", ["ㅇㅋㅇㅋ"]),
  ...block("me", "오후 5:40", ["님 안땡기는거 없지"]),
  ...block("them", "오후 5:41", ["ㅇㅇ 오히려", "밥 못먹어서", "지금 배고픔"]),
  ...block("me", "오후 5:42", ["ㅜ", "오키 내가 맛잇는거 사줌슨"]),
  ...block("them", "오후 5:43", ["ㅇㅋㅇㅋ"]),
];
