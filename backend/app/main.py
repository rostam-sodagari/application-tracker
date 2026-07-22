from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import config, db
from .auth import require_auth
from .config import FRONTEND_DIST
from .routers import applications, cvs, home, meta, public_config, settings

app = FastAPI(title="Application Tracker")

db.init_db()

# Unauthenticated: the frontend needs this before a user has logged in at all.
app.include_router(public_config.router)

# Local mode hosts its own registration, login, and logout endpoints. Appwrite mode does not,
# since the frontend registers and logs in directly against Appwrite's own account service.
if config.BACKEND_MODE == "local":
    from .auth_providers.local_auth import router as local_auth_router

    app.include_router(local_auth_router)

# Every route below requires a valid session, verified by whichever backend is active.
protected = [Depends(require_auth)]
app.include_router(applications.router, dependencies=protected)
app.include_router(cvs.router, dependencies=protected)
app.include_router(home.router, dependencies=protected)
app.include_router(meta.router, dependencies=protected)
app.include_router(settings.router, dependencies=protected)

# The built React app (frontend/dist, produced by `npm run build`) is served last so it never
# shadows the /api/* routes above. Falls back to index.html for any other path so client-side
# routing (for example a hard refresh on /cvs) keeps working. The SPA shell itself is static
# JavaScript and HTML with no data in it, so it is fine to serve without auth; the login form
# lives inside it.
if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    index = FRONTEND_DIST / "index.html"
    if not index.exists():
        raise HTTPException(
            status_code=404,
            detail="frontend/dist not built yet, run `npm install && npm run build` in dashboard/frontend/",
        )
    return FileResponse(index)
