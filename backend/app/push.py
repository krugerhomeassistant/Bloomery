"""Web Push (RFC 8030/8291/8292) to installed Bloomery apps: phone home-screen app or desktop browser.

Payloads are encrypted with http-ece (aes128gcm) and signed with a VAPID key generated once per server and kept in
the Setting table ("vapid"). Subscriptions per user live under "push:<uid>" as a JSON list. Needs HTTPS.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any
from urllib.parse import urlsplit

import http_ece
import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from py_vapid import Vapid02
from sqlmodel import Session

from .models import Setting

log = logging.getLogger("bloomery.push")
CONTACT = "https://github.com"  # VAPID "sub" fallback; normally the Bloomery address the device subscribed from


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def vapid(db: Session) -> Vapid02:
    row = db.get(Setting, "vapid")
    if row:
        return Vapid02.from_pem(row.value.encode())
    v = Vapid02()
    v.generate_keys()
    db.merge(Setting(key="vapid", value=v.private_pem().decode()))
    db.commit()
    return v


def public_key(db: Session) -> str:
    """applicationServerKey for PushManager.subscribe (uncompressed P-256 point, base64url)."""
    pub = vapid(db).public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return _b64(pub)


def subscriptions(db: Session, uid: int) -> list[dict[str, Any]]:
    row = db.get(Setting, f"push:{uid}")
    return json.loads(row.value) if row else []


def save_subscriptions(db: Session, uid: int, subs: list[dict[str, Any]]) -> None:
    key = f"push:{uid}"
    if subs:
        db.merge(Setting(key=key, value=json.dumps(subs)))
    elif row := db.get(Setting, key):
        db.delete(row)
    db.commit()


def encrypt(payload: bytes, sub: dict[str, Any]) -> bytes:
    return http_ece.encrypt(
        payload,
        private_key=ec.generate_private_key(ec.SECP256R1()),
        dh=_unb64(sub["keys"]["p256dh"]),
        auth_secret=_unb64(sub["keys"]["auth"]),
        version="aes128gcm",
    )


async def send(db: Session, uid: int, title: str, body: str, url: str = "/") -> int:
    """Push to every device of a user. Drops subscriptions the push service says are gone. Returns deliveries."""
    subs = subscriptions(db, uid)
    if not subs:
        return 0
    v = vapid(db)
    payload = json.dumps({"title": title, "body": body, "url": url}).encode()
    keep, sent = [], 0
    async with httpx.AsyncClient(timeout=15) as c:
        for sub in subs:
            ep = urlsplit(sub["endpoint"])
            claims = {
                "sub": sub.get("contact") or CONTACT,
                "aud": f"{ep.scheme}://{ep.netloc}",
                "exp": int(time.time()) + 12 * 3600,
            }
            headers = {**v.sign(claims), "TTL": "86400", "Content-Encoding": "aes128gcm", "Urgency": "normal"}
            try:
                r = await c.post(sub["endpoint"], content=encrypt(payload, sub), headers=headers)
            except httpx.HTTPError as e:
                log.warning("push to %s failed: %s", ep.netloc, e)
                keep.append(sub)
                continue
            if r.status_code in (404, 410):  # unsubscribed / expired
                continue
            keep.append(sub)
            if r.status_code < 300:
                sent += 1
            else:
                log.warning("push to %s rejected: %s %s", ep.netloc, r.status_code, r.text[:200])
    if len(keep) != len(subs):
        save_subscriptions(db, uid, keep)
    return sent
