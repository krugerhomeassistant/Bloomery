"""Doctor's report: a summary of the last N months for a GP or gynaecologist (rendered as a printable page).

Leaves out sex and activity logs; notes only when asked for.
"""

from __future__ import annotations

import statistics
from collections import Counter
from datetime import date, timedelta
from typing import Any

from .catalog import LABELS
from .cycles import Engine, symptom_heatmap, symptom_patterns

REPORT_CATS = {"symptoms", "mood", "digestion", "discharge"}
SKIP = {"none", "fine"}


def _tags(tags: dict | None, cats: set[str] = REPORT_CATS) -> list[str]:
    return [f"{c}:{v}" for c, vs in (tags or {}).items() if c in cats for v in vs if v not in SKIP]


def build(eng: Engine, logs: list, user: Any, today: date, months: int, include_notes: bool) -> dict[str, Any]:
    since = today - timedelta(days=round(months * 30.44))
    window = sorted((l for l in logs if since <= l.day <= today), key=lambda l: l.day)
    segs = [s for s in eng.segments if not s.predicted and s.end >= since and s.start <= today]
    by_day = {l.day: l for l in window}

    cycles = []
    for s in segs:
        done = s.end < today and s is not eng.current
        days = [by_day[d] for d in (s.start + timedelta(n) for n in range(s.length)) if d in by_day]
        flows = Counter(l.flow for l in days if l.flow and l.day <= s.period_end)
        spotting = sum(
            1
            for l in days
            if l.day > s.period_end and (l.flow == "spotting" or "spotting" in (l.tags or {}).get("discharge", []))
        )
        top = Counter(t for l in days for t in _tags(l.tags)).most_common(4)
        cycles.append(
            {
                "start": s.start.isoformat(),
                "length": s.length if done else None,
                "days_so_far": None if done else (today - s.start).days + 1,
                "period_length": (s.period_end - s.start).days + 1,
                "heavy_days": flows.get("heavy", 0),
                "spotting_days": spotting,
                "ovulation": s.ovulation.isoformat(),
                "ovulation_confirmed": s.ovulation_confirmed,
                "top": [LABELS.get(t, t.split(":")[1]) for t, _ in top],
            }
        )

    lengths = [c["length"] for c in cycles if c["length"]]
    periods = [c["period_length"] for c in cycles if c["length"]]
    pairs = [(l.day, {k: v for k, v in (l.tags or {}).items() if k in REPORT_CATS}) for l in window]
    counts = Counter(t for l in window for t in _tags(l.tags))
    pills = Counter(v for l in window for v in (l.tags or {}).get("pill", []))
    tests = [
        {"date": l.day.isoformat(), "test": cat.replace("_", " "), "result": v}
        for l in window
        for cat in ("ovulation_test", "pregnancy_test")
        for v in (l.tags or {}).get(cat, [])
        if v in ("positive", "faint")
    ]
    ov = eng.overview()
    return {
        "generated": today.isoformat(),
        "since": since.isoformat(),
        "months": months,
        "patient": {
            "name": user.display_name or user.username,
            "age": today.year - user.birth_year if user.birth_year else None,
            "goal": user.goal,
            "life_stage": eng.profile.mode,
            "pregnancy": ov["pregnancy"],
        },
        "summary": {
            "cycles": len(lengths),
            "avg_cycle": round(statistics.mean(lengths), 1) if lengths else None,
            "min_cycle": min(lengths) if lengths else None,
            "max_cycle": max(lengths) if lengths else None,
            "sd_cycle": round(statistics.pstdev(lengths), 1) if len(lengths) >= 2 else None,
            "avg_period": round(statistics.mean(periods), 1) if periods else None,
            "last_period": segs[-1].start.isoformat() if segs else None,
            "next_period": ov["next_period"],
            "regularity": eng.stats()["regularity"],
            "luteal": eng.luteal,
            "bbt_confirmed": sum(1 for c in cycles if c["ovulation_confirmed"]),
        },
        "cycles": list(reversed(cycles)),
        "flags": eng.flags(),
        "symptoms": [{"label": LABELS.get(t, t.split(":")[1]), "days": n} for t, n in counts.most_common(12)],
        "patterns": symptom_patterns(eng, pairs, LABELS)["patterns"],
        "heatmap": symptom_heatmap(eng, pairs, LABELS, since=since),
        "temperature": [{"date": l.day.isoformat(), "value": l.temperature} for l in window if l.temperature],
        "pill": {"taken": pills.get("taken", 0), "missed": pills.get("missed", 0)} if pills else None,
        "tests": tests,
        "notes": [{"date": l.day.isoformat(), "text": l.notes} for l in window if l.notes] if include_notes else [],
    }
