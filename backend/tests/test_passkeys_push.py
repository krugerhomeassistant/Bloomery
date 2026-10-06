"""Passkey unlock (with a software authenticator doing real ECDSA) and Web Push (payload decrypted like a browser)."""

import base64
import hashlib
import json
import os
import struct

import cbor2
import http_ece
import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app import push
from app.db import init_db
from app.main import app

ORIGIN = "https://bloom.example"


def b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def login() -> TestClient:
    init_db()  # also when this file runs on its own
    c = TestClient(app, headers={"Origin": ORIGIN})
    c.post("/api/auth/login", json={"username": "ana", "password": "supersecret"})
    if c.get("/api/auth/me").status_code != 200:
        c.post("/api/auth/register", json={"username": "ana", "password": "supersecret"})
    return c


class SoftAuthenticator:
    """Minimal platform authenticator: P-256 key, 'none' attestation, user presence + verification."""

    def __init__(self, rp_id: str) -> None:
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.cred_id, self.rp_id, self.count = os.urandom(16), rp_id, 0

    def _auth_data(self, attested: bool) -> bytes:
        self.count += 1
        flags = 0x01 | 0x04 | (0x40 if attested else 0)  # UP | UV | AT
        data = hashlib.sha256(self.rp_id.encode()).digest() + bytes([flags]) + struct.pack(">I", self.count)
        if attested:
            n = self.key.public_key().public_numbers()
            cose = cbor2.dumps({1: 2, 3: -7, -1: 1, -2: n.x.to_bytes(32, "big"), -3: n.y.to_bytes(32, "big")})
            data += b"\0" * 16 + struct.pack(">H", len(self.cred_id)) + self.cred_id + cose
        return data

    def _cd(self, kind: str, challenge: str, origin: str) -> bytes:
        return json.dumps({"type": kind, "challenge": challenge, "origin": origin, "crossOrigin": False}).encode()

    def _base(self) -> dict:
        return {
            "id": b64(self.cred_id),
            "rawId": b64(self.cred_id),
            "type": "public-key",
            "authenticatorAttachment": "platform",
            "clientExtensionResults": {},
        }

    def create(self, options: dict, origin: str = ORIGIN) -> dict:
        att = cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": self._auth_data(True)})
        cd = self._cd("webauthn.create", options["challenge"], origin)
        return {**self._base(), "response": {"clientDataJSON": b64(cd), "attestationObject": b64(att)}}

    def get(self, options: dict, origin: str = ORIGIN) -> dict:
        cd, ad = self._cd("webauthn.get", options["challenge"], origin), self._auth_data(False)
        sig = self.key.sign(ad + hashlib.sha256(cd).digest(), ec.ECDSA(hashes.SHA256()))
        return {
            **self._base(),
            "response": {
                "clientDataJSON": b64(cd),
                "authenticatorData": b64(ad),
                "signature": b64(sig),
                "userHandle": None,
            },
        }


def test_passkey_register_and_unlock():
    c = login()
    plain = TestClient(app)  # no Origin header / plain http
    plain.cookies = c.cookies
    assert plain.post("/api/auth/passkey/register/options").status_code == 400

    phone = SoftAuthenticator("bloom.example")
    opts = c.post("/api/auth/passkey/register/options").json()
    assert opts["rp"]["id"] == "bloom.example" and opts["authenticatorSelection"]["userVerification"] == "required"
    keys = c.post("/api/auth/passkey/register", json={"credential": phone.create(opts), "name": "iPhone"}).json()
    assert [k["name"] for k in keys] == ["iPhone"] and c.get("/api/auth/me").json()["passkeys"] == 1

    opts = c.post("/api/auth/passkey/unlock/options").json()
    assert opts["allowCredentials"][0]["id"] == b64(phone.cred_id)
    assert c.post("/api/auth/passkey/unlock", json={"credential": phone.get(opts)}).json() == {"ok": True}

    # replayed / wrong-origin / unknown-device assertions are rejected
    opts = c.post("/api/auth/passkey/unlock/options").json()
    assert (
        c.post("/api/auth/passkey/unlock", json={"credential": phone.get(opts, "https://evil.example")}).status_code
        == 400
    )
    assert c.post("/api/auth/passkey/unlock", json={"credential": phone.get(opts)}).status_code == 400  # challenge used
    other = SoftAuthenticator("bloom.example")
    opts = c.post("/api/auth/passkey/unlock/options").json()
    assert c.post("/api/auth/passkey/unlock", json={"credential": other.get(opts)}).status_code == 400

    # passkeys belong to the address they were made on
    elsewhere = TestClient(app, headers={"Origin": "https://other.example"})
    elsewhere.cookies = c.cookies
    assert elsewhere.post("/api/auth/passkey/unlock/options").status_code == 404

    assert c.delete(f"/api/auth/passkey/{b64(phone.cred_id)}").json() == []
    assert c.get("/api/auth/me").json()["passkeys"] == 0


def test_web_push_encrypts_for_the_device(monkeypatch):
    c = login()
    info = c.get("/api/notifications/push").json()
    server_key = base64.urlsafe_b64decode(info["public_key"] + "==")
    assert len(server_key) == 65 and server_key[0] == 4  # uncompressed P-256 point

    device = ec.generate_private_key(ec.SECP256R1())
    auth = os.urandom(16)
    p256dh = device.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    sub = {"endpoint": "https://web.push.apple.com/abc", "keys": {"p256dh": b64(p256dh), "auth": b64(auth)}}
    assert c.post("/api/notifications/push", json=sub).json() == {"devices": 1}
    assert c.post("/api/notifications/push", json=sub).json() == {"devices": 1}  # same device again

    seen: list[httpx.Request] = []
    status = {"code": 201}

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(req)
        return httpx.Response(status["code"])

    real = httpx.AsyncClient
    monkeypatch.setattr(push.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    r = c.post("/api/notifications/test?today=2026-10-06", json={"url": "", "time": "08:00", "tz": "UTC", "kinds": []})
    assert r.json()["ok"] is True and r.json()["devices"] == 1
    req = seen[-1]
    assert req.headers["content-encoding"] == "aes128gcm" and req.headers["authorization"].startswith("vapid t=")
    msg = json.loads(http_ece.decrypt(req.content, private_key=device, auth_secret=auth, version="aes128gcm"))
    assert msg["title"] == "🌸 Bloomery is connected" and msg["url"] == "/"

    status["code"] = 410  # device unsubscribed: dropped
    c.post("/api/notifications/test?today=2026-10-06", json={"url": "", "time": "08:00", "tz": "UTC", "kinds": []})
    assert c.get("/api/notifications/push").json()["devices"] == 0
    assert (
        c.post("/api/notifications/test", json={"url": "", "time": "08:00", "tz": "UTC", "kinds": []}).status_code
        == 400
    )
