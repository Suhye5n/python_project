const CACHE_NAME = "kakaotalk-fake-v2";
const ASSETS = [
  "./",
  "./index.html",
  "./style.css",
  "./app.js",
  "./data.js",
  "./manifest.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/apple-touch-icon.png",
  "./assets/friend-avatar.png",
  "./rows/row-01-oh-suhyeon.png",
  "./rows/row-02-gulbi-masked.png",
  "./rows/row-03-family.png",
  "./rows/row-04-survival.png",
  "./rows/row-05-wallet.png",
  "./rows/row-06-account.png",
  "./rows/row-07-samsungcard.png",
  "./rows/row-08-kakaopay.png",
  "./rows/row-09-june-pension.png",
  "./rows/row-10-deljoie.png",
  "./rows/row-11-reserve.png",
  "./rows/row-12-dreami.png",
  "./rows/row-13-longblack.png",
  "./rows/row-14-friend-masked.png",
  "./rows/row-15-talkcloud.png",
  "./rows/row-16-dihacle.png",
  "./rows/row-17-wsa.png",
  "./rows/row-18-fastcampus.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
