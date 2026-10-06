"""Quick logging with an API key (Home Assistant actions, Siri Shortcuts)."""

from fastapi.testclient import TestClient

from app.db import init_db
from app.main import app


def test_quick_log_with_api_key():
    init_db()
    owner = TestClient(app)
    owner.post("/api/auth/login", json={"username": "ana", "password": "supersecret"})
    if owner.get("/api/auth/me").status_code != 200:
        owner.post("/api/auth/register", json={"username": "ana", "password": "supersecret"})
    key = owner.post("/api/tokens/api").json()["token"]
    assert key != owner.get("/api/tokens/ha").json()["token"]

    bot = TestClient(app, headers={"Authorization": f"Bearer {key}"})
    assert TestClient(app).post("/api/quick/log", json={"tags": ["cramps"]}).status_code == 401
    assert TestClient(app, headers={"Authorization": "Bearer nope"}).get("/api/quick/catalog").status_code == 401
    assert bot.get("/api/auth/me").status_code == 401  # key only opens /api/quick
    assert bot.delete("/api/account").status_code == 401

    assert bot.post("/api/quick/period-start", json={"day": "2026-05-01"}).json()["days"] >= 3
    assert owner.get("/api/logs/2026-05-01").json()["flow"] == "medium"

    r = bot.post(
        "/api/quick/log", json={"day": "2026-05-02", "tags": ["Cramps", "mood:sad", "headache"], "note": "rough day"}
    )
    assert r.json()["logged"] == ["Cramps", "Sad", "Headache"]
    r = bot.post(
        "/api/quick/log",
        json={
            "day": "2026-05-02",
            "tags": ["cramps", "Bloating"],
            "flow": "heavy",
            "temperature": 97.9,
            "temperature_unit": "F",
            "note": "better later",
        },
    )
    log = owner.get("/api/logs/2026-05-02").json()
    assert (
        log["tags"]["symptoms"].count("cramps") == 1
        and "sad" in log["tags"]["mood"]
        and log["tags"]["digestion"] == ["bloating"]
    )
    assert log["flow"] == "heavy" and log["temperature"] == 36.61 and log["notes"] == "rough day\nbetter later"

    assert bot.post("/api/quick/log", json={"tags": ["unicorns"]}).status_code == 422
    assert bot.post("/api/quick/log", json={}).status_code == 422
    assert bot.post("/api/quick/log", json={"temperature": 20}).status_code == 422
    assert bot.post("/api/quick/log", json={"tz": "Mars/Base", "tags": ["cramps"]}).status_code == 422
    assert bot.post("/api/quick/log", json={"tz": "Africa/Johannesburg", "tags": ["cramps"]}).json()["ok"]
    assert any(c["id"] == "symptoms" for c in bot.get("/api/quick/catalog").json()["categories"])

    owner.delete("/api/tokens/api")
    assert bot.post("/api/quick/log", json={"tags": ["cramps"]}).status_code == 401


def test_wrist_temperature_import_and_units():
    from datetime import date

    from app.importers import _apple

    days = _apple(
        [
            ["AppleSleepingWristTemperature", "2026-03-02", "35.12", "degC"],
            ["AppleSleepingWristTemperature", "2026-03-03", "95.5", "degF"],
            ["BasalBodyTemperature", "2026-03-03", "36.55", "degC"],  # thermometer wins on the same morning
            ["AppleSleepingWristTemperature", "2026-03-03", "35.40", "degC"],
        ]
    )
    assert days[date(2026, 3, 2)]["temperature"] == 35.12
    assert days[date(2026, 3, 3)]["temperature"] == 36.55

    init_db()
    owner = TestClient(app)
    owner.post("/api/auth/login", json={"username": "ana", "password": "supersecret"})
    key = owner.post("/api/tokens/api").json()["token"]
    bot = TestClient(app, headers={"Authorization": f"Bearer {key}"})
    assert bot.post(
        "/api/quick/log", json={"day": "2026-03-05", "temperature": 95.36, "temperature_unit": "°F"}
    ).json()["ok"]
    assert owner.get("/api/logs/2026-03-05").json()["temperature"] == 35.2
    assert bot.post(
        "/api/quick/log", json={"day": "2026-03-06", "temperature": 34.876, "temperature_unit": "ºC"}
    ).json()["ok"]
    assert owner.get("/api/logs/2026-03-06").json()["temperature"] == 34.88
