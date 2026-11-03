/* Coplas: la app y el catálogo funcionan sin conexión. Página y catálogo se piden primero a la red para recibir coplas nuevas. */
const V = "coplas-v1.0.0";
const SHELL = ["./", "./index.html", "./catalogo.json", "./manifest.webmanifest", "./icon-180.png", "./icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(V).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k.startsWith("coplas-") && k !== V).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const r = e.request;
  if (r.method !== "GET") return;
  const u = new URL(r.url);
  const propio = u.origin === self.location.origin;

  if (r.mode === "navigate" || (propio && u.pathname.endsWith("/catalogo.json"))) {
    const clave = r.mode === "navigate" ? "./index.html" : "./catalogo.json";
    e.respondWith(
      fetch(r)
        .then((res) => {
          if (res.ok) { const cp = res.clone(); caches.open(V).then((c) => c.put(clave, cp)); }
          return res;
        })
        .catch(() => caches.match(clave))
    );
    return;
  }

  if (propio || u.host === "fonts.googleapis.com" || u.host === "fonts.gstatic.com") {
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
