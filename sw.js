// Service Worker aggiornato per Todis Volley App
const CACHE_NAME = 'todis-volley-v2';

const urlsToCache = [
  './',
  'index.html',
  'maschile.html',
  'femminile.html',
  'generale.html',
  'segnapunti.html',
  'manifest.json',
  'logo.jpg',
  'scelta_campionato.jpg',
  'all_result.png',
  'todis_result.png',
  'tabellone_segnapunti.png'
];

// Installazione: Caching risorse statiche
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch: Strategia Network First (Cerca online, se fallisce usa la cache)
// Questo garantisce che gli utenti vedano sempre i risultati aggiornati se hanno internet
self.addEventListener('fetch', function(event) {
  event.respondWith(
    fetch(event.request)
      .then(function(response) {
        // Se la risposta è valida, la cloniamo nella cache per il futuro
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        var responseToCache = response.clone();
        caches.open(CACHE_NAME)
          .then(function(cache) {
            cache.put(event.request, responseToCache);
          });
        return response;
      })
      .catch(function() {
        // Se siamo offline, cerchiamo nella cache
        return caches.match(event.request);
      })
  );
});

// Attivazione: Pulizia vecchie cache (Importante per aggiornare dalla v1 alla v2)
self.addEventListener('activate', function(event) {
  var cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
