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
  "./rows/row-01-oh-suhyeon.jpg",
  "./rows/row-02-gulbi-masked.jpg",
  "./rows/row-03-family.jpg",
  "./rows/row-04-survival.jpg",
  "./rows/row-05-wallet.jpg",
  "./rows/row-06-account.jpg",
  "./rows/row-07-samsungcard.jpg",
  "./rows/row-08-kakaopay.jpg",
  "./rows/row-09-june-pension.jpg",
  "./rows/row-10-deljoie.jpg",
  "./rows/row-11-reserve.jpg",
  "./rows/row-12-dreami.jpg",
  "./rows/row-13-longblack.jpg",
  "./rows/row-14-friend-masked.jpg",
  "./rows/row-15-talkcloud.jpg",
  "./rows/row-16-dihacle.jpg",
  "./rows/row-17-wsa.jpg",
  "./rows/row-18-fastcampus.jpg",
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
