"""Backup & restore API (server owner only): schedule, run now, download, restore, Google Drive connect."""

from __future__ import annotations

import secrets
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field

from .. import backup
from ..deps import SessionDep, UserDep
from ..i18n import _
from .assistant import require_admin

router = APIRouter(prefix="/api/backups", tags=["backups"])


def _public(cfg: dict[str, Any]) -> dict[str, Any]:
    g = cfg["gdrive"]
    return {
        **{k: cfg[k] for k in ("enabled", "time", "tz", "keep", "last", "last_ok", "last_error")},
        "encrypted": bool(cfg["passphrase"]),
        "gdrive": {
            "client_id": g["client_id"],
            "has_secret": bool(g["client_secret"]),
            "connected": backup.drive_connected(cfg),
        },
    }


@router.get("")
async def overview(user: UserDep, db: SessionDep):
    require_admin(user, db)
    cfg = backup.load(db)
    cloud: list[dict[str, Any]] | None = None
    cloud_error = ""
    if backup.drive_connected(cfg):
        known_folder = cfg["gdrive"]["folder_id"]
        try:
            async with httpx.AsyncClient(timeout=20) as c, backup.Drive(cfg["gdrive"], c) as d:
                cloud = await d.list()
            if cfg["gdrive"]["folder_id"] != known_folder:  # Drive() fills it in on first use
                backup.store(db, cfg)
        except (backup.BackupError, httpx.HTTPError) as e:
            cloud_error = str(e) or type(e).__name__
    return {**_public(cfg), "local": backup.local_files(), "cloud": cloud, "cloud_error": cloud_error}


class ConfigIn(BaseModel):
    enabled: bool
    time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    tz: str = Field(max_length=64)
    keep: int = Field(ge=1, le=365)
    passphrase: str | None = Field(None, max_length=200)  # None = keep, "" = turn encryption off
    gdrive_client_id: str | None = Field(None, max_length=300)
    gdrive_client_secret: str | None = Field(None, max_length=300)  # None = keep


@router.put("/config")
def save_config(body: ConfigIn, user: UserDep, db: SessionDep):
    require_admin(user, db)
    cfg = backup.load(db)
    cfg.update(enabled=body.enabled, time=body.time, tz=body.tz, keep=body.keep)
    if body.passphrase is not None:
        if body.passphrase and len(body.passphrase) < 8:
            raise HTTPException(422, _("Use a passphrase of at least 8 characters"))
        cfg["passphrase"] = body.passphrase
    g = cfg["gdrive"]
    if body.gdrive_client_id is not None and body.gdrive_client_id.strip() != g["client_id"]:
        g.update(client_id=body.gdrive_client_id.strip(), refresh_token="", folder_id="")  # new app = reconnect
    if body.gdrive_client_secret is not None:
        g["client_secret"] = body.gdrive_client_secret.strip()
    backup.store(db, cfg)
    return _public(cfg)


@router.post("/run")
async def run_now(user: UserDep, db: SessionDep):
    require_admin(user, db)
    return await backup.run(db)


@router.get("/file/{name}")
def download(name: str, user: UserDep, db: SessionDep):
    require_admin(user, db)
    path = backup.backup_dir() / name
    if not name.startswith("bloomery-") or "/" in name or not path.is_file():
        raise HTTPException(404)
    return FileResponse(path, filename=name, media_type="application/octet-stream")


def _restore(blob: bytes, passphrase: str) -> dict[str, bool]:
    if len(blob) > backup.MAX_RESTORE:
        raise HTTPException(413, _("Backup file is too large"))
    try:
        backup.restore(blob, passphrase)
    except backup.BackupError as e:
        raise HTTPException(422, str(e)) from e
    return {"ok": True}


@router.post("/restore")
async def restore_upload(
    request: Request, user: UserDep, db: SessionDep, x_backup_passphrase: Annotated[str, Header()] = ""
):
    """Body = the backup file (raw bytes). Passphrase in the X-Backup-Passphrase header."""
    require_admin(user, db)
    blob = await request.body()
    db.close()
    return _restore(blob, x_backup_passphrase)


@router.post("/restore/cloud/{file_id}")
async def restore_cloud(
    file_id: str, user: UserDep, db: SessionDep, x_backup_passphrase: Annotated[str, Header()] = ""
):
    require_admin(user, db)
    cfg = backup.load(db)
    if not backup.drive_connected(cfg):
        raise HTTPException(409, _("Google Drive isn't connected"))
    try:
        async with httpx.AsyncClient(timeout=60) as c, backup.Drive(cfg["gdrive"], c) as d:
            blob = await d.download(file_id)
    except (backup.BackupError, httpx.HTTPError) as e:
        raise HTTPException(502, str(e) or "Google Drive download failed") from e
    db.close()
    return _restore(blob, x_backup_passphrase)


# ---------------------------------------------------------------- Google Drive OAuth
def _redirect_uri(origin: str) -> str:
    return f"{origin.rstrip('/')}/api/backups/google/callback"


@router.get("/google/start")
def google_start(origin: str, request: Request, user: UserDep, db: SessionDep):
    """`origin` = the address the owner is using (location.origin); it must match the redirect URI added in Google Cloud."""
    require_admin(user, db)
    g = backup.load(db)["gdrive"]
    if not (g["client_id"] and g["client_secret"]):
        raise HTTPException(409, _("Save the Google client ID and secret first"))
    if not origin.startswith(("https://", "http://localhost", "http://127.0.0.1")):
        raise HTTPException(422, _("Google only allows HTTPS addresses (or localhost)"))
    state = secrets.token_urlsafe(24)
    request.session["gstate"] = state
    request.session["gorigin"] = origin
    return {"url": backup.google_auth_url(g["client_id"], _redirect_uri(origin), state)}


@router.get("/google/callback", include_in_schema=False)
async def google_callback(
    request: Request, user: UserDep, db: SessionDep, state: str = "", code: str = "", error: str = ""
):
    require_admin(user, db)
    expected, origin = request.session.pop("gstate", None), request.session.pop("gorigin", "")
    if error or not code or not expected or not secrets.compare_digest(state, expected):
        return RedirectResponse(f"/profile?backup=google-{error or 'failed'}", 303)
    cfg = backup.load(db)
    try:
        cfg["gdrive"]["refresh_token"] = await backup.google_exchange(cfg["gdrive"], code, _redirect_uri(origin))
        async with httpx.AsyncClient(timeout=20) as c, backup.Drive(cfg["gdrive"], c) as d:
            await d.folder()
    except (backup.BackupError, httpx.HTTPError):
        return RedirectResponse("/profile?backup=google-failed", 303)
    backup.store(db, cfg)
    return RedirectResponse("/profile?backup=google-connected", 303)


@router.delete("/google")
async def google_disconnect(user: UserDep, db: SessionDep):
    require_admin(user, db)
    cfg = backup.load(db)
    if token := cfg["gdrive"]["refresh_token"]:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                await c.post(backup.GOOGLE_REVOKE, data={"token": token})
        except httpx.HTTPError:
            pass  # still forget it locally
    cfg["gdrive"].update(refresh_token="", folder_id="")
    backup.store(db, cfg)
    return _public(cfg)
