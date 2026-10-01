from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db import get_engine
from app.main import app
from app.models import Setting
from app.routers import auth


def test_pin_lock_and_account_cleanup(monkeypatch):
    monkeypatch.setattr(auth, "registration_open", lambda db: True)  # own throwaway user, others' accounts untouched
    c = TestClient(app)
    assert c.post("/api/auth/register", json={"username": "pinny", "password": "pinpinpin"}).status_code == 200
    assert c.get("/api/auth/me").json()["pin_set"] is False
    assert c.put("/api/auth/pin", json={"password": "nope", "pin": "1234"}).status_code == 400
    assert c.put("/api/auth/pin", json={"password": "pinpinpin", "pin": "12a4"}).status_code == 422
    assert c.put("/api/auth/pin", json={"password": "pinpinpin", "pin": "1234"}).json()["pin_set"] is True
    assert c.post("/api/auth/pin/verify", json={"pin": "1234"}).json() == {"ok": True}
    for i in range(9):
        r = c.post("/api/auth/pin/verify", json={"pin": "0000"})
        assert r.status_code == 400 and f"{9 - i} " in r.json()["detail"]
    assert c.post("/api/auth/pin/verify", json={"pin": "0000"}).status_code == 401
    assert c.get("/api/auth/me").status_code == 401  # session ended
    c.post("/api/auth/login", json={"username": "pinny", "password": "pinpinpin"})
    c.post("/api/tokens/ha")
    uid = c.get("/api/auth/me").json()["id"]
    assert c.delete("/api/account").status_code == 200
    with Session(get_engine()) as db:
        left = [s.key for s in db.exec(select(Setting)) if s.key.endswith(f":{uid}") or s.value == str(uid)]
    assert left == []
