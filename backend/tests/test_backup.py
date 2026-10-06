"""Backups: snapshot, encryption, retention, restore (file + Google Drive), schedule, OAuth flow, admin-only."""

import json
import re
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi.testclient import TestClient

from app import backup
from app.main import app
from app.routers import auth


def owner() -> TestClient:
    c = TestClient(app)
    c.post("/api/auth/login", json={"username": "ana", "password": "supersecret"})
    if c.get("/api/auth/me").status_code != 200:  # running this file alone
        c.post("/api/auth/register", json={"username": "ana", "password": "supersecret"})
    return c


class FakeDrive:
    """In-memory Google OAuth + Drive v3 behind httpx.MockTransport."""

    def __init__(self) -> None:
        self.files: dict[str, dict] = {}
        self.n = 0

    def _id(self) -> str:
        self.n += 1
        return f"f{self.n}"

    def __call__(self, req: httpx.Request) -> httpx.Response:
        url = str(req.url)
        if url.startswith(backup.GOOGLE_TOKEN):
            form = parse_qs(req.content.decode())
            if form["grant_type"] == ["authorization_code"]:
                return httpx.Response(200, json={"refresh_token": "rt-1", "access_token": "at"})
            return httpx.Response(200, json={"access_token": "at"})
        if url.startswith(backup.GOOGLE_REVOKE):
            return httpx.Response(200)
        assert req.headers["authorization"] == "Bearer at"
        if url.startswith("https://www.googleapis.com/upload/"):
            boundary = req.headers["content-type"].split("boundary=")[1]
            meta_part, data_part = req.content.split(f"--{boundary}".encode())[1:3]
            meta = json.loads(meta_part.split(b"\r\n\r\n", 1)[1].strip())
            data = data_part.split(b"\r\n\r\n", 1)[1][:-2]
            fid = self._id()
            self.files[fid] = {
                "id": fid,
                "name": meta["name"],
                "parents": meta["parents"],
                "data": data,
                "createdTime": f"2026-10-06T00:00:{self.n:02d}Z",
                "mimeType": "application/octet-stream",
            }
            return httpx.Response(200, json={"id": fid})
        m = re.match(r"https://www.googleapis.com/drive/v3/files(?:/(\w+))?", url)
        assert m, url
        fid = m.group(1)
        if req.method == "POST":  # folder
            body = json.loads(req.content)
            new = self._id()
            self.files[new] = {"id": new, **body, "parents": [], "createdTime": "2026-10-06T00:00:00Z"}
            return httpx.Response(200, json={"id": new})
        if req.method == "DELETE":
            self.files.pop(fid, None)
            return httpx.Response(204)
        if fid:
            return httpx.Response(200, content=self.files[fid]["data"])
        q = req.url.params["q"]
        if "mimeType=" in q:
            hits = [f for f in self.files.values() if f.get("mimeType") == backup.FOLDER_MIME]
        else:
            parent = q.split("'")[1]
            hits = sorted(
                (f for f in self.files.values() if parent in f.get("parents", [])),
                key=lambda f: f["createdTime"],
                reverse=True,
            )
        return httpx.Response(
            200,
            json={
                "files": [
                    {
                        "id": f["id"],
                        "name": f["name"],
                        "createdTime": f["createdTime"],
                        "size": str(len(f.get("data", b""))),
                    }
                    for f in hits
                ]
            },
        )


@pytest.fixture
def drive(monkeypatch):
    fake = FakeDrive()
    real = httpx.AsyncClient
    monkeypatch.setattr(backup.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(fake), **kw))
    return fake


def test_encrypt_roundtrip_and_errors():
    blob = backup.encrypt(b"hello", "correct horse")
    assert blob.startswith(backup.MAGIC) and b"hello" not in blob
    assert backup.decrypt(blob, "correct horse") == b"hello"
    with pytest.raises(backup.BackupError, match="Wrong passphrase"):
        backup.decrypt(blob, "nope nope")
    with pytest.raises(backup.BackupError, match="encrypted"):
        backup.unpack(blob, "")
    with pytest.raises(backup.BackupError, match="isn't a Bloomery backup"):
        backup.unpack(b"just text", "")


def test_backup_run_download_restore_and_retention():
    c = owner()
    c.put("/api/logs/2026-03-01?today=2026-03-01", json={"flow": "heavy", "notes": "before backup"})
    cfg = c.put("/api/backups/config", json={"enabled": True, "time": "03:00", "tz": "UTC", "keep": 2}).json()
    assert cfg["encrypted"] is False and cfg["gdrive"]["connected"] is False

    r = c.post("/api/backups/run").json()
    assert r["name"].endswith(".db.gz") and r["error"] == "" and r["cloud"] is False
    raw = c.get(f"/api/backups/file/{r['name']}").content
    assert raw[:2] == b"\x1f\x8b"
    assert c.get("/api/backups/file/..%2Fbloomery.db").status_code == 404

    c.put("/api/logs/2026-03-01?today=2026-03-01", json={"flow": "heavy", "notes": "changed after"})
    assert c.post("/api/backups/restore", content=raw).json() == {"ok": True}
    assert c.get("/api/logs/2026-03-01").json()["notes"] == "before backup"
    assert any("prerestore" in f["name"] for f in c.get("/api/backups").json()["local"])

    assert c.post("/api/backups/restore", content=b"not a backup").status_code == 422
    for _ in range(3):
        c.post("/api/backups/run")
    regular = [f for f in c.get("/api/backups").json()["local"] if backup.NAME_RE.match(f["name"])]
    assert len(regular) <= 2


def test_encrypted_backup_needs_passphrase():
    c = owner()
    assert (
        c.put(
            "/api/backups/config",
            json={"enabled": True, "time": "03:00", "tz": "UTC", "keep": 5, "passphrase": "short"},
        ).status_code
        == 422
    )
    c.put(
        "/api/backups/config",
        json={"enabled": True, "time": "03:00", "tz": "UTC", "keep": 5, "passphrase": "long enough phrase"},
    )
    name = c.post("/api/backups/run").json()["name"]
    assert name.endswith(".enc")
    blob = c.get(f"/api/backups/file/{name}").content
    assert c.post("/api/backups/restore", content=blob).status_code == 422
    assert (
        c.post("/api/backups/restore", content=blob, headers={"X-Backup-Passphrase": "wrong one!"}).status_code == 422
    )
    assert c.post(
        "/api/backups/restore", content=blob, headers={"X-Backup-Passphrase": "long enough phrase"}
    ).json() == {"ok": True}
    c.put("/api/backups/config", json={"enabled": True, "time": "03:00", "tz": "UTC", "keep": 5, "passphrase": ""})


def test_google_drive_connect_upload_prune_restore(drive):
    c = owner()
    assert c.get("/api/backups/google/start", params={"origin": "https://bloom.example"}).status_code == 409
    c.put(
        "/api/backups/config",
        json={
            "enabled": True,
            "time": "03:00",
            "tz": "UTC",
            "keep": 2,
            "gdrive_client_id": "cid.apps.googleusercontent.com",
            "gdrive_client_secret": "sec",
        },
    )
    assert c.get("/api/backups/google/start", params={"origin": "http://192.168.1.5:8420"}).status_code == 422
    url = c.get("/api/backups/google/start", params={"origin": "https://bloom.example"}).json()["url"]
    q = parse_qs(urlparse(url).query)
    assert q["redirect_uri"] == ["https://bloom.example/api/backups/google/callback"]
    assert q["scope"] == [backup.SCOPE] and q["access_type"] == ["offline"]

    bad = c.get("/api/backups/google/callback", params={"state": "forged", "code": "x"}, follow_redirects=False)
    assert bad.headers["location"].endswith("google-failed")
    c.get("/api/backups/google/start", params={"origin": "https://bloom.example"})  # new state
    state = parse_qs(
        urlparse(c.get("/api/backups/google/start", params={"origin": "https://bloom.example"}).json()["url"]).query
    )["state"][0]
    ok = c.get("/api/backups/google/callback", params={"state": state, "code": "abc"}, follow_redirects=False)
    assert ok.headers["location"] == "/profile?backup=google-connected"

    info = c.get("/api/backups").json()
    assert info["gdrive"]["connected"] is True and info["cloud"] == []
    for _ in range(3):
        assert c.post("/api/backups/run").json()["cloud"] is True
    cloud = c.get("/api/backups").json()["cloud"]
    assert len(cloud) == 2 and all(backup.NAME_RE.match(f["name"]) for f in cloud)

    assert c.post(f"/api/backups/restore/cloud/{cloud[0]['id']}").json() == {"ok": True}
    assert c.delete("/api/backups/google").json()["gdrive"]["connected"] is False


def test_scheduled_tick_runs_once_per_day():
    import asyncio

    c = owner()
    c.put("/api/backups/config", json={"enabled": True, "time": "03:00", "tz": "Africa/Johannesburg", "keep": 5})
    before = len(backup.local_files())
    early = datetime(2026, 10, 7, 0, 30, tzinfo=UTC)  # 02:30 local
    late = datetime(2026, 10, 7, 1, 30, tzinfo=UTC)  # 03:30 local
    assert asyncio.run(backup.tick(early)) is False
    assert asyncio.run(backup.tick(late)) is True
    assert asyncio.run(backup.tick(late)) is False
    assert len(backup.local_files()) == min(before + 1, 5 + 3)


def test_owner_only(monkeypatch):
    monkeypatch.setattr(auth, "registration_open", lambda db: True)
    other = TestClient(app)
    other.post("/api/auth/register", json={"username": "notowner", "password": "notowner1"})
    other.post("/api/auth/login", json={"username": "notowner", "password": "notowner1"})
    assert other.get("/api/backups").status_code == 403
    assert other.post("/api/backups/run").status_code == 403
    assert other.post("/api/backups/restore", content=b"x").status_code == 403
