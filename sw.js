const CACHE_NAME = 'todis-volley-offline-v5'; // Cambio nome per forzare l'aggiornamento su tutti i telefoni

// Elenco COMPLETO di tutto ciò che serve all'app per funzionare senza internet
const ASSETS_TO_CACHE = [
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
  'tabellone_segnapunti.png',
  'prossimi_appuntamenti.png'
];

// 1. INSTALLAZIONE: Scarica subito tutto nella pancia del telefono
self.addEventListener('install', (event) => {
  self.skipWaiting(); // Forza l'attivazione immediata
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Caching all assets');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

// 2. ATTIVAZIONE: Cancella le vecchie versioni per risparmiare spazio
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (key !== CACHE_NAME) {
          console.log('[Service Worker] Removing old cache', key);
          return caches.delete(key);
        }
      }));
    })
  );
  self.clients.claim();
});

// 3. RECUPERO DATI (FETCH): Strategia "Network First, falling back to Cache"
self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Se la rete funziona, restituisci il dato fresco E aggiorna la cache
        if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
        }
        const responseToCache = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });
        return response;
      })
      .catch(() => {
        // Se la rete fallisce (OFFLINE), restituisci la versione salvata
        console.log('[Service Worker] Network failed, serving from cache');
        return caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                return cachedResponse;
            }
            // Se non c'è nemmeno in cache (caso raro se installato bene), mostra error o index
            // Qui potremmo reindirizzare alla home se una pagina specifica manca
            return caches.match('index.html'); 
        });
      })
  );
});
