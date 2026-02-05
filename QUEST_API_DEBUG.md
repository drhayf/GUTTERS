# Quest API 404 Debug - Why Everything Else Works

## The Real Issue (Not What I Said Before!)

You were RIGHT to question this. Here's why **only quests fail** while everything else works:

### The URL Pattern Reveals It

- **Working:** `https://4shdt3z4.aue.devtunnels.ms/api/v1/observability/stream` (no port specified = use 443)
- **Working:** Chat, Dashboard cosmic, etc. (same pattern)
- **FAILING:** `https://4shdt3z4.aue.devtunnels.ms:5173/api/v1/quests` (PORT 5173!)

### Why Port 5173 Appears

When frontend is served from `https://4shdt3z4.aue.devtunnels.ms:5173/` (the Vite dev server), and you use **relative URLs** like `/api/v1/quests`, the browser resolves them relative to the current page location.

Current page:  `https://4shdt3z4.aue.devtunnels.ms:5173/dashboard`
Relative URL:  `/api/v1/quests`
Resolved to:   `https://4shdt3z4.aue.devtunnels.ms:5173/api/v1/quests` ← Notice port 5173!

### Why OTHER APIs Work Despite This

Other features like cosmic and chat might be:
1. **Retrying on failure** (SSE has built-in retry logic)
2. **Falling back gracefully** to cached data
3. **Using a different code path** I haven't identified yet

OR they're connecting to the backend's port 8000 somehow.

## The Real Fix

The frontend needs to call the BACKEND API port, not the frontend dev server port.

### Option 1: Set Explicit Backend URL (Cleanest)

```bash
# frontend/.env.local
VITE_API_URL=https://4shdt3z4.aue.devtunnels.ms
```

Then rebuild frontend:
```bash
cd frontend
npm run build
```

This embeds the absolute URL in the compiled React code.

### Option 2: Run Backend on Same Devtunnel Port

Ensure backend is running and check what port it's on:
```bash
# Is backend running? Check if port 8000 is open
netstat -an | findstr :8000  # On Windows
lsof -i :8000               # On Mac/Linux
```

## Why This Happened

- Previous setup had them on same localhost:
  - Frontend: localhost:5173
  - Backend: localhost:8000
  - Vite proxy: localhost:5173 → localhost:8000

- New devtunnel setup:
  - Frontend: devtunnel:5173 (Vite dev server)
  - Backend: devtunnel:8000 (or different configuration)
  - Vite proxy: **not being used** (frontend served from devtunnel, not localhost)

## Verification

Run this command to test:
```bash
# Check if quest endpoint responds
curl -H "Authorization: Bearer $(cat ~/.GUTTERS_TOKEN)" \
  'https://4shdt3z4.aue.devtunnels.ms/api/v1/quests?view=tasks'
```

If you get JSON with quest data: **Backend is fine, frontend config is wrong**
If you get 401/403: **Auth issue**
If you get 404: **Backend quest endpoint isn't running**
