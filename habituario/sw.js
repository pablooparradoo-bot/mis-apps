/* Mi Habituario: funciona sin conexión. La página se pide primero a la red (para recibir actualizaciones) y, si no hay red, se usa la copia guardada. */
const V = "habituario-v2.2.0";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./icon-180.png", "./icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(V).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k.startsWith("habituario-") && k !== V).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const r = e.request;
  if (r.method !== "GET") return;
  const u = new URL(r.url);

  if (r.mode === "navigate") {
    e.respondWith(
      fetch(r)
        .then((res) => {
          if (res.ok) { const cp = res.clone(); caches.open(V).then((c) => c.put("./index.html", cp)); }
          return res;
        })
        .catch(() => caches.match("./index.html"))
    );
    return;
  }

  const fonts = u.host === "fonts.googleapis.com" || u.host === "fonts.gstatic.com";
  if (u.origin === self.location.origin || fonts) {
    e.respondWith(
      caches.match(r).then((hit) => {
        const net = fetch(r)
          .then((res) => {
            if (res.ok || res.type === "opaque") { const cp = res.clone(); caches.open(V).then((c) => c.put(r, cp)); }
            return res;
          })
          .catch(() => hit);
        return hit || net;
      })
    );
  }
});
