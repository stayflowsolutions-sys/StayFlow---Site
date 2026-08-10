// Service worker - notificacoes push (Web Push API) + criterio minimo
// de instalabilidade de PWA (Chrome exige um service worker com
// handler de "fetch" registrado pra oferecer "Instalar app").

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  // De proposito SEM estrategia de cache ainda - so repassa pra rede
  // normal. Existe so pra satisfazer o criterio de instalabilidade do
  // Chrome; cache de verdade (assets estaticos) fica pra quando tiver
  // uma estrategia de invalidacao por versao - servir JS/HTML
  // desatualizado depois de um deploy ja foi um problema real nesta
  // mesma sessao (cache de navegador confundindo o que estava no ar).
  event.respondWith(fetch(event.request));
});

self.addEventListener("push", (event) => {
  let payload = { title: "StayFlow", body: "" };
  try {
    if (event.data) payload = event.data.json();
  } catch (error) {
    payload.body = event.data ? event.data.text() : "";
  }

  const title = payload.title || "StayFlow";
  const options = {
    body: payload.body || "",
    icon: "/assets/images/logo.png",
    badge: "/assets/images/logo.png",
    data: { url: payload.url || "/app" },
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) || "/app";

  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if (client.url.includes(self.location.origin) && "focus" in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      return self.clients.openWindow(targetUrl);
    })
  );
});
