from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import get_settings
from .db import init_db
from .routers import assistant, auth, tracking

VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title="Bloomery", version=VERSION, lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.add_middleware(
        SessionMiddleware, secret_key=s.resolved_secret(), session_cookie="bloomery_session",
        max_age=s.session_max_age_days * 86400, same_site="lax", https_only=s.secure_cookies)
    for r in (auth.router, tracking.router, assistant.router):
        app.include_router(r)

    @app.get("/api/health")
    def health():
        return {"ok": True, "version": VERSION}

    static: Path = s.static_dir
    if (static / "index.html").exists():
        if (static / "assets").exists():
            app.mount("/assets", StaticFiles(directory=static / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str):
            if path.startswith("api/"):
                raise HTTPException(404)
            f = (static / path).resolve()
            if path and f.is_file() and static.resolve() in f.parents:
                return FileResponse(f)
            return FileResponse(static / "index.html", headers={"Cache-Control": "no-cache"})

    return app


app = create_app()
