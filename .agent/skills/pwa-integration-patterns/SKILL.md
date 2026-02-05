---
name: pwa-integration-patterns
description: Patterns for synchronizing Vite/React frontends with FastAPI backends. Use when building or deploying the GUTTERS PWA.
---

# PWA Integration Patterns

Guides the high-fidelity synchronization between the React Intelligence Layer and the FastAPI Core.

## When to Use

- Initializing `frontend/` directory in a GUTTERS project.
- Fixing "Blank Page" or 404 issues in production builds.
- Implementing Auth/JWT logic in React components.
- Connecting to remote Redis Cloud instances.

## Core Implementation

### 1. Vite Build Configuration
Vite assets must use absolute paths for predictable FastAPI mounting.

```typescript
// frontend/vite.config.ts
export default defineConfig({
  build: {
    outDir: '../src/app/static',
    emptyOutDir: true,
  }
  // server proxy for local development
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/auth': 'http://localhost:8000'
    }
  }
})
```

### 2. FastAPI Static Mounting & SPA Fallback
FastAPI must serve build assets and handle client-side routing.

```python
# src/app/main.py
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    # MUST mount specific asset dirs to match absolute index.html paths
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    # Fallback to index.html for React Router
    if full_path.startswith(("api/", "admin/", "docs")):
        raise HTTPException(status_code=404)
    return FileResponse(static_dir / "index.html")
```

### 3. JWT Handling Pattern
Use Axios interceptors for seamless token refresh.

```typescript
// frontend/src/lib/api.ts
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401 && !err.config._retry) {
      err.config._retry = true;
      // hit /api/v1/refresh (withCredentials: true for cookie)
      // update localStorage['access_token']
      return api(err.config);
    }
    return Promise.reject(err);
  }
);
```

## Gotchas

- **Redis Auth**: Remote Redis (like Redis Cloud) MUST have the password passed in `RedisSettings(..., password=settings.REDIS_PASSWORD)`.
- **Absolute Paths**: If `index.html` has `<script src="/assets/..." />`, FastAPI must mount `/assets`. Mounting `/static` is NOT enough.
- **Form Data**: OAuth2 login routes (`/api/v1/login`) expect `application/x-www-form-urlencoded`, not JSON.

## Critical Checklist

- [ ] Vite `outDir` points to `src/app/static`.
- [ ] FastAPI mounts `/assets` directory.
- [ ] SPA fallback exclude `/api`, `/admin`, and `/docs`.
- [ ] `useKeyboardHeight` hook used in mobile chat views.
