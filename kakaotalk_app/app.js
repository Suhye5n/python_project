const listScreen = document.getElementById("screen-list");
const roomScreen = document.getElementById("screen-room");
const contactListEl = document.getElementById("contact-list");
const messagesEl = document.getElementById("messages");
const roomTitleEl = document.getElementById("room-title");
const backBtn = document.getElementById("back-btn");
const noticeBar = document.getElementById("notice-bar");
const noticeClose = document.getElementById("notice-close");
const msgInput = document.getElementById("msg-input");

function renderContacts() {
  contactListEl.innerHTML = "";
  CONTACTS.forEach((c) => {
    const li = document.createElement("li");
    li.className = "contact-row" + (c.tappable ? " tappable" : "");

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    if (c.avatar.img) {
      avatar.innerHTML = `<img src="${c.avatar.img}" alt="${c.name}" />`;
    } else {
      avatar.style.background = c.avatar.bg;
      avatar.style.color = c.avatar.fg || "#111";
      avatar.style.fontSize = c.avatar.text ? "13px" : "24px";
      avatar.textContent = c.avatar.text || c.avatar.emoji || "";
    }

    const main = document.createElement("div");
    main.className = "contact-main";
    main.innerHTML = `
      <div class="contact-name-row">
        <span class="contact-name">${c.name}</span>
        ${c.count ? `<span class="contact-count">${c.count}</span>` : ""}
        ${c.muted ? `<span class="mute-icon">🔕</span>` : ""}
      </div>
      <div class="contact-msg">${c.msg}</div>
    `;

    const side = document.createElement("div");
    side.className = "contact-side";
    if (c.ad) {
      side.innerHTML = `<button class="dl-btn">다운로드</button>`;
    } else {
      side.innerHTML = `<span class="contact-time">${c.time}</span>`;
      if (c.unread) {
        side.innerHTML += `<span class="contact-badge${c.muted ? " muted" : ""}">${c.unread}</span>`;
      }
    }

    li.append(avatar, main, side);

    if (c.tappable) {
      li.addEventListener("click", () => openRoom(c));
    }

    contactListEl.appendChild(li);
  });
}

function renderMessages() {
  messagesEl.innerHTML = "";
  MESSAGES.forEach((m, i) => {
    const prev = MESSAGES[i - 1];
    const next = MESSAGES[i + 1];
    const isNewGroup = !prev || prev.sender !== m.sender;
    const showTime = !next || next.sender !== m.sender || next.time !== m.time;

    const row = document.createElement("div");
    row.className = "msg-row " + (m.sender === "me" ? "mine" : "theirs");

    if (m.sender === "them") {
      const avatarWrap = document.createElement("div");
      avatarWrap.className = "sender-avatar" + (isNewGroup ? "" : " spacer");
      avatarWrap.innerHTML = `<img src="${CONTACTS.find((c) => c.id === FRIEND_ID).avatar.img}" alt="" />`;
      row.appendChild(avatarWrap);
    }

    const group = document.createElement("div");
    group.className = "msg-group";

    if (m.sender === "them" && isNewGroup) {
      const name = document.createElement("div");
      name.className = "sender-name";
      name.textContent = CONTACTS.find((c) => c.id === FRIEND_ID).name;
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

function openRoom(contact) {
  roomTitleEl.textContent = contact.name;
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
    renderMessages();
  }
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

function setBadge() {
  const total = CONTACTS.reduce((sum, c) => sum + (c.unread && !c.muted ? parseInt(c.unread) || 0 : 0), 0);
  if ("setAppBadge" in navigator) {
    navigator.setAppBadge(total).catch(() => {});
  }
}

function clearBadge() {
  if ("clearAppBadge" in navigator) {
    navigator.clearAppBadge().catch(() => {});
  }
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  });
}

renderContacts();
setBadge();
