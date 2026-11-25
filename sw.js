/* ==========================================================================
   OneSignal Push Notifications
   ========================================================================== */
importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js");

/* ==========================================================================
   Configuration
   ========================================================================== */
const CACHE_NAME = "todis-volley-offline-v7";

const ASSETS_TO_CACHE = [
    "./",
    "index.html",
    "maschile.html",
    "femminile.html",
    "generale_m.html",
    "generale_f.html",
    "segnapunti.html",
    "media.html",
    "manifest.json",
    "logo.jpg",
    "new_landing_page.jpg",
    "Sunday.png",
    "Sunday_Male.png",
    "Sunday_Female.png",
    "all_result.png",
    "todis_result.png",
    "tabellone_segnapunti.png",
    "prossimi_appuntamenti.png"
];

/* ==========================================================================
   Install
   ========================================================================== */
self.addEventListener("install", (event) => {

    self.skipWaiting();

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log("[SW] Caching application assets");
                return cache.addAll(ASSETS_TO_CACHE);
            })
    );

});

/* ==========================================================================
   Activate
   ========================================================================== */
self.addEventListener("activate", (event) => {

    event.waitUntil(
        caches.keys().then((keys) => {

            return Promise.all(
                keys.map((key) => {

                    if (key !== CACHE_NAME) {
                        console.log("[SW] Removing old cache:", key);
                        return caches.delete(key);
                    }

                })
            );

        })
    );

    self.clients.claim();

});

/* ==========================================================================
   Fetch
   Cache ONLY local application resources
   ========================================================================== */
self.addEventListener("fetch", (event) => {

    const requestUrl = new URL(event.request.url);

    // Ignora richieste non GET
    if (event.request.method !== "GET") {
        return;
    }

    // Ignora chrome-extension://
    if (
        requestUrl.protocol !== "http:" &&
        requestUrl.protocol !== "https:"
    ) {
        return;
    }

    // Ignora tutto ciò che non appartiene al sito
    if (requestUrl.origin !== self.location.origin) {
        return;
    }

    event.respondWith(

        fetch(event.request)

            .then((response) => {

                if (
                    !response ||
                    response.status !== 200
                ) {
                    return response;
                }

                const responseToCache = response.clone();

                caches.open(CACHE_NAME)
                    .then((cache) => {

                        cache.put(
                            event.request,
                            responseToCache
                        );

                    })
                    .catch((err) => {
                        console.warn(
                            "[SW] Cache put failed",
                            err
                        );
                    });

                return response;

            })

            .catch(async () => {

                const cachedResponse =
                    await caches.match(event.request);

                if (cachedResponse) {
                    return cachedResponse;
                }

                // fallback pagina principale
                return caches.match("index.html");

            })

    );

});
