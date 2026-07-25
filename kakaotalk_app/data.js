// 편집 포인트: ROWS 배열의 time/msg 값과 MESSAGES 배열만 고치면 화면 내용이 바뀝니다.
// (나머지 대화상대는 실제 스크린샷을 잘라 만든 이미지라서 코드로 수정할 수 없습니다.)

const FRIEND_ID = "friend";

const ROWS = [
  { id: "oh-suhyeon", img: "rows/row-01-oh-suhyeon.png" },
  { id: "gulbi", editable: true, img: "rows/row-02-gulbi-masked.png", time: "오후 4:22", msg: "넹" },
  { id: "family", img: "rows/row-03-family.png" },
  { id: "survival", img: "rows/row-04-survival.png" },
  { id: "wallet", img: "rows/row-05-wallet.png" },
  { id: "account", img: "rows/row-06-account.png" },
  { id: "samsungcard", img: "rows/row-07-samsungcard.png" },
  { id: "kakaopay", img: "rows/row-08-kakaopay.png" },
  { id: "june-pension", img: "rows/row-09-june-pension.png" },
  { id: "deljoie", img: "rows/row-10-deljoie.png" },
  { id: "reserve", img: "rows/row-11-reserve.png" },
  { id: "dreami", img: "rows/row-12-dreami.png" },
  { id: "longblack", img: "rows/row-13-longblack.png" },
  {
    id: FRIEND_ID,
    editable: true,
    tappable: true,
    img: "rows/row-14-friend-masked.png",
    time: "오전 12:16",
    msg: "히필갑자기이런일이",
    roomTitle: "라고했을때시켜야짛는데/한되팔렘",
  },
  { id: "talkcloud", img: "rows/row-15-talkcloud.png" },
  { id: "dihacle", img: "rows/row-16-dihacle.png" },
  { id: "wsa", img: "rows/row-17-wsa.png" },
  { id: "fastcampus", img: "rows/row-18-fastcampus.png" },
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
