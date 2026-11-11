/* Lecture hors ligne et mises à jour.
   - En ligne, l'app et les données sont prises sur le réseau en priorité : une correction publiée
     arrive dès l'ouverture suivante. La copie gardée sur l'appareil ne sert que sans connexion,
     ou si le réseau met plus de quelques secondes à répondre.
   - Quand une nouvelle version de ce fichier s'installe, les pages ouvertes sont rechargées une
     fois, pour ne pas rester sur l'ancienne app. */
const VERSION = 'veille-sante-v2';
const PREFIXE = 'veille-sante-';
const DELAI_RESEAU_MS = 4000;
const COQUILLE = ['./', 'index.html', 'styles.css', 'app.js', 'manifest.webmanifest', 'icon.svg', 'icon-192.png', 'icon-512.png',
  'data/catalogue.json', 'data/config.json', 'data/index.json'];

self.addEventListener('install', (e) => {
  // « reload » : on ne se contente pas de la copie du navigateur, on redemande chaque fichier.
  e.waitUntil(caches.open(VERSION)
    .then((c) => c.addAll(COQUILLE.map((u) => new Request(u, { cache: 'reload' }))))
    .then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    // Seules les anciennes copies de cette app sont supprimées, pas celles d'une autre app
    // servie à la même adresse.
    const anciennes = (await caches.keys()).filter((k) => k.startsWith(PREFIXE) && k !== VERSION);
    await Promise.all(anciennes.map((k) => caches.delete(k)));
    await self.clients.claim();
    if (anciennes.length) {
      // Sans attendre la fin du rechargement : il passe par ce service worker, qui ne répond
      // qu'une fois son activation terminée. L'attendre ici bloquerait la page.
      const pages = await self.clients.matchAll({ type: 'window' });
      pages.forEach((p) => { p.navigate(p.url).catch(() => null); });
    }
  })());
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== self.location.origin) return;
  if (url.pathname.includes('/push/onesignal/')) return;
  e.respondWith(reseauDAbord(e, req));
});

async function reseauDAbord(e, req) {
  const cache = await caches.open(VERSION);
  const enCache = await cache.match(req, { ignoreSearch: true });
  const ecritures = [];
  // « no-cache » : le navigateur vérifie auprès du serveur que sa copie est encore la bonne.
  const reseau = fetch(req, { cache: 'no-cache' }).catch(() => fetch(req)).then((rep) => {
    if (rep.ok) ecritures.push(cache.put(req, rep.clone()));
    return rep;
  });
  // La copie locale est mise à jour même si la réponse arrive après le délai.
  e.waitUntil(reseau.then(() => Promise.all(ecritures)).catch(() => null));

  if (!enCache) {
    return reseau.catch(async () => (await cache.match('index.html')) || Response.error());
  }
  const delai = new Promise((resoudre) => { setTimeout(() => resoudre(enCache), DELAI_RESEAU_MS); });
  return Promise.race([reseau.catch(() => enCache), delai]);
}
