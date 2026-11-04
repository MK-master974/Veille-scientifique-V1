/* Lecture hors ligne : l'app est gardée en cache, les données sont prises sur le réseau
   en priorité (pour avoir la dernière veille) puis dans le cache en l'absence de connexion. */
const VERSION = 'veille-sante-v1';
const COQUILLE = ['./', 'index.html', 'styles.css', 'app.js', 'manifest.webmanifest', 'icon.svg', 'icon-192.png', 'icon-512.png',
  'data/catalogue.json', 'data/config.json', 'data/index.json'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(COQUILLE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    .then((cles) => Promise.all(cles.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== self.location.origin) return;
  if (url.pathname.includes('/push/onesignal/')) return;

  if (url.pathname.includes('/data/')) {
    e.respondWith(fetch(req).then((rep) => {
      if (rep.ok) { const copie = rep.clone(); caches.open(VERSION).then((c) => c.put(req, copie)); }
      return rep;
    }).catch(() => caches.match(req, { ignoreSearch: true }).then((r) => r || Response.error())));
    return;
  }

  e.respondWith(caches.match(req, { ignoreSearch: true }).then((enCache) => {
    const reseau = fetch(req).then((rep) => {
      if (rep.ok) { const copie = rep.clone(); caches.open(VERSION).then((c) => c.put(req, copie)); }
      return rep;
    }).catch(() => enCache || caches.match('index.html'));
    return enCache || reseau;
  }));
});
