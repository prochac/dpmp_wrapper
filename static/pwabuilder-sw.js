//This is the service worker with the combined offline experience (Offline page + Offline copy of pages)

//Install stage sets up the offline page in the cahche and opens a new cache

CACHED = [
    '/offline',
    '/sms-ticket',
    '/static/mini-default.min.css',
    '/static/css.css',
    '/static/material-icons-styles.css',
    '/static/material-icons.woff2',
    '/static/logo.png',
];

self.addEventListener('install', function (event) {
    event.waitUntil(preLoad());
});

var preLoad = function () {
    console.log('[PWA Builder] Install Event processing');
    return caches.open('pwabuilder-offline').then(function (cache) {
        console.log('[PWA Builder] Cached index and offline page during Install');
        return cache.addAll(CACHED);
    });
};

self.addEventListener('fetch', function (event) {
    console.log('The service worker is serving the asset.');
    event.respondWith(checkResponse(event.request).catch(function () {
            return returnFromCache(event.request)
        }
    ));
});

//This is a event that can be fired from your page to tell the SW to update the offline page
self.addEventListener('refreshOffline', function (response) {
    return caches.open('pwabuilder-offline').then(function (cache) {
        console.log('[PWA Builder] Offline page updated from refreshOffline event: ' + response.url);
        return cache.addAll(CACHED);
    });
});

var checkResponse = function (request) {
    return new Promise(function (fulfill, reject) {
        fetch(request).then(function (response) {
            if (response.status !== 404) {
                fulfill(response)
            } else {
                reject()
            }
        }, reject)
    });
};

var addToCache = function (request) {
    return caches.open('pwabuilder-offline').then(function (cache) {
        return fetch(request).then(function (response) {
            console.log('[PWA Builder] add page to offline' + response.url);
            return cache.put(request, response);
        });
    });
};

var returnFromCache = function (request) {
    return caches.open('pwabuilder-offline').then(function (cache) {
        return cache.match(request).then(function (matching) {
            if (!matching || matching.status == 404) {
                return cache.match('offline')
            } else {
                return matching
            }
        });
    });
};