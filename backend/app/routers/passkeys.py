"""Passkeys (WebAuthn) to unlock the app with Face ID / Touch ID / fingerprint / Windows Hello instead of the PIN.

The relying party is the address the browser is using (Origin header), so passkeys work on the HTTPS domain
they were created on. Credentials are stored per user in the Setting table under "passkeys:<uid>".
"""

from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session
from webauthn import (
    base64url_to_bytes,
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.exceptions import InvalidAuthenticationResponse, InvalidRegistrationResponse
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from ..deps import SessionDep, UserDep
from ..i18n import _
from ..models import Setting

router = APIRouter(prefix="/api/auth/passkey", tags=["auth"])


def load(db: Session, uid: int) -> list[dict[str, Any]]:
    row = db.get(Setting, f"passkeys:{uid}")
    return json.loads(row.value) if row else []


def save(db: Session, uid: int, keys: list[dict[str, Any]]) -> None:
    key = f"passkeys:{uid}"
    if keys:
        db.merge(Setting(key=key, value=json.dumps(keys)))
    elif row := db.get(Setting, key):
        db.delete(row)
    db.commit()


def _origin(request: Request) -> tuple[str, str]:
    """(origin, rp_id) from the browser's Origin header. WebAuthn needs HTTPS (or localhost)."""
    origin = request.headers.get("origin", "")
    host = urlsplit(origin).hostname or ""
    if not (origin.startswith("https://") or host in ("localhost", "127.0.0.1")):
        raise HTTPException(400, _("Face ID / fingerprint unlock needs Bloomery to be opened over HTTPS"))
    return origin, host


def _public(k: dict[str, Any]) -> dict[str, Any]:
    return {"id": k["id"], "name": k["name"], "created": k["created"], "rp_id": k["rp_id"]}


@router.get("")
def list_passkeys(user: UserDep, db: SessionDep):
    return [_public(k) for k in load(db, user.id)]


@router.post("/register/options")
def register_options(request: Request, user: UserDep, db: SessionDep):
    rp_id = _origin(request)[1]
    opts = generate_registration_options(
        rp_id=rp_id,
        rp_name="Bloomery",
        user_id=f"bloomery-{user.id}".encode(),
        user_name=user.username,
        user_display_name=user.display_name or user.username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,  # this phone/computer's biometrics
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[PublicKeyCredentialDescriptor(id=base64url_to_bytes(k["id"])) for k in load(db, user.id)],
    )
    request.session["pk_challenge"] = bytes_to_base64url(opts.challenge)
    return json.loads(options_to_json(opts))


class RegisterIn(BaseModel):
    credential: dict[str, Any]
    name: str = Field("This device", max_length=60)


@router.post("/register")
def register(body: RegisterIn, request: Request, user: UserDep, db: SessionDep):
    origin, rp_id = _origin(request)
    challenge = request.session.pop("pk_challenge", None)
    if not challenge:
        raise HTTPException(400, _("Start again"))
    try:
        v = verify_registration_response(
            credential=body.credential,
            expected_challenge=base64url_to_bytes(challenge),
            expected_rp_id=rp_id,
            expected_origin=origin,
            require_user_verification=True,
        )
    except InvalidRegistrationResponse as e:
        raise HTTPException(400, f"Couldn't add this device: {e}") from e
    keys = load(db, user.id)
    keys.append(
        {
            "id": bytes_to_base64url(v.credential_id),
            "public_key": bytes_to_base64url(v.credential_public_key),
            "sign_count": v.sign_count,
            "name": body.name.strip() or "This device",
            "rp_id": rp_id,
            "created": datetime.now(UTC).isoformat(),
        }
    )
    save(db, user.id, keys)
    return [_public(k) for k in keys]


@router.post("/unlock/options")
def unlock_options(request: Request, user: UserDep, db: SessionDep):
    rp_id = _origin(request)[1]
    keys = [k for k in load(db, user.id) if k["rp_id"] == rp_id]
    if not keys:
        raise HTTPException(404, _("No Face ID / fingerprint set up for this address"))
    opts = generate_authentication_options(
        rp_id=rp_id,
        challenge=secrets.token_bytes(32),
        allow_credentials=[PublicKeyCredentialDescriptor(id=base64url_to_bytes(k["id"])) for k in keys],
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    request.session["pk_challenge"] = bytes_to_base64url(opts.challenge)
    return json.loads(options_to_json(opts))


class UnlockIn(BaseModel):
    credential: dict[str, Any]


@router.post("/unlock")
def unlock(body: UnlockIn, request: Request, user: UserDep, db: SessionDep):
    origin, rp_id = _origin(request)
    challenge = request.session.pop("pk_challenge", None)
    keys = load(db, user.id)
    key = next((k for k in keys if k["id"] == body.credential.get("id")), None)
    if not challenge or not key:
        raise HTTPException(400, _("Unknown device. Use your PIN."))
    try:
        v = verify_authentication_response(
            credential=body.credential,
            expected_challenge=base64url_to_bytes(challenge),
            expected_rp_id=rp_id,
            expected_origin=origin,
            credential_public_key=base64url_to_bytes(key["public_key"]),
            credential_current_sign_count=key["sign_count"],
            require_user_verification=True,
        )
    except InvalidAuthenticationResponse as e:
        raise HTTPException(400, _("Face ID / fingerprint check failed. Use your PIN.")) from e
    key["sign_count"] = v.new_sign_count
    save(db, user.id, keys)
    return {"ok": True}


@router.delete("/{key_id}")
def remove(key_id: str, user: UserDep, db: SessionDep):
    keys = [k for k in load(db, user.id) if k["id"] != key_id]
    save(db, user.id, keys)
    return [_public(k) for k in keys]
