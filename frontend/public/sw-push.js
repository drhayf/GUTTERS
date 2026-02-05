
// VAPID Web Push Handling
// This script is imported by the main Service Worker

// Handle incoming push event
self.addEventListener('push', (event) => {
    if (!event.data) {
        console.log('Push event but no data');
        return;
    }

    try {
        const data = event.data.json();
        const title = data.title || 'GUTTERS Update';
        const options = {
            body: data.body || 'New cosmic activity detected.',
            icon: '/pwa/manifest-icon-192.maskable.png', // Android/Desktop
            badge: '/pwa/manifest-icon-192.maskable.png', // Android/Small icon
            data: {
                url: data.url || '/'
            },
            // Cosmic Vibe: Dark theme preference if supported by OS, but limited control here
            image: data.image || '/pwa/manifest-icon-512.maskable.png',
            tag: 'gutters-notification',
            renotify: true,
            actions: [
                {
                    action: 'open',
                    title: 'Evolve'
                }
            ]
        };

        event.waitUntil(
            self.registration.showNotification(title, options)
        );
    } catch (e) {
        console.error('Error handling push event:', e);
    }
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const urlToOpen = event.notification.data?.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
            // Check if there is already a window for this app open and focus it.
            for (let i = 0; i < windowClients.length; i++) {
                const client = windowClients[i];
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }
            // If not, open a new window.
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});
