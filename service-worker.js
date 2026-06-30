// ─────────────────────────────────────────────────────────────
// service-worker.js
// Permite que CajeroSinComisión funcione offline y se instale
// como app en el celular.
// ─────────────────────────────────────────────────────────────

const CACHE_NAME = "cajero-sin-comision-v1";

// Archivos que se guardan en caché para funcionar sin internet
const ARCHIVOS_CACHE = [
  "/",
  "/index.html",
  "/manifest.json",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
];

// ── Instalación: guarda archivos en caché ────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[SW] Guardando archivos en caché...");
      return cache.addAll(ARCHIVOS_CACHE);
    })
  );
  self.skipWaiting();
});

// ── Activación: limpia cachés antiguas ───────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// ── Fetch: sirve desde caché si está disponible ──────────────
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Las llamadas a la API siempre van a la red (datos en tiempo real)
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Para todo lo demás: caché primero, red como respaldo
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request).then((response) => {
        // Guardar en caché si es una respuesta válida
        if (response.status === 200) {
          const clon = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clon));
        }
        return response;
      });
    })
  );
});
