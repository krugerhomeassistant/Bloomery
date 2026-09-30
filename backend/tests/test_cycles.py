from datetime import date, timedelta

from app.cycles import Engine, Profile, derive_periods, detect_thermal_shift

D = timedelta


def bleed(*starts, n=5):
    return [s + D(days=i) for s in starts for i in range(n)]


def test_derive_periods_merges_small_gaps():
    days = [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 4), date(2026, 1, 20)]
    ps = derive_periods(days)
    assert [(p.start, p.end) for p in ps] == [(date(2026, 1, 1), date(2026, 1, 4)), (date(2026, 1, 20), date(2026, 1, 20))]


def test_empty_state():
    e = Engine(Profile(), date(2026, 3, 1), [])
    assert e.status()["state"] == "empty"
    assert e.next_period is None


def test_regular_30_day_cycles_predict_30():
    s = [date(2026, 1, 1) + D(days=30 * i) for i in range(5)]
    e = Engine(Profile(cycle_length=28), s[-1] + D(days=10), bleed(*s))
    assert e.predicted_cycle == 30
    assert e.next_period == s[-1] + D(days=30)
    assert e.current.ovulation == s[-1] + D(days=16)
    assert e.stats()["regularity"] == "regular"


def test_single_period_blends_with_prior():
    e = Engine(Profile(cycle_length=28), date(2026, 1, 3), bleed(date(2026, 1, 1)))
    assert e.status()["state"] == "period"
    assert e.status()["headline"] == "Day 3"
    assert e.next_period == date(2026, 1, 29)


def test_due_and_late():
    start = date(2026, 1, 1)
    e = Engine(Profile(cycle_length=28), start + D(days=28), bleed(start))
    assert e.status()["state"] == "due"
    e = Engine(Profile(cycle_length=28), start + D(days=31), bleed(start))
    st = e.status()
    assert st["state"] == "late" and st["headline"] == "3 days"
    assert e.next_period == start + D(days=32)


def test_fertile_status_and_chance():
    start = date(2026, 1, 1)
    e = Engine(Profile(cycle_length=28), start + D(days=11), bleed(start))  # ov = day 15 (Jan 15)
    st = e.status()
    assert st["state"] == "fertile"
    assert st["headline"] == "3 days"
    assert e.day_info(date(2026, 1, 15))["kind"] == "ovulation"
    assert e.day_info(date(2026, 1, 14))["chance"] == "high"
    assert e.day_info(date(2026, 1, 25))["phase"] == "luteal"


def test_thermal_shift():
    base = date(2026, 1, 1)
    temps = [(base + D(days=i), 36.3 + (0.01 * (i % 3))) for i in range(12)]
    temps += [(base + D(days=12 + i), 36.7) for i in range(4)]
    assert detect_thermal_shift(temps) == base + D(days=11)


def test_calendar_marks_predictions():
    start = date(2026, 1, 1)
    e = Engine(Profile(), date(2026, 1, 10), bleed(start))
    cal = {d["date"]: d for d in e.calendar(date(2026, 1, 1), date(2026, 2, 5))}
    assert cal["2026-01-01"]["kind"] == "period"
    assert cal["2026-01-29"]["kind"] == "predicted_period"
    assert cal["2026-01-29"]["cycle_day"] == 1
