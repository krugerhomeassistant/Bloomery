"""Seed a demo account with ~7 months of realistic data. Usage: python scripts/seed_demo.py [base_url]"""
import random, sys
from datetime import date, timedelta
import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8420"
random.seed(7)
c = httpx.Client(base_url=BASE)
if c.post("/api/auth/register", json={"username": "demo", "password": "demodemo", "display_name": "Mia"}).status_code != 200:
    c.post("/api/auth/login", json={"username": "demo", "password": "demodemo"}).raise_for_status()
c.put("/api/profile", json={"onboarded": True, "cycle_length": 28, "period_length": 5, "goal": "track", "birth_year": 1995})
today = date.today()
lengths = [29, 28, 31, 27, 30, 29, 28]
start = today - timedelta(days=12)
starts = [start]
for L in lengths:
    starts.insert(0, starts[0] - timedelta(days=L))
for s in starts:
    plen = random.choice([4, 5, 5, 6])
    for i in range(plen):
        d = s + timedelta(days=i)
        if d > today: break
        tags = {}
        if i < 2: tags["symptoms"] = random.sample(["cramps", "backache", "fatigue", "headache"], 2)
        if i == 0: tags["mood"] = ["irritated"]
        c.put(f"/api/logs/{d}", json={"flow": ["heavy", "medium", "medium", "light", "light", "light"][i], "tags": tags})
    for k in range(3, 7):  # PMS days before next start
        d = s - timedelta(days=k)
        if s != starts[0] and d <= today:
            c.put(f"/api/logs/{d}", json={"tags": {"mood": random.sample(["mood_swings", "sad", "anxious"], 1),
                                                    "symptoms": ["tender_breasts", "cravings"][: random.randint(1, 2)],
                                                    "digestion": ["bloating"]}})
    for k in (11, 12, 13):
        d = s + timedelta(days=k)
        if d <= today:
            c.put(f"/api/logs/{d}", json={"tags": {"discharge": ["egg_white"], "mood": ["energetic"], "sex": ["high_drive"]}})
for i in range(13):  # BBT for current cycle
    d = start + timedelta(days=i)
    if d <= today:
        r = c.get(f"/api/logs/{d}").json()
        r.pop("day", None); r.pop("updated_at", None)
        r["temperature"] = round(36.35 + random.uniform(-0.08, 0.08), 2)
        r["weight"] = round(61.5 + random.uniform(-0.4, 0.4), 1)
        c.put(f"/api/logs/{d}", json=r)
print(c.get(f"/api/cycle/overview?today={today}").json()["status"])
