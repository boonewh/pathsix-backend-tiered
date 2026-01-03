# PathSix CRM - PWA Implementation Guide

**Target:** Convert existing React/Vue frontend into a Progressive Web App
**Timeline:** Phase 1 (Basic PWA): 4-8 hours | Phase 2 (Advanced): 1-2 days
**Backend Status:** ✅ Already PWA-ready (no backend changes needed)

---

## Table of Contents

1. [Why PWA for PathSix CRM](#why-pwa-for-pathsix-crm)
2. [Phase 1: Basic PWA (Launch-Ready)](#phase-1-basic-pwa-launch-ready)
3. [Phase 2: Advanced PWA (Post-Launch)](#phase-2-advanced-pwa-post-launch)
4. [Testing Checklist](#testing-checklist)
5. [Deployment Considerations](#deployment-considerations)

---

## Why PWA for PathSix CRM

### Business Benefits:
- **Mobile-first sales teams** - Add to home screen for instant access
- **Offline capability** - View clients/contacts without internet
- **No app store friction** - Deploy updates instantly, no approval wait
- **Lower development cost** - Single codebase for web + mobile
- **Better engagement** - PWA users engage 2-3x more than web users

### Technical Benefits:
- **Works with existing backend** - Your API is already compatible
- **Progressive enhancement** - Browser users aren't forced to install
- **Automatic updates** - Users always get latest version
- **Cross-platform** - Windows, Mac, Linux, iOS, Android from one codebase

---

## Phase 1: Basic PWA (Launch-Ready)

**Goal:** Make PathSix installable with basic offline support
**Time Estimate:** 4-8 hours
**Deliverables:** Manifest file, service worker, app icons, install prompt

### Step 1: Create Web App Manifest (30 min)

**File:** `public/manifest.json`

```json
{
  "name": "PathSix CRM",
  "short_name": "PathSix",
  "description": "Powerful CRM for sales teams with tiered pricing and offline support",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2563eb",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "categories": ["business", "productivity"],
  "screenshots": [
    {
      "src": "/screenshots/desktop-dashboard.png",
      "sizes": "1280x720",
      "type": "image/png",
      "form_factor": "wide"
    },
    {
      "src": "/screenshots/mobile-clients.png",
      "sizes": "750x1334",
      "type": "image/png",
      "form_factor": "narrow"
    }
  ]
}
```

**Customization Notes:**
- `theme_color`: Use your primary brand color
- `background_color`: Use your app's background color
- `icons`: Generate these in Step 2
- `screenshots`: Optional but improves install prompts (add later)

---

### Step 2: Generate App Icons (1 hour)

**Required Sizes:**
- 72x72, 96x96, 128x128, 144x144, 152x152, 192x192, 384x384, 512x512

**Tools:**
1. **Automated:** Use [PWA Asset Generator](https://github.com/onderceylan/pwa-asset-generator)
   ```bash
   npx pwa-asset-generator logo.svg public/icons --manifest public/manifest.json
   ```

2. **Manual:** Use [realfavicongenerator.net](https://realfavicongenerator.net/)
   - Upload your logo
   - Select "PWA" option
   - Download all sizes

3. **Design Tools:** Export from Figma/Sketch at each size

**Icon Guidelines:**
- Use solid background (not transparent)
- Ensure logo is centered with 10% padding
- Test on light and dark backgrounds
- Make sure text is readable at 72x72

**File Structure:**
```
public/
  icons/
    icon-72x72.png
    icon-96x96.png
    icon-128x128.png
    icon-144x144.png
    icon-152x152.png
    icon-192x192.png
    icon-384x384.png
    icon-512x512.png
```

---

### Step 3: Update index.html (15 min)

**File:** `public/index.html`

Add to `<head>`:

```html
<!-- PWA Manifest -->
<link rel="manifest" href="/manifest.json">

<!-- iOS Specific -->
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="PathSix">
<link rel="apple-touch-icon" href="/icons/icon-152x152.png">

<!-- Android/Chrome -->
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#2563eb">

<!-- Windows -->
<meta name="msapplication-TileColor" content="#2563eb">
<meta name="msapplication-TileImage" content="/icons/icon-144x144.png">
```

---

### Step 4: Create Service Worker (2 hours)

**File:** `public/service-worker.js`

```javascript
const CACHE_NAME = 'pathsix-v1.0.0';
const RUNTIME_CACHE = 'pathsix-runtime';

// Files to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  // Add your CSS/JS bundles here (Vite/Webpack generates these)
  // Example: '/assets/index-abc123.js'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[ServiceWorker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== RUNTIME_CACHE)
          .map((name) => {
            console.log('[ServiceWorker] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - network first, fallback to cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip chrome-extension and other schemes
  if (!url.protocol.startsWith('http')) return;

  // API requests: Network first, cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Only cache successful GET requests
          if (response.ok && request.method === 'GET') {
            const responseClone = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // Offline: return cached response if available
          return caches.match(request).then((cached) => {
            if (cached) {
              console.log('[ServiceWorker] Serving cached API response:', url.pathname);
              return cached;
            }
            // Return offline page or error response
            return new Response(
              JSON.stringify({ error: 'Offline. Please check your connection.' }),
              {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
              }
            );
          });
        })
    );
    return;
  }

  // Static assets: Cache first, network fallback
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) {
        console.log('[ServiceWorker] Serving from cache:', url.pathname);
        return cached;
      }

      return fetch(request).then((response) => {
        // Cache successful responses
        if (response.ok) {
          const responseClone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, responseClone);
          });
        }
        return response;
      });
    })
  );
});

// Listen for messages from main app
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
```

**Important Notes:**
- Update `CACHE_NAME` version on each deployment
- Add your actual JS/CSS bundle names to `STATIC_ASSETS`
- This provides basic offline support for viewing cached data

---

### Step 5: Register Service Worker in App (1 hour)

**For React Apps:**

**File:** `src/serviceWorkerRegistration.js`

```javascript
// Service Worker Registration
export function register() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      const swUrl = `${process.env.PUBLIC_URL}/service-worker.js`;

      navigator.serviceWorker
        .register(swUrl)
        .then((registration) => {
          console.log('ServiceWorker registered:', registration);

          // Check for updates every hour
          setInterval(() => {
            registration.update();
          }, 60 * 60 * 1000);

          // Handle updates
          registration.onupdatefound = () => {
            const installingWorker = registration.installing;
            if (installingWorker) {
              installingWorker.onstatechange = () => {
                if (installingWorker.state === 'installed') {
                  if (navigator.serviceWorker.controller) {
                    // New update available
                    console.log('New content available; please refresh.');

                    // Show update notification to user
                    showUpdateNotification(registration);
                  } else {
                    console.log('Content cached for offline use.');
                  }
                }
              };
            }
          };
        })
        .catch((error) => {
          console.error('ServiceWorker registration failed:', error);
        });
    });
  }
}

function showUpdateNotification(registration) {
  // Show a toast/banner to user
  const updateBanner = document.createElement('div');
  updateBanner.innerHTML = `
    <div style="position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
                background: #2563eb; color: white; padding: 12px 24px;
                border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 9999;">
      <span>New version available!</span>
      <button onclick="location.reload()" style="margin-left: 12px; background: white;
              color: #2563eb; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">
        Update
      </button>
    </div>
  `;
  document.body.appendChild(updateBanner);
}

export function unregister() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.unregister();
      })
      .catch((error) => {
        console.error(error.message);
      });
  }
}
```

**File:** `src/main.jsx` (or `src/index.jsx`)

```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Register service worker
serviceWorkerRegistration.register();
```

**For Vue Apps:**

**File:** `src/registerServiceWorker.js`

```javascript
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then((registration) => {
        console.log('ServiceWorker registered:', registration);
      })
      .catch((error) => {
        console.error('ServiceWorker registration failed:', error);
      });
  });
}
```

**File:** `src/main.js`

```javascript
import { createApp } from 'vue';
import App from './App.vue';
import './registerServiceWorker';

createApp(App).mount('#app');
```

---

### Step 6: Add Install Prompt UI (1-2 hours)

**File:** `src/components/InstallPrompt.jsx` (React) or `src/components/InstallPrompt.vue` (Vue)

**React Version:**

```jsx
import { useState, useEffect } from 'react';

export default function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      // Prevent the mini-infobar from appearing
      e.preventDefault();
      // Save the event so it can be triggered later
      setDeferredPrompt(e);
      // Show custom install prompt
      setShowPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handler);

    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    // Show the install prompt
    deferredPrompt.prompt();

    // Wait for the user's response
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`User response: ${outcome}`);

    // Clear the saved prompt
    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    // Remember user dismissed (optional - save to localStorage)
    localStorage.setItem('installPromptDismissed', Date.now());
  };

  // Don't show if already installed or user dismissed recently
  useEffect(() => {
    // Check if app is already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setShowPrompt(false);
    }

    // Check if user dismissed recently (within 7 days)
    const dismissed = localStorage.getItem('installPromptDismissed');
    if (dismissed && Date.now() - parseInt(dismissed) < 7 * 24 * 60 * 60 * 1000) {
      setShowPrompt(false);
    }
  }, []);

  if (!showPrompt) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-4 z-50">
      <div className="flex items-start gap-3">
        <img src="/icons/icon-72x72.png" alt="PathSix" className="w-12 h-12 rounded-lg" />
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
            Install PathSix CRM
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            Add to your home screen for quick access and offline support
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleInstall}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition"
            >
              Install
            </button>
            <button
              onClick={handleDismiss}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-md transition"
            >
              Not now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

**Usage in App:**

```jsx
import InstallPrompt from './components/InstallPrompt';

function App() {
  return (
    <>
      <YourAppContent />
      <InstallPrompt />
    </>
  );
}
```

---

### Step 7: Test Basic PWA (1 hour)

**Desktop Chrome:**
1. Open DevTools → Application tab
2. Check "Manifest" - Should show PathSix details
3. Check "Service Workers" - Should show registered worker
4. Click install icon in address bar (⊕)
5. Verify app opens in standalone window

**Mobile (Real Device):**
1. Visit your app in Chrome/Safari
2. Look for "Add to Home Screen" prompt
3. Add to home screen
4. Open from home screen icon
5. Verify full-screen mode (no browser UI)

**Lighthouse Audit:**
1. DevTools → Lighthouse tab
2. Select "Progressive Web App"
3. Run audit
4. Target score: 90+ (100 is ideal)

**Common Issues:**
- Icons not showing? Check file paths in manifest.json
- Install prompt not appearing? Must be HTTPS (or localhost)
- Service worker not registering? Check browser console for errors

---

### Phase 1 Checklist

- [ ] `manifest.json` created with all metadata
- [ ] App icons generated (all 8 sizes)
- [ ] `index.html` updated with PWA meta tags
- [ ] Service worker created with basic caching
- [ ] Service worker registered in app entry point
- [ ] Install prompt component created
- [ ] Tested on Chrome desktop (install works)
- [ ] Tested on mobile device (add to home screen works)
- [ ] Lighthouse PWA score 90+
- [ ] Offline mode tested (cached pages load)

**Deliverables for Phase 1:**
✅ Users can install PathSix as an app
✅ Basic offline support (view cached pages)
✅ App works in browser AND as installed app
✅ Ready for production launch

---

## Phase 2: Advanced PWA (Post-Launch)

**Goal:** Add sophisticated offline features and push notifications
**Time Estimate:** 1-2 days
**When:** After launch, based on user feedback

### Feature 1: Offline Data Storage (4-6 hours)

**Goal:** Cache client/contact/lead data for offline viewing

**Technology:** IndexedDB (use [Dexie.js](https://dexie.org/) wrapper)

**Install:**
```bash
npm install dexie
```

**File:** `src/utils/db.js`

```javascript
import Dexie from 'dexie';

export const db = new Dexie('PathSixCRM');

// Define database schema
db.version(1).stores({
  clients: '++id, tenant_id, name, email, created_at',
  contacts: '++id, tenant_id, client_id, name, email',
  leads: '++id, tenant_id, status, source, created_at',
  projects: '++id, tenant_id, client_id, name, status',
  syncQueue: '++id, endpoint, method, data, timestamp'
});

// Sync data from API to IndexedDB
export async function syncClients() {
  try {
    const response = await fetch('/api/clients', {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    const clients = await response.json();

    // Clear old data and insert new
    await db.clients.clear();
    await db.clients.bulkAdd(clients);

    console.log('Clients synced to local database');
  } catch (error) {
    console.error('Sync failed:', error);
  }
}

// Get token from localStorage/sessionStorage
function getToken() {
  return localStorage.getItem('authToken');
}

// Export functions for other entities
export async function syncContacts() { /* Similar to syncClients */ }
export async function syncLeads() { /* Similar to syncClients */ }
```

**File:** `src/hooks/useOfflineData.js`

```javascript
import { useState, useEffect } from 'react';
import { db, syncClients } from '../utils/db';

export function useOfflineClients() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  useEffect(() => {
    const loadClients = async () => {
      try {
        if (navigator.onLine) {
          // Online: fetch from API and sync to IndexedDB
          await syncClients();
        }

        // Load from IndexedDB (works offline too)
        const localClients = await db.clients.toArray();
        setClients(localClients);
      } catch (error) {
        console.error('Failed to load clients:', error);
      } finally {
        setLoading(false);
      }
    };

    loadClients();

    // Listen for online/offline events
    const handleOnline = () => {
      setIsOffline(false);
      syncClients(); // Sync when back online
    };
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return { clients, loading, isOffline };
}
```

**Usage:**

```jsx
function ClientsList() {
  const { clients, loading, isOffline } = useOfflineClients();

  return (
    <div>
      {isOffline && (
        <div className="bg-yellow-100 border-yellow-400 text-yellow-800 px-4 py-2">
          You're offline. Showing cached data.
        </div>
      )}

      {loading ? <Spinner /> : (
        <ul>
          {clients.map(client => (
            <li key={client.id}>{client.name}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

---

### Feature 2: Background Sync (3-4 hours)

**Goal:** Queue up creates/updates when offline, sync when online

**File:** Update `public/service-worker.js`

```javascript
// Add to existing service-worker.js

// Background sync event
self.addEventListener('sync', (event) => {
  console.log('[ServiceWorker] Background sync triggered:', event.tag);

  if (event.tag === 'sync-offline-changes') {
    event.waitUntil(syncOfflineChanges());
  }
});

async function syncOfflineChanges() {
  // Get pending changes from IndexedDB
  const db = await openDB();
  const queue = await db.getAll('syncQueue');

  console.log(`[ServiceWorker] Syncing ${queue.length} offline changes`);

  for (const item of queue) {
    try {
      const response = await fetch(item.endpoint, {
        method: item.method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': item.token
        },
        body: JSON.stringify(item.data)
      });

      if (response.ok) {
        // Remove from queue on success
        await db.delete('syncQueue', item.id);
        console.log('[ServiceWorker] Synced:', item.endpoint);
      }
    } catch (error) {
      console.error('[ServiceWorker] Sync failed for:', item.endpoint, error);
      // Keep in queue to retry later
    }
  }
}

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('PathSixCRM', 1);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
```

**File:** `src/utils/offlineSync.js`

```javascript
import { db } from './db';

export async function createClientOffline(clientData) {
  // Add to local database immediately
  const localId = await db.clients.add({
    ...clientData,
    _pendingSync: true,
    _localId: Date.now()
  });

  // Queue for background sync
  await db.syncQueue.add({
    endpoint: '/api/clients',
    method: 'POST',
    data: clientData,
    token: localStorage.getItem('authToken'),
    timestamp: Date.now()
  });

  // Request background sync
  if ('serviceWorker' in navigator && 'sync' in navigator.serviceWorker) {
    const registration = await navigator.serviceWorker.ready;
    await registration.sync.register('sync-offline-changes');
  }

  return localId;
}
```

---

### Feature 3: Push Notifications (4-6 hours)

**Goal:** Notify users about new leads, reminders, team messages

**Backend Required:** You'll need to add push subscription storage

**Step 3A: Update Backend** (30 min)

Add to your backend:

**File:** `app/models.py`

```python
# Add to existing models.py

class PushSubscription(Base):
    __tablename__ = 'push_subscriptions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    endpoint = Column(String, nullable=False)
    p256dh_key = Column(String, nullable=False)
    auth_key = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', backref='push_subscriptions')
```

**File:** `app/routes/push.py` (new file)

```python
from quart import Blueprint, request, jsonify
from app.utils.auth_utils import requires_auth
from app.models import PushSubscription
from app.database import SessionLocal

push_bp = Blueprint('push', __name__)

@push_bp.route('/api/push/subscribe', methods=['POST'])
@requires_auth()
async def subscribe_push(user):
    """Save push notification subscription"""
    data = await request.json

    session = SessionLocal()
    try:
        subscription = PushSubscription(
            user_id=user.id,
            tenant_id=user.tenant_id,
            endpoint=data['endpoint'],
            p256dh_key=data['keys']['p256dh'],
            auth_key=data['keys']['auth']
        )
        session.add(subscription)
        session.commit()

        return jsonify({"message": "Subscription saved"}), 200
    finally:
        session.close()

@push_bp.route('/api/push/unsubscribe', methods=['POST'])
@requires_auth()
async def unsubscribe_push(user):
    """Remove push notification subscription"""
    data = await request.json

    session = SessionLocal()
    try:
        session.query(PushSubscription).filter_by(
            user_id=user.id,
            endpoint=data['endpoint']
        ).delete()
        session.commit()

        return jsonify({"message": "Unsubscribed"}), 200
    finally:
        session.close()
```

**Step 3B: Frontend Push Setup** (2-3 hours)

**File:** `src/utils/pushNotifications.js`

```javascript
// Public VAPID key (generate with web-push library on backend)
const VAPID_PUBLIC_KEY = 'YOUR_VAPID_PUBLIC_KEY_HERE';

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export async function subscribeToPush() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    console.warn('Push notifications not supported');
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.ready;

    // Request notification permission
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      console.log('Notification permission denied');
      return null;
    }

    // Subscribe to push
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
    });

    // Send subscription to backend
    await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      },
      body: JSON.stringify(subscription)
    });

    console.log('Push subscription successful');
    return subscription;
  } catch (error) {
    console.error('Failed to subscribe to push:', error);
    return null;
  }
}

export async function unsubscribeFromPush() {
  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.getSubscription();

  if (subscription) {
    await subscription.unsubscribe();

    // Notify backend
    await fetch('/api/push/unsubscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      },
      body: JSON.stringify(subscription)
    });
  }
}
```

**File:** Update `public/service-worker.js`

```javascript
// Add to existing service-worker.js

// Listen for push events
self.addEventListener('push', (event) => {
  console.log('[ServiceWorker] Push received');

  const data = event.data ? event.data.json() : {};
  const title = data.title || 'PathSix CRM';
  const options = {
    body: data.body || 'You have a new notification',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    data: data.url || '/',
    vibrate: [200, 100, 200],
    tag: data.tag || 'default'
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('[ServiceWorker] Notification clicked');

  event.notification.close();

  // Open the app or focus existing window
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Focus existing window if open
        for (const client of clientList) {
          if (client.url === event.notification.data && 'focus' in client) {
            return client.focus();
          }
        }
        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(event.notification.data);
        }
      })
  );
});
```

**Usage in App:**

```jsx
import { subscribeToPush } from './utils/pushNotifications';

function NotificationSettings() {
  const [subscribed, setSubscribed] = useState(false);

  const handleEnable = async () => {
    const subscription = await subscribeToPush();
    if (subscription) {
      setSubscribed(true);
    }
  };

  return (
    <button onClick={handleEnable}>
      {subscribed ? 'Notifications Enabled' : 'Enable Notifications'}
    </button>
  );
}
```

---

### Phase 2 Checklist

- [ ] IndexedDB setup with Dexie
- [ ] Offline data caching for clients/leads/contacts
- [ ] Background sync for offline changes
- [ ] Push notification backend endpoints
- [ ] Push notification frontend subscription
- [ ] Service worker push event handlers
- [ ] Notification settings UI
- [ ] Test offline create/edit → online sync
- [ ] Test push notifications on real device

---

## Testing Checklist

### Desktop Testing

**Chrome:**
- [ ] Install app from address bar
- [ ] App opens in standalone window
- [ ] Offline mode works (disconnect network)
- [ ] Service worker updates on new deployment
- [ ] Lighthouse PWA score 90+

**Edge:**
- [ ] Install app from menu
- [ ] Verify same functionality as Chrome

**Firefox:**
- [ ] Service worker works
- [ ] Manifest recognized
- [ ] (Note: Install prompt limited on Firefox)

### Mobile Testing

**iOS (Safari):**
- [ ] "Add to Home Screen" from share menu
- [ ] App icon appears on home screen
- [ ] Opens in full-screen
- [ ] Service worker registers
- [ ] Offline caching works
- [ ] (Note: Push notifications only work when installed)

**Android (Chrome):**
- [ ] Install banner appears
- [ ] Install from menu works
- [ ] App drawer icon appears
- [ ] Push notifications work
- [ ] Background sync works

### Offline Testing

- [ ] Disconnect network
- [ ] Navigate to cached pages (should load)
- [ ] Try to create record (should queue)
- [ ] Reconnect network
- [ ] Verify queued changes sync automatically
- [ ] Check IndexedDB in DevTools

### Performance Testing

- [ ] First load < 3 seconds
- [ ] Subsequent loads < 1 second (cached)
- [ ] Lighthouse Performance score 90+
- [ ] Bundle size reasonable (< 500KB gzipped)

---

## Deployment Considerations

### Build Configuration

**Vite (recommended):**

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icons/*.png'],
      manifest: {
        // Will merge with public/manifest.json
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.pathsix\.com\/api\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 // 24 hours
              }
            }
          }
        ]
      }
    })
  ]
});
```

**Webpack:**

Use [Workbox Webpack Plugin](https://developers.google.com/web/tools/workbox/modules/workbox-webpack-plugin)

### HTTPS Requirement

PWAs **require HTTPS** (except localhost). Your deployment must have SSL:

- **Backend:** Already planned for production
- **Frontend:** Vercel/Netlify/Cloudflare Pages provide free SSL
- **Custom Domain:** Use Let's Encrypt (free) or Cloudflare

### Cache Versioning

**Important:** Update cache version on each deployment!

```javascript
// In service-worker.js
const CACHE_NAME = 'pathsix-v1.0.1'; // Increment on each deploy

// In package.json, add script:
{
  "scripts": {
    "prebuild": "node scripts/update-sw-version.js"
  }
}
```

**File:** `scripts/update-sw-version.js`

```javascript
const fs = require('fs');
const path = require('path');

const swPath = path.join(__dirname, '../public/service-worker.js');
let content = fs.readFileSync(swPath, 'utf8');

const version = require('../package.json').version;
content = content.replace(
  /const CACHE_NAME = 'pathsix-v[\d.]+'/,
  `const CACHE_NAME = 'pathsix-v${version}'`
);

fs.writeFileSync(swPath, content);
console.log(`Updated service worker cache version to v${version}`);
```

### Update Strategy

**Options:**

1. **Auto-update (Recommended for Phase 1):**
   - Service worker updates silently
   - Show "Update available" banner
   - User clicks to refresh

2. **Prompt on critical updates:**
   - Check version on app load
   - Force reload if breaking changes

```javascript
// Check for updates on app mount
useEffect(() => {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then((registration) => {
      registration.update();
    });
  }
}, []);
```

---

## Performance Best Practices

### Minimize Bundle Size

```bash
# Analyze bundle
npm run build
npx vite-bundle-analyzer

# Code splitting
import { lazy, Suspense } from 'react';
const ClientsPage = lazy(() => import('./pages/Clients'));

# Tree shaking (automatic with Vite/Webpack)
```

### Optimize Images

- Use WebP format for icons (with PNG fallback)
- Compress with [Squoosh](https://squoosh.app/)
- Lazy load images below fold

### Preload Critical Assets

```html
<!-- In index.html -->
<link rel="preload" href="/fonts/inter.woff2" as="font" crossorigin>
<link rel="preload" href="/api/billing/usage" as="fetch" crossorigin>
```

---

## Common Pitfalls & Solutions

### Issue 1: Install Prompt Not Showing

**Causes:**
- Not HTTPS (use localhost for dev)
- Missing manifest.json
- Service worker not registered
- User already dismissed

**Solution:**
```javascript
// Check in DevTools → Application → Manifest
// Check for errors in console
// Test with: chrome://flags/#bypass-app-banner-engagement-checks
```

### Issue 2: Service Worker Not Updating

**Causes:**
- Cache name not changed
- Browser cache aggressive

**Solution:**
```javascript
// Force update in dev:
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(r => r.unregister());
});

// In production: Change CACHE_NAME on every deploy
```

### Issue 3: CORS Errors for API

**Causes:**
- Backend not allowing credentials
- Service worker fetching without auth

**Solution:**
```python
# Backend (already done in your setup)
app.config['CORS_SUPPORTS_CREDENTIALS'] = True

# Frontend service worker
fetch(request, {
  credentials: 'include'
})
```

### Issue 4: iOS Safari Issues

**Known Limitations:**
- Push notifications only when installed
- Limited storage quota
- No background sync

**Workarounds:**
- Check if standalone: `window.navigator.standalone`
- Provide iOS-specific instructions
- Poll for updates instead of background sync

---

## Resources

### Official Docs:
- [MDN PWA Guide](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
- [web.dev PWA Training](https://web.dev/progressive-web-apps/)
- [Workbox (Google)](https://developers.google.com/web/tools/workbox)

### Tools:
- [PWA Builder](https://www.pwabuilder.com/) - Generate assets
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) - Audit tool
- [Web Push Book](https://web-push-book.gauntface.com/) - Push notifications

### Testing:
- [Chrome DevTools Application Tab](https://developers.google.com/web/tools/chrome-devtools/progressive-web-apps)
- [ngrok](https://ngrok.com/) - Test HTTPS locally
- [BrowserStack](https://www.browserstack.com/) - Test on real devices

---

## Summary

### Phase 1 Delivers:
✅ Installable PWA on all platforms
✅ Basic offline support (cached pages)
✅ Professional app experience
✅ Production-ready in 4-8 hours

### Phase 2 Adds:
🚀 Advanced offline data caching
🚀 Background sync for offline changes
🚀 Push notifications
🚀 Near-native app experience

### Backend Requirements:
- ✅ No changes needed for Phase 1
- ⚠️ Push notification endpoints for Phase 2 (optional)
- ✅ HTTPS in production (already planned)

### Your Competitive Advantage:
- **Faster time-to-market** vs native app development
- **Lower cost** (no app store fees)
- **Better UX** (install optional, not required)
- **Instant updates** (no approval delays)

---

**Questions? Issues?**
- Check browser console for errors
- Use Lighthouse audit to identify problems
- Test on real devices early

**Ready to start?** Begin with Phase 1, Step 1 (manifest.json) and work through sequentially. Each step builds on the previous one.

Good luck! 🚀