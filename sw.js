// Service Worker per rendere l'app installabile
const CACHE_NAME = 'todis-volley-v1';
const urlsToCache = [
  './',
  'index.html',
  'generale.html',
  'segnapunti.html',
  'manifest.json',
  'logo.jpg' // Assicurati che questo nome corrisponda al tuo file su GitHub
];

// Installazione: Caching risorse statiche
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch: Strategia Network First (Cerca online, se non va usa la cache)
// Questo assicura che tu veda sempre i risultati aggiornati!
self.addEventListener('fetch', function(event) {
  event.respondWith(
    fetch(event.request).catch(function() {
      return caches.match(event.request);
    })
  );
});