from fastapi.testclient import TestClient

from app.main import app


def test_partner_share_link():
    with TestClient(app) as owner:
        owner.post("/api/auth/login", json={"username": "ana", "password": "supersecret"})
        if owner.get("/api/auth/me").status_code != 200:
            owner.post("/api/auth/register", json={"username": "ana", "password": "supersecret"})
        owner.post("/api/period/start?today=2026-02-01", json={"day": "2026-02-01"})
        owner.put("/api/logs/2026-02-02", json={"tags": {"sex": ["unprotected"], "mood": ["sad"]}, "notes": "private"})
        assert owner.get("/api/tokens/share").json() == {"token": None}
        token = owner.post("/api/tokens/share").json()["token"]
        assert owner.get("/api/tokens/share").json()["token"] == token

    with TestClient(app) as partner:  # no login
        v = partner.get(f"/api/share/{token}?today=2026-02-02")
        assert v.status_code == 200
        body = v.text
        assert v.json()["status"]["state"] == "period" and v.json()["tip"] and len(v.json()["days"]) == 35
        for secret in ("unprotected", "sad", "private", "supersecret", "password"):
            assert secret not in body
        assert partner.get("/api/tokens/share").status_code == 401  # managing links needs login

    with TestClient(app) as owner:
        owner.post("/api/auth/login", json={"username": "ana", "password": "supersecret"})
        new = owner.post("/api/tokens/share").json()["token"]  # regenerate → old link dies
        assert owner.get(f"/api/share/{token}").status_code == 404
        owner.delete("/api/tokens/share")
        assert owner.get(f"/api/share/{new}").status_code == 404


def test_home_assistant_feeds():
    with TestClient(app) as c:
        c.post("/api/auth/login", json={"username": "ana", "password": "supersecret"})
        t = c.post("/api/tokens/ha").json()["token"]
        assert c.get("/api/tokens/share").json()["token"] != t  # independent from partner link
    with TestClient(app) as ha:  # no session, token only
        j = ha.get(f"/api/ha/{t}?tz=Africa/Johannesburg").json()
        assert {"cycle_day", "phase", "in_period", "fertile", "days_until_period", "next_period"} <= j.keys()
        assert isinstance(j["in_period"], bool)
        ics = ha.get(f"/api/ha/{t}/calendar.ics")
        assert ics.headers["content-type"].startswith("text/calendar")
        assert ics.text.startswith("BEGIN:VCALENDAR\r\n") and "SUMMARY:Predicted period" in ics.text
        assert ha.get("/api/ha/nope").status_code == 404
        assert ha.get(f"/api/share/{t}").status_code == 404  # HA token can't open partner view
