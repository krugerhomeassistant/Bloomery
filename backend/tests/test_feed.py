from datetime import date, timedelta
from types import SimpleNamespace as L

from app.cycles import Engine, Profile
from app.feed import feed, forecasts, log_note, milestones, recap

D = timedelta
starts = [date(2026, 1, 1) + D(days=28 * i) for i in range(5)]  # 4 complete cycles + current
bleeding = [s + D(days=i) for s in starts for i in range(5)]
# tender breasts 3 days before every period, cramps on day 1
logs = [L(day=s - D(days=3), tags={"symptoms": ["tender_breasts"]}) for s in starts[1:]]
logs += [L(day=s, tags={"symptoms": ["cramps"]}) for s in starts[:-1]]


def eng(today):
    return Engine(Profile(), today, bleeding)


def test_forecast_pms_symptom_before_period():
    today = starts[-1] + D(days=25)  # 3 days before predicted next period
    f = forecasts(eng(today), logs, today)
    assert [c["tag"] for c in f] == ["symptoms:tender_breasts"]
    assert "4 of your last 4 cycles" in f[0]["text"]


def test_forecast_skips_already_logged_and_needs_history():
    today = starts[-1] + D(days=25)
    assert forecasts(eng(today), [*logs, L(day=today, tags={"symptoms": ["tender_breasts"]})], today) == []
    assert forecasts(Engine(Profile(), date(2026, 1, 3), bleeding[:5]), logs, date(2026, 1, 3)) == []


def test_milestones_recap_tip_and_note():
    day1 = starts[-1]
    e = eng(day1)
    assert milestones(e, day1, "track")[0]["title"] == "Your period started"
    r = recap(e, logs, day1)
    assert "28 days" in r["text"] and "right on your average" in r["text"]
    kinds = [c["kind"] for c in feed(e, logs, day1, "track")]
    assert kinds[0] == "milestone" and "recap" in kinds and kinds[-1] == "tip"
    note = log_note(e, [{"tag": "symptoms:cramps", "phase": "menstrual"}], day1, {"symptoms": ["cramps"]})
    assert note.startswith("Cramps during your period matches your usual pattern")
    assert log_note(e, [], day1, {"symptoms": ["fine"]}) is None
