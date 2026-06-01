const CACHE_NAME = "health-tracker-v3";

self.addEventListener("install", event => {
  self.skipWaiting(); // 🔥 forces activation immediately
});

self.addEventListener("activate", event => {
  event.waitUntil(self.clients.claim()); // 🔥 forces control of open tabs
});

self.addEventListener("fetch", event => {
  event.respondWith(fetch(event.request));
});