"""Backups of the whole instance.

A backup is a consistent SQLite snapshot (sqlite3 backup API, safe while the app is running), gzipped and,
when a passphrase is set, encrypted with AES-256-GCM (key from Argon2id). Files go to <data>/backups and,
optionally, to a "Bloomery backups" folder in Google Drive (drive.file scope: Bloomery only sees files it made).
Config lives in the Setting table under "backup" as JSON, so no schema change is needed.
"""

from __future__ import annotations

import asyncio
import gzip
import json
import logging
import re
import secrets
import sqlite3
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlmodel import Session

from .config import get_settings
from .db import get_engine, init_db
from .i18n import _
from .models import Setting

log = logging.getLogger("bloomery.backup")

KEY = "backup"
DEFAULTS: dict[str, Any] = {
    "enabled": True,
    "time": "03:00",
    "tz": "UTC",
    "keep": 14,
    "passphrase": "",
    "gdrive": {"client_id": "", "client_secret": "", "refresh_token": "", "folder_id": ""},
    "last": "",
    "last_ok": None,
    "last_error": "",
    "last_day": "",
}
MAGIC = b"BLMRY1"  # encrypted-file header: MAGIC | salt(16) | nonce(12) | AES-GCM(ciphertext+tag)
NAME_RE = re.compile(r"^bloomery-\d{8}-\d{6}(-\d+)?\.db\.gz(\.enc)?$")
MAX_RESTORE = 200 * 1024 * 1024


class BackupError(Exception):
    """User-facing backup/restore problem."""


# ---------------------------------------------------------------- config
def load(db: Session) -> dict[str, Any]:
    row = db.get(Setting, KEY)
    cfg = {**DEFAULTS, **(json.loads(row.value) if row else {})}
    cfg["gdrive"] = {**DEFAULTS["gdrive"], **cfg["gdrive"]}
    return cfg


def store(db: Session, cfg: dict[str, Any]) -> None:
    db.merge(Setting(key=KEY, value=json.dumps(cfg)))
    db.commit()


def backup_dir() -> Path:
    d = get_settings().data_dir / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return get_settings().data_dir / "bloomery.db"


# ---------------------------------------------------------------- crypto
def _key(passphrase: str, salt: bytes) -> bytes:
    # 32 MiB / 3 passes: strong against brute force, light enough for a small home server
    return hash_secret_raw(
        passphrase.encode(), salt, time_cost=3, memory_cost=32 * 1024, parallelism=1, hash_len=32, type=Type.ID
    )


def encrypt(data: bytes, passphrase: str) -> bytes:
    salt, nonce = secrets.token_bytes(16), secrets.token_bytes(12)
    return MAGIC + salt + nonce + AESGCM(_key(passphrase, salt)).encrypt(nonce, data, MAGIC)


def decrypt(blob: bytes, passphrase: str) -> bytes:
    salt, nonce, ct = blob[6:22], blob[22:34], blob[34:]
    try:
        return AESGCM(_key(passphrase, salt)).decrypt(nonce, ct, MAGIC)
    except Exception as e:
        raise BackupError(_("Wrong passphrase, or the file is damaged.")) from e


# ---------------------------------------------------------------- snapshot / restore
def snapshot() -> bytes:
    """Gzipped, consistent copy of the live database (includes anything still in the WAL)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "snap.db"
        src, dst = sqlite3.connect(db_path()), sqlite3.connect(out)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
        return gzip.compress(out.read_bytes(), compresslevel=6)


def make(passphrase: str) -> tuple[str, bytes]:
    data = snapshot()
    name = f"bloomery-{datetime.now(UTC):%Y%m%d-%H%M%S}.db.gz"
    if passphrase:
        return name + ".enc", encrypt(data, passphrase)
    return name, data


def unpack(blob: bytes, passphrase: str) -> bytes:
    """Encrypted/gzipped/plain backup bytes -> raw SQLite bytes."""
    if blob.startswith(MAGIC):
        if not passphrase:
            raise BackupError(_("This backup is encrypted. Enter its passphrase."))
        blob = decrypt(blob, passphrase)
    if blob[:2] == b"\x1f\x8b":
        try:
            blob = gzip.decompress(blob)
        except OSError as e:
            raise BackupError(_("The backup file is damaged.")) from e
    if not blob.startswith(b"SQLite format 3\x00"):
        raise BackupError(_("That isn't a Bloomery backup."))
    return blob


def restore(blob: bytes, passphrase: str) -> None:
    """Replace the live database with a backup. A safety backup of the current data is written first."""
    raw = unpack(blob, passphrase)
    with tempfile.TemporaryDirectory() as tmp:
        cand = Path(tmp) / "restore.db"
        cand.write_bytes(raw)
        con = sqlite3.connect(cand)
        try:
            ok = con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            con.close()
        if not ok or not {"user", "daylog", "setting"} <= tables:
            raise BackupError(_("That backup is damaged or isn't from Bloomery."))
        name, data = make("")
        (backup_dir() / name.replace("bloomery-", "bloomery-prerestore-", 1)).write_bytes(data)
        get_engine().dispose()  # close pooled connections, then copy page-by-page into the live file
        src, dst = sqlite3.connect(cand), sqlite3.connect(db_path())
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
    init_db()  # tables added in newer versions


# ---------------------------------------------------------------- local files
def local_files() -> list[dict[str, Any]]:
    files = [p for p in backup_dir().iterdir() if p.is_file() and p.name.startswith("bloomery-")]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        {
            "name": p.name,
            "size": p.stat().st_size,
            "created": datetime.fromtimestamp(p.stat().st_mtime, UTC).isoformat(),
        }
        for p in files
    ]


def prune_local(keep: int) -> None:
    regular = [f for f in local_files() if NAME_RE.match(f["name"])]
    for f in regular[keep:]:
        (backup_dir() / f["name"]).unlink(missing_ok=True)
    for f in [f for f in local_files() if "prerestore" in f["name"]][3:]:  # keep the last 3 safety copies
        (backup_dir() / f["name"]).unlink(missing_ok=True)


# ---------------------------------------------------------------- Google Drive
GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE = "https://oauth2.googleapis.com/revoke"
DRIVE = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,size,createdTime"
SCOPE = "https://www.googleapis.com/auth/drive.file"
FOLDER = "Bloomery backups"
FOLDER_MIME = "application/vnd.google-apps.folder"


def google_auth_url(client_id: str, redirect_uri: str, state: str) -> str:
    q = httpx.QueryParams(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    return f"{GOOGLE_AUTH}?{q}"


def _google_error(r: httpx.Response) -> BackupError:
    try:
        j = r.json()
        msg = j.get("error_description") or (j.get("error") or {}).get("message") or j.get("error")
    except ValueError:
        msg = r.text[:200]
    return BackupError(f"Google Drive: {msg or r.status_code}")


async def google_exchange(g: dict[str, str], code: str, redirect_uri: str) -> str:
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(
            GOOGLE_TOKEN,
            data={
                "code": code,
                "client_id": g["client_id"],
                "client_secret": g["client_secret"],
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
    if r.status_code != 200:
        raise _google_error(r)
    token = r.json().get("refresh_token")
    if not token:
        raise BackupError(
            "Google didn't return a refresh token. Remove Bloomery's access in your Google account and connect again."
        )
    return str(token)


class Drive:
    """Tiny Google Drive v3 client for one folder."""

    def __init__(self, g: dict[str, str], client: httpx.AsyncClient) -> None:
        self.g, self.c, self.headers = g, client, {}

    async def __aenter__(self) -> Drive:
        r = await self.c.post(
            GOOGLE_TOKEN,
            data={
                "client_id": self.g["client_id"],
                "client_secret": self.g["client_secret"],
                "refresh_token": self.g["refresh_token"],
                "grant_type": "refresh_token",
            },
        )
        if r.status_code != 200:
            raise _google_error(r)
        self.headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    async def _json(self, method: str, url: str, headers: dict[str, str] | None = None, **kw: Any) -> Any:
        r = await self.c.request(method, url, headers={**self.headers, **(headers or {})}, **kw)
        if r.status_code >= 400:
            raise _google_error(r)
        return r.json() if r.content else None

    async def folder(self) -> str:
        """Our folder id: the remembered one, an existing one Bloomery created earlier (fresh install), or a new one."""
        if fid := self.g.get("folder_id"):
            return fid
        q = f"name='{FOLDER}' and mimeType='{FOLDER_MIME}' and trashed=false"
        found = (await self._json("GET", f"{DRIVE}/files", params={"q": q, "fields": "files(id)"}))["files"]
        if found:
            self.g["folder_id"] = found[0]["id"]
        else:
            self.g["folder_id"] = (
                await self._json("POST", f"{DRIVE}/files", json={"name": FOLDER, "mimeType": FOLDER_MIME})
            )["id"]
        return self.g["folder_id"]

    async def list(self) -> list[dict[str, Any]]:
        q = f"'{await self.folder()}' in parents and trashed=false"
        res = await self._json(
            "GET",
            f"{DRIVE}/files",
            params={
                "q": q,
                "orderBy": "createdTime desc",
                "pageSize": 100,
                "fields": "files(id,name,size,createdTime)",
            },
        )
        return [
            {"id": f["id"], "name": f["name"], "size": int(f.get("size", 0)), "created": f["createdTime"]}
            for f in res["files"]
        ]

    async def upload(self, name: str, data: bytes) -> None:
        boundary = secrets.token_hex(16)
        meta = json.dumps({"name": name, "parents": [await self.folder()]}).encode()
        body = (
            f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode()
            + meta
            + f"\r\n--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
            + data
            + f"\r\n--{boundary}--\r\n".encode()
        )
        await self._json(
            "POST", DRIVE_UPLOAD, content=body, headers={"Content-Type": f"multipart/related; boundary={boundary}"}
        )

    async def download(self, file_id: str) -> bytes:
        r = await self.c.get(f"{DRIVE}/files/{file_id}", params={"alt": "media"}, headers=self.headers)
        if r.status_code >= 400:
            raise _google_error(r)
        return r.content

    async def delete(self, file_id: str) -> None:
        r = await self.c.delete(f"{DRIVE}/files/{file_id}", headers=self.headers)
        if r.status_code >= 400 and r.status_code != 404:
            raise _google_error(r)


def drive_connected(cfg: dict[str, Any]) -> bool:
    g = cfg["gdrive"]
    return bool(g["client_id"] and g["client_secret"] and g["refresh_token"])


# ---------------------------------------------------------------- run / schedule
async def run(db: Session) -> dict[str, Any]:
    """Make a backup now: local file always, Google Drive when connected. Records the outcome in the config."""
    cfg = load(db)
    name, data = await asyncio.to_thread(make, cfg["passphrase"])
    stem, n = name, 1
    while (backup_dir() / name).exists():  # two backups in the same second
        n += 1
        name = stem.replace(".db.gz", f"-{n}.db.gz", 1)
    (backup_dir() / name).write_bytes(data)
    prune_local(int(cfg["keep"]))
    error = ""
    if drive_connected(cfg):
        try:
            async with httpx.AsyncClient(timeout=60) as c, Drive(cfg["gdrive"], c) as d:
                await d.upload(name, data)
                for old in [f for f in await d.list() if NAME_RE.match(f["name"])][int(cfg["keep"]) :]:
                    await d.delete(old["id"])
        except (BackupError, httpx.HTTPError) as e:
            error = str(e) or type(e).__name__
            log.warning("Google Drive backup failed: %s", error)
    cfg.update(last=datetime.now(UTC).isoformat(), last_ok=not error, last_error=error)
    store(db, cfg)
    return {"name": name, "size": len(data), "cloud": drive_connected(cfg) and not error, "error": error}


async def tick(now_utc: datetime | None = None) -> bool:
    """Run the daily backup once the configured local time has passed. Returns True if one ran."""
    now_utc = now_utc or datetime.now(UTC)
    with Session(get_engine()) as db:
        cfg = load(db)
        if not cfg["enabled"] or not db_path().exists():
            return False
        try:
            local = now_utc.astimezone(ZoneInfo(cfg["tz"]))
        except Exception:
            local = now_utc
        if cfg["last_day"] == local.date().isoformat() or local.strftime("%H:%M") < cfg["time"]:
            return False
        cfg["last_day"] = local.date().isoformat()  # mark first so a failure doesn't retry every minute
        store(db, cfg)
        await run(db)
        return True


async def scheduler() -> None:
    while True:
        try:
            await tick()
        except Exception:
            log.exception("backup tick failed")
        await asyncio.sleep(60)
