// Service worker minimo, feito so pra notificacoes push (Web Push API).
// Nao faz cache de nada de propósito - a StayFlow ainda nao e um PWA
// completo, so precisa de um service worker registrado pra poder
// receber "push" mesmo com a aba fechada.

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
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
