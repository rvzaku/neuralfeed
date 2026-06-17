// Minimal service worker — satisfies PWA installability (a fetch handler is
// required) and provides a tiny offline shell. NeuralFeed is a live curator, so
// we deliberately do NOT cache API responses or article content; we only fall
// back to a cached app shell when the network is unavailable. Network-first.
const CACHE = "neuralfeed-shell-v1";
const SHELL = ["/"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  // Only handle same-origin GET navigations; never touch API/auth traffic.
  if (request.method !== "GET" || new URL(request.url).origin !== self.location.origin) return;
  if (request.mode !== "navigate") return;

  event.respondWith(
    fetch(request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(request, copy)).catch(() => {});
        return res;
      })
      .catch(() => caches.match(request).then((r) => r || caches.match("/")))
  );
});
