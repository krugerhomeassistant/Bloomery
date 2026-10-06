from datetime import date, timedelta

from app.cycles import Engine, Profile, derive_periods, detect_thermal_shift

D = timedelta


def bleed(*starts, n=5):
    return [s + D(days=i) for s in starts for i in range(n)]


def test_derive_periods_merges_small_gaps():
    days = [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 4), date(2026, 1, 20)]
    ps = derive_periods(days)
    assert [(p.start, p.end) for p in ps] == [
        (date(2026, 1, 1), date(2026, 1, 4)),
        (date(2026, 1, 20), date(2026, 1, 20)),
    ]


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


def test_life_stages():
    from datetime import date, timedelta

    from app.cycles import Engine, Profile
    from app.feed import feed, log_note

    starts = [date(2026, 1, 1) + timedelta(days=28 * i) for i in range(4)]
    bleed = [s + timedelta(days=k) for s in starts for k in range(5)]
    today = starts[-1] + timedelta(days=70)  # 10 weeks after last period

    preg = Engine(Profile(mode="pregnancy"), today, bleed)
    p = preg.pregnancy()
    assert (p["week"], p["day"], p["trimester"]) == (10, 0, 1) and p["due"] == (
        starts[-1] + timedelta(days=280)
    ).isoformat()
    assert preg.day_info(today)["kind"] is None and preg.day_info(starts[-1])["kind"] == "period"
    assert preg.status()["state"] == "pregnancy" and preg.next_period is None and preg.flags() == []
    assert feed(preg, [], today, "track")[0]["title"] == "Week 10"
    assert Engine(Profile(mode="pregnancy", lmp=today - timedelta(days=100)), today, bleed).pregnancy()["week"] == 14

    cyc = Engine(Profile(), today, bleed)
    assert "pregnancy mode" in log_note(cyc, [], today, {"pregnancy_test": ["positive"]})
    assert any(f["title"] == "Period is late" for f in cyc.flags())

    peri = Engine(Profile(mode="perimenopause"), today, bleed)
    assert peri.variability >= 5 and peri.status()["label"] == "Days since period"
    assert [f["title"] for f in peri.flags()] == ["No period for 66 days"]
    assert (
        Engine(Profile(mode="perimenopause"), today + timedelta(days=300), bleed).flags()[0]["title"]
        == "12 months without a period"
    )


def test_symptom_heatmap():
    from app.cycles import symptom_heatmap

    starts = [date(2026, 1, 1) + D(days=28 * i) for i in range(4)]
    eng = Engine(Profile(), starts[-1] + D(days=10), bleed(*starts))
    logs = [(s + D(days=1), {"symptoms": ["cramps"]}) for s in starts]  # cycle day 2, every cycle
    logs += [(starts[0] + D(days=25), {"symptoms": ["cramps", "fine"]})]
    h = symptom_heatmap(eng, logs, {"symptoms:cramps": "Cramps"})
    assert h["days"] == 28 and h["cycles"] == 4 and h["period_days"] == 5
    row = h["rows"][0]
    assert row["label"] == "Cramps" and row["share"][1] == 1.0 and row["share"][0] == 0
    assert row["share"][25] == round(1 / 3, 2)  # day 26 reached by the 3 finished cycles only
    assert all(r["tag"] != "symptoms:fine" for r in h["rows"])
