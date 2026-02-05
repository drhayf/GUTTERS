from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .admin.initialize import create_admin_interface
from .api import router
from .core.config import settings
from .core.setup import create_application, lifespan_factory
from .modules.infrastructure.push.listeners import register_listeners

admin = create_admin_interface()


@asynccontextmanager
async def lifespan_with_admin(app: FastAPI) -> AsyncGenerator[None, None]:
    """Custom lifespan that includes admin and event listener initialization."""
    # Get the default lifespan
    default_lifespan = lifespan_factory(settings)

    # Run the default lifespan initialization and our admin initialization
    async with default_lifespan(app):
        # Register push notification event listeners
        await register_listeners()

        # Initialize admin interface if it exists
        if admin:
            # Initialize admin database and setup
            await admin.initialize()

        # Initialize tracking data in background (non-blocking)
        # This ensures fresh data is available for users on first load
        from .core.startup import initialize_tracking_data
        import asyncio
        asyncio.create_task(initialize_tracking_data())

        yield


app = create_application(router=router, settings=settings, lifespan=lifespan_with_admin)

# Mount admin interface if enabled
if admin:
    app.mount(settings.CRUD_ADMIN_MOUNT_PATH, admin.app)

# --- Frontend Serving ---
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

# Mount static files if directory exists
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    # Mount assets directory directly at /assets to match index.html absolute paths
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Also serve vite.svg if it exists at root
    @app.get("/vite.svg", include_in_schema=False)
    async def get_vite_svg():
        return FileResponse(static_dir / "vite.svg")

    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Serve React SPA fallback for all other routes
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """Serve React SPA for non-api routes."""
    # Don't intercept API or docs routes
    if full_path.startswith(("api/", "admin/", "docs", "redoc", "openapi.json")):
        from fastapi import HTTPException

        raise HTTPException(status_code=404)

    candidate_file = static_dir / full_path
    if candidate_file.exists() and candidate_file.is_file():
        return FileResponse(candidate_file)

    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    # Optional: return a simple message if frontend isn't built
    return {"message": "GUTTERS Intelligence Layer - Frontend not yet synchronized."}
