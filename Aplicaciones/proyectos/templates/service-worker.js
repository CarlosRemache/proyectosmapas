{% load static %}
const CACHE_NAME = "distric-pwa-v2";

const URLS_TO_CACHE = [
  "/",              // login (si la raíz redirige ahí)
  "/login/",
  "/inicio/",
  "/offline/",
  "/historial/",
  "/perfilusuario/",
  "/creardocumento/",
  "/nuevovehiculo/",
  "/listadovehiculo/",
  "/pedidosusuario/",
  "/adminpanel/",
  "/panel/calendario/",
  "/panel/calendario/lista/",
  "/lista_asignaciones/",
  "/listadoproveedor/",
  "/listadopedido/",
  "/listadofacturas/",
  "/listado_pagos/",
  "/salvoconductos/",
  "{% static 'plantilla/assets/css/main.css' %}",
  "{% static 'plantilla/assets/js/main.js' %}",
  "{% static 'plantilla/assets/img/icon-192.png' %}",
  "{% static 'plantilla/assets/img/icon-512.png' %}",
  "{% static 'plantilla/assets/manifest.webmanifest' %}",
];



// Instalar: guardar en caché
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(URLS_TO_CACHE))
  );
});

// Activar: limpiar caches viejas
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names.map((name) => {
          if (name !== CACHE_NAME) return caches.delete(name);
        })
      )
    )
  );
});

// Fetch: network first con fallback a caché/offline
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        return response;
      })
      .catch(() =>
        caches.match(event.request).then((cached) => {
          if (cached) return cached;
          return caches.match("/offline/");
        })
      )
  );
});
