import os
import tempfile

os.environ["BLOOMERY_DATA_DIR"] = tempfile.mkdtemp()
os.environ["BLOOMERY_STATIC_DIR"] = "/nonexistent"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_full_flow():
    with TestClient(app) as c:
        assert c.get("/api/auth/status").json()["registration_open"] is True
        assert c.get("/api/cycle/overview").status_code == 401
        r = c.post("/api/auth/register", json={"username": "Ana", "password": "supersecret"})
        assert r.status_code == 200, r.text
        # auto mode: registration closes after first user
        assert c.get("/api/auth/status").json()["registration_open"] is False

        assert c.put("/api/profile", json={"cycle_length": 29, "onboarded": True}).json()["cycle_length"] == 29
        assert c.post("/api/period/start?today=2026-01-03", json={"day": "2026-01-01"}).json()["days"] == 5
        ov = c.get("/api/cycle/overview?today=2026-01-03").json()
        assert ov["status"]["state"] == "period"
        assert ov["next_period"] == "2026-01-30"

        r = c.put("/api/logs/2026-01-02", json={"flow": "heavy", "tags": {"symptoms": ["cramps"], "mood": ["sad"]},
                                                "temperature": 36.4})
        assert r.status_code == 200, r.text
        assert c.put("/api/logs/2026-01-02", json={"tags": {"symptoms": ["nope"]}}).status_code == 422

        c.post("/api/period/end", json={"day": "2026-01-03"})
        cal = c.get("/api/cycle/calendar?start=2026-01-01&end=2026-01-31&today=2026-01-10").json()
        kinds = {d["date"]: d["kind"] for d in cal}
        assert kinds["2026-01-03"] == "period" and kinds["2026-01-04"] is None
        assert kinds["2026-01-30"] == "predicted_period"

        ins = c.get("/api/insights?today=2026-01-10").json()
        assert ins["symptoms"]["top"][0]["count"] == 1
        d = c.get("/api/ai/daily?today=2026-01-10").json()
        assert d["source"] == "rules" and d["content"]
        assert c.post("/api/ai/chat", json={"message": "hi"}).status_code == 503

        exp = c.get("/api/export").json()
        assert len(exp["logs"]) == 3
        assert c.post("/api/import", json={"logs": exp["logs"], "replace": True}).json()["imported"] == 3
        c.post("/api/auth/logout")
        assert c.post("/api/auth/login", json={"username": "ana", "password": "wrongpass1"}).status_code == 401
        assert c.post("/api/auth/login", json={"username": "ana", "password": "supersecret"}).status_code == 200
