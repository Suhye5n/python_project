const listScreen = document.getElementById("screen-list");
const roomScreen = document.getElementById("screen-room");
const contactListEl = document.getElementById("contact-list");
const messagesEl = document.getElementById("messages");
const roomTitleEl = document.getElementById("room-title");
const backBtn = document.getElementById("back-btn");
const noticeBar = document.getElementById("notice-bar");
const noticeClose = document.getElementById("notice-close");
const msgInput = document.getElementById("msg-input");
const micBtn = document.getElementById("mic-btn");

function renderContacts() {
  contactListEl.innerHTML = "";
  ROWS.forEach((r, i) => {
    const li = document.createElement("li");
    li.className = "contact-row" + (r.tappable ? " tappable" : "");
    const loading = i < 6 ? "eager" : "lazy";

    if (r.editable) {
      const wrap = document.createElement("div");
      wrap.className = "row-wrap";
      wrap.innerHTML = `
        <img src="${r.img}" alt="" loading="${loading}" decoding="async" />
        <span class="overlay-time">${r.time}</span>
        <span class="overlay-msg">${r.msg}</span>
      `;
      li.appendChild(wrap);
    } else {
      li.innerHTML = `<img src="${r.img}" alt="" loading="${loading}" decoding="async" />`;
    }

    if (r.tappable) {
      li.addEventListener("click", () => openRoom(r));
    }

    contactListEl.appendChild(li);
  });
}

function renderMessages() {
  const friend = ROWS.find((r) => r.id === FRIEND_ID);
  messagesEl.innerHTML = "";
  MESSAGES.forEach((m, i) => {
    if (m.type === "date") {
      const divider = document.createElement("div");
      divider.className = "date-divider";
      divider.innerHTML = `<span>${m.label} <span class="date-chevron">&gt;</span></span>`;
      messagesEl.appendChild(divider);
      return;
    }

    const prev = MESSAGES[i - 1];
    const next = MESSAGES[i + 1];
    const isNewGroup = !prev || prev.sender !== m.sender;
    const showTime = !next || next.sender !== m.sender || next.time !== m.time;

    const row = document.createElement("div");
    row.className = "msg-row " + (m.sender === "me" ? "mine" : "theirs");

    if (m.sender === "them") {
      const avatarWrap = document.createElement("div");
      avatarWrap.className = "sender-avatar" + (isNewGroup ? "" : " spacer");
      avatarWrap.innerHTML = `<img src="assets/friend-avatar.png" alt="" />`;
      row.appendChild(avatarWrap);
    }

    const group = document.createElement("div");
    group.className = "msg-group";

    if (m.sender === "them" && isNewGroup) {
      const name = document.createElement("div");
      name.className = "sender-name";
      name.textContent = friend.roomTitle;
      group.appendChild(name);
    }

    const line = document.createElement("div");
    line.className = "bubble-line";

    const bubble = document.createElement("div");
    bubble.className = "bubble" + (m.type === "sticker" ? " sticker" : "");
    bubble.textContent = m.type === "sticker" ? m.emoji : m.text;

    line.appendChild(bubble);

    if (showTime) {
      const time = document.createElement("span");
      time.className = "msg-time";
      time.textContent = m.time;
      line.appendChild(time);
    }

    group.appendChild(line);
    row.appendChild(group);
    messagesEl.appendChild(row);
  });

  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function openRoom(row) {
  roomTitleEl.textContent = row.roomTitle;
  document.getElementById("notice-title").textContent = NOTICE.title;
  document.getElementById("notice-body").textContent = NOTICE.body;
  noticeBar.classList.remove("hidden");

  listScreen.classList.add("behind");
  roomScreen.classList.add("active");
  renderMessages();

  clearBadge();
}

function closeRoom() {
  roomScreen.classList.remove("active");
  listScreen.classList.remove("behind");
}

backBtn.addEventListener("click", closeRoom);
noticeClose.addEventListener("click", () => noticeBar.classList.add("hidden"));

msgInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && msgInput.value.trim()) {
    MESSAGES.push({ sender: "me", type: "text", text: msgInput.value.trim(), time: "지금" });
    msgInput.value = "";
    micBtn.classList.remove("hidden");
    renderMessages();
  }
});

msgInput.addEventListener("input", () => {
  micBtn.classList.toggle("hidden", msgInput.value.length > 0);
});

let touchStartX = null;
roomScreen.addEventListener("touchstart", (e) => {
  touchStartX = e.touches[0].clientX;
});
roomScreen.addEventListener("touchend", (e) => {
  if (touchStartX !== null && touchStartX < 40) {
    const dx = e.changedTouches[0].clientX - touchStartX;
    if (dx > 70) closeRoom();
  }
  touchStartX = null;
});

function clearBadge() {
  if ("clearAppBadge" in navigator) {
    navigator.clearAppBadge().catch(() => {});
  }
}

if ("setAppBadge" in navigator) {
  navigator.setAppBadge(999).catch(() => {});
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  });
}

const appEl = document.getElementById("app");
if (window.visualViewport) {
  const syncViewport = () => {
    const vv = window.visualViewport;
    appEl.style.height = vv.height + "px";
    appEl.style.top = vv.offsetTop + "px";
  };
  window.visualViewport.addEventListener("resize", syncViewport);
  window.visualViewport.addEventListener("scroll", syncViewport);
  syncViewport();
}

renderContacts();
