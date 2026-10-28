// 1. Importa il motore di OneSignal per le notifiche Push
importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js");

const CACHE_NAME = 'todis-volley-offline-v6'; // Passato a v6 per forzare l'aggiornamento

// Elenco COMPLETO e AGGIORNATO dei file necessari
const ASSETS_TO_CACHE = [
  './',
  'index.html',
  'maschile.html',
  'femminile.html',
  'generale_m.html',
  'generale_f.html',
  'segnapunti.html',
  'media.html',          // NUOVA PAGINA
  'manifest.json',
  'logo.jpg',
  'new_landing_page.jpg', // NUOVA IMMAGINE
  'Sunday.png',
  'Sunday_Male.png',
  'Sunday_Female.png',
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
            // Fallback se manca un file
            return caches.match('index.html'); 
        });
      })
  );
});
