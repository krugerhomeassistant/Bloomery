"""Birth control schedules, endpoint, and hidden fertility predictions on hormonal methods."""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.contraception import status
from app.cycles import Engine, Profile
from app.db import init_db
from app.main import app

D0 = date(2026, 1, 1)


def at(cfg: dict, days: int) -> dict:
    return status(cfg, D0 + timedelta(days=days))


def test_schedules():
    pill = {"method": "pill", "start": "2026-01-01", "pill_type": "21_7"}
    assert at(pill, 0)["title"] == "Pill day 1" and at(pill, 0)["action"]
    assert "Break starts in 2 days" in at(pill, 18)["text"]
    assert at(pill, 21)["title"] == "Break day 1 of 7" and not at(pill, 21)["action"]
    assert at(pill, 27)["action"] and "Thu 29 Jan" in at(pill, 27)["text"]  # last break day (28 Jan): new pack tomorrow
    assert at(pill, 28)["title"] == "Pill day 1"
    assert at({**pill, "pill_type": "24_4"}, 24)["title"] == "Break day 1 of 4"
    assert "new pack tomorrow" in at({**pill, "pill_type": "28"}, 27)["text"]
    assert at({**pill, "pill_type": "pop"}, 40)["title"] == "Take your pill"

    ring = {"method": "ring", "start": "2026-01-01"}
    assert [at(ring, d)["title"] for d in (0, 20, 21, 25, 27, 28)] == [
        "Ring week 1",
        "Remove your ring tomorrow",
        "Remove your ring today",
        "Ring-free day 5",
        "Insert a new ring tomorrow",
        "Ring week 1",
    ]
    patch = {"method": "patch", "start": "2026-01-01"}
    assert [at(patch, d)["title"] for d in (0, 7, 14, 21, 24, 27)] == [
        "Patch 1 of 3",
        "Change your patch today",
        "Change your patch today",
        "Take your patch off today",
        "Patch-free day 4",
        "New patch tomorrow",
    ]

    inj = {"method": "injection", "start": "2026-01-01"}
    assert at(inj, 7 * 13 - 7)["action"] and at(inj, 91)["title"] == "Injection due today"
    assert at(inj, 95)["title"] == "Injection overdue"
    iud = {"method": "iud_copper", "start": "2025-06-01", "expires": "2026-02-15"}
    assert at(iud, 0)["title"] == "IUD replacement due"
    assert (
        status({"method": "iud_copper", "start": "2025-06-01"}, date(2026, 3, 1))["title"] == "Monthly IUD string check"
    )
    assert status({"method": "implant", "start": "2025-06-01"}, date(2026, 3, 1))["title"] == "implant in place"
    assert status({"method": "condom"}, D0) is None and status(None, D0) is None


def test_hormonal_hides_fertility():
    starts = [D0 + timedelta(days=28 * i) for i in range(4)]
    bleed = [s + timedelta(days=k) for s in starts for k in range(5)]
    today = starts[-1] + timedelta(days=12)
    normal, horm = Engine(Profile(), today, bleed), Engine(Profile(hormonal=True), today, bleed)
    assert normal.status()["state"] == "fertile" and normal.day_info(today)["kind"] == "fertile"
    assert horm.status()["state"] == "cycle" and horm.day_info(today)["kind"] is None
    assert horm.day_info(today)["chance"] is None and "hidden" in horm.status()["sub"]
    assert horm.next_period == normal.next_period  # withdrawal bleeds are still predicted


def test_contraception_endpoint_and_notification():
    init_db()
    c = TestClient(app)
    c.post("/api/auth/login", json={"username": "ana", "password": "supersecret"})
    if c.get("/api/auth/me").status_code != 200:
        c.post("/api/auth/register", json={"username": "ana", "password": "supersecret"})
    assert c.get("/api/contraception").json()["config"]["method"] == "none"
    assert c.put("/api/contraception", json={"method": "ring"}).status_code == 422
    r = c.put("/api/contraception?today=2026-01-22", json={"method": "ring", "start": "2026-01-01"}).json()
    assert r["status"]["title"] == "Remove your ring today"
    feed = c.get("/api/feed?today=2026-01-22").json()
    assert feed[0]["kind"] == "contraception"
    assert c.get("/api/cycle/overview?today=2026-01-22").json()["hormonal"] is True

    from sqlmodel import Session

    from app import notify
    from app.db import get_engine
    from app.models import User

    with Session(get_engine()) as db:
        user = db.get(User, c.get("/api/auth/me").json()["id"])
        title, _ = notify.compose(db, user, date(2026, 1, 22), ["pill"])
        assert "Remove your ring today" in title
        assert notify.compose(db, user, date(2026, 1, 10), ["pill"]) is None  # nothing to do today
    c.put("/api/contraception", json={"method": "none"})
    assert c.get("/api/cycle/overview").json()["hormonal"] is False
