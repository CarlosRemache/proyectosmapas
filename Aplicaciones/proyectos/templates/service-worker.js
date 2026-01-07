{% load static %}
const CACHE_NAME = "distric-pwa-v5";

const URLS_TO_CACHE = [
  "/",              
  "/login/",
  "/inicio/",
  "/offline/",
  "/historial/",
  "/perfilusuario/",
  "/reporteviaje/",
  "/reportehistorial/",
  "/nuevopedido/",
  "/nuevoproveedor/",
  "/buscarlugares/",
  "/rutas/",
  "/recorrido/",
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
  "/pagos/",
  "/salvoconductos/",
  "{% url 'manifest' %}",

  "{% static 'plantilla/assets/css/main.css' %}",
  "{% static 'plantilla/assets/js/main.js' %}",
  "{% static 'icons/icon-192x192.png' %}",
  "{% static 'icons/icon-512x512.png' %}",

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
