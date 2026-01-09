// Service Worker per Todis Volley App (V3)
const CACHE_NAME = 'todis-volley-v3'; // Cambiato nome per forzare update

const urlsToCache = [
  './',
  'index.html',
  'maschile.html',
  'femminile.html',
  'generale_m.html',
  'generale_f.html',
  'segnapunti.html',
  'manifest.json',
  'logo.jpg',
  'scelta_campionato.jpg',
  'all_result.png',
  'todis_result.png',
  'tabellone_segnapunti.png'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    fetch(event.request)
      .then(function(response) {
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
        return caches.match(event.request);
      })
  );
});

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
