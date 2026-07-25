const CACHE_NAME = "kakaotalk-fake-v3";
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
  "./rows/row-19-cj-deljoie.jpg",
  "./rows/row-20-loccitane.jpg",
  "./rows/row-21-ably.jpg",
  "./rows/row-22-jinryang.jpg",
  "./rows/row-23-sibotaku.jpg",
  "./rows/row-24-twosome.jpg",
  "./rows/row-25-juvis-ad.jpg",
  "./rows/row-26-bithumb.jpg",
  "./rows/row-27-banksalad.jpg",
  "./rows/row-28-klairs.jpg",
  "./rows/row-29-taling.jpg",
  "./rows/row-30-zigzag.jpg",
  "./rows/row-31-lguplus.jpg",
  "./rows/row-32-kakaogift.jpg",
  "./rows/row-33-delipang.jpg",
  "./rows/row-34-starbucks.jpg",
  "./rows/row-35-paybook.jpg",
  "./rows/row-36-studyalert.jpg",
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
