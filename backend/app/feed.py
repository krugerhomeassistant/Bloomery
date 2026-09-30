"""Rule-based daily feed: symptom forecasts, milestones, cycle recap, phase tips, after-log notes.
Pure functions over Engine + logs; no AI needed (AI daily insight gets the forecasts as context)."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta

from .catalog import CATALOG, LABELS
from .cycles import Engine, Segment

FORECAST_CATS = {"symptoms", "mood", "digestion", "discharge"}
SKIP = {"none", "fine"}
EMOJI = {f"{c['id']}:{i}": e for c in CATALOG for i, _, e in c["items"]}
PHASE_WORDS = {"menstrual": "during your period", "follicular": "after your period",
               "fertile": "around ovulation", "ovulation": "around ovulation", "luteal": "before your period"}

PHASE_TIPS = {
    "menstrual": [
        "A heating pad on your lower belly relaxes the uterine muscles and can ease cramps.",
        "You lose iron while bleeding — lentils, spinach, red meat or beans with vitamin C help replace it.",
        "Gentle movement like walking or yoga can reduce cramps more than you'd expect.",
        "Prostaglandins peak in the first days; anti-inflammatory painkillers work best taken early.",
    ],
    "follicular": [
        "Rising estrogen often means more energy — a good week for tougher workouts or new projects.",
        "Many people find focus and mood lift now. Plan demanding tasks for this stretch.",
        "Your skin often looks its best in this phase as estrogen rises.",
        "Great time to try something new: motivation and stamina tend to be higher.",
    ],
    "fertile": [
        "Cervical fluid often turns clear and stretchy (like egg white) near ovulation.",
        "Libido often rises around ovulation — that's estrogen and testosterone peaking.",
        "Some people feel a brief one-sided twinge (mittelschmerz) when they ovulate.",
        "Sperm can survive up to 5 days, which is why the fertile window starts before ovulation.",
    ],
    "luteal": [
        "Progesterone rises now and can make you sleepier — an earlier bedtime helps.",
        "Cravings are common before your period. Complex carbs and magnesium-rich foods (nuts, dark chocolate) can help.",
        "Cutting back on salt and caffeine this week can reduce bloating and breast tenderness.",
        "Your body temperature is slightly higher now, so you may sleep better in a cooler room.",
    ],
}
PHASE_TIPS["ovulation"] = PHASE_TIPS["fertile"]

SYMPTOM_TIPS = {
    "symptoms:cramps": "Heat, gentle stretching and staying hydrated can take the edge off.",
    "symptoms:headache": "Hormone dips can trigger headaches — water, regular meals and rest help.",
    "symptoms:tender_breasts": "A soft, supportive bra and less salt/caffeine can ease tenderness.",
    "symptoms:fatigue": "Iron-rich food and an earlier night can help your energy recover.",
    "symptoms:insomnia": "Try a cooler room and no screens for the last hour before bed.",
    "symptoms:backache": "Heat on your lower back and gentle cat-cow stretches can help.",
    "symptoms:acne": "Hormonal breakouts often follow the cycle — be gentle and avoid over-scrubbing.",
    "symptoms:cravings": "Totally normal. Pair treats with protein or fibre to avoid energy crashes.",
    "digestion:bloating": "Less salt, more water and a short walk after meals can reduce bloating.",
    "digestion:nausea": "Small, bland meals and ginger tea can settle your stomach.",
    "mood:anxious": "Slow breathing (in 4, out 6) for a couple of minutes calms the nervous system.",
    "mood:irritated": "Hormone shifts can shorten your fuse — a short walk or some quiet time helps.",
    "mood:sad": "Be kind to yourself today. If low mood lasts for weeks, talk to someone you trust or a professional.",
    "mood:mood_swings": "Regular meals and sleep smooth out the hormonal rollercoaster a little.",
}


def _card(kind: str, emoji: str, title: str, text: str) -> dict:
    return {"kind": kind, "emoji": emoji, "title": title, "text": text}


def _tags(tags: dict | None) -> set[str]:
    return {f"{c}:{v}" for c, vs in (tags or {}).items() if c in FORECAST_CATS for v in vs if v not in SKIP}


def forecasts(eng: Engine, logs: list, today: date, limit: int = 3) -> list[dict]:
    """Tags logged near this point (±1 day) in ≥2 past cycles and ≥50% of cycles with logs.
    Aligned both to cycle start (period-type symptoms) and to next period (PMS-type); best alignment wins."""
    cur, nxt = eng.current, eng.next_period
    if not cur or not nxt:
        return []
    done = [s for s in eng.segments if not s.predicted and s.end < cur.start]
    by_seg: dict[int, list[tuple[date, set[str]]]] = defaultdict(list)
    for l in logs:
        for i, s in enumerate(done):
            if s.start <= l.day <= s.end:
                by_seg[i].append((l.day, _tags(l.tags)))
    cycles = [i for i, v in by_seg.items() if any(t for _, t in v)]
    if len(cycles) < 2:
        return []
    t_start, t_end = (today - cur.start).days, (today - nxt).days
    hits: Counter = Counter()
    for i in cycles:
        s: Segment = done[i]
        near = set()
        for d, tags in by_seg[i]:
            if abs((d - s.start).days - t_start) <= 1 or abs((d - (s.end + timedelta(days=1))).days - t_end) <= 1:
                near |= tags
        hits.update(near)
    logged_today = next((_tags(l.tags) for l in logs if l.day == today), set())
    out = []
    for tag, n in hits.most_common():
        if n < 2 or n / len(cycles) < 0.5 or tag in logged_today:
            continue
        label = LABELS.get(tag, tag).lower()
        verb = "feel" if tag.startswith("mood:") else "notice"
        out.append({**_card("forecast", EMOJI.get(tag, "🔮"), f"Heads-up: {LABELS.get(tag, tag)}",
                            f"You might {verb} {label} today — you logged it around this point in {n} of your last {len(cycles)} cycles."
                            + (f" {SYMPTOM_TIPS[tag]}" if tag in SYMPTOM_TIPS else "")), "tag": tag})
        if len(out) == limit:
            break
    return out


def milestones(eng: Engine, today: date, goal: str) -> list[dict]:
    cur, nxt = eng.current, eng.next_period
    if not cur:
        return []
    st = eng.status()
    out = []
    if today == cur.start:
        out.append(_card("milestone", "🌺", "Your period started", "Day 1 of a new cycle. Rest if you need it and keep a heat pad handy."))
    if today == cur.fertile_start:
        text = "Your fertile window opens today and lasts about 6 days." + (
            " These are your best days to try." if goal == "conceive" else " Chance of pregnancy is higher until it closes.")
        out.append(_card("milestone", "🌼", "Fertile window starts", text))
    if today == cur.ovulation:
        out.append(_card("milestone", "✨", "Estimated ovulation day",
                         "Your egg is likely released today" + (" (confirmed by your temperature)." if cur.ovulation_confirmed else ".")))
    if st.get("state") == "cycle" and nxt and 1 <= (nxt - today).days <= 3:
        n = (nxt - today).days
        out.append(_card("milestone", "👜", f"Period in {n} day{'s' if n > 1 else ''}", "Good time to pack pads, tampons or your cup."))
    if st.get("state") == "late":
        text = ("Stress, travel, illness or sleep changes can delay a period. "
                "If pregnancy is possible, a home test is reliable from the day your period was due.")
        out.append(_card("milestone", "⏳", f"Period late by {st['headline']}", text))
    return out


def recap(eng: Engine, logs: list, today: date) -> dict | None:
    """Shown during the first 4 days of a new cycle, summarising the one that just ended."""
    cur = eng.current
    if not cur or cur.predicted or (today - cur.start).days > 3:
        return None
    prev = next((s for s in reversed(eng.segments) if not s.predicted and s.end < cur.start), None)
    if not prev:
        return None
    avg = eng.stats()["avg_cycle_length"]
    top = Counter(t for l in logs if prev.start <= l.day <= prev.end for t in _tags(l.tags)).most_common(3)
    text = f"It lasted {prev.length} days"
    if avg:
        diff = prev.length - avg
        text += " — right on your average." if abs(diff) < 1.5 else f" — {abs(diff):.0f} days {'longer' if diff > 0 else 'shorter'} than your average of {avg:g}."
    text += f" Your period was {(prev.period_end - prev.start).days + 1} days."
    if top:
        text += " Most logged: " + ", ".join(LABELS.get(t, t).lower() for t, _ in top) + "."
    return _card("recap", "📊", "Last cycle recap", text)


def tip(eng: Engine, today: date) -> dict | None:
    phase = eng.day_info(today)["phase"]
    tips = PHASE_TIPS.get(phase or "")
    if not tips:
        return None
    return _card("tip", "💡", "Tip for this phase", tips[today.toordinal() % len(tips)])


def feed(eng: Engine, logs: list, today: date, goal: str) -> list[dict]:
    return [c for c in [*milestones(eng, today, goal), recap(eng, logs, today), *forecasts(eng, logs, today), tip(eng, today)] if c]


def log_note(eng: Engine, patterns: list[dict], day: date, tags: dict) -> str | None:
    """Short note after saving a log: pattern match and/or a tip for the logged symptom."""
    logged = sorted(_tags(tags), key=lambda t: t not in SYMPTOM_TIPS)
    if not logged:
        return None
    phase = eng.day_info(day)["phase"]
    phase = "fertile" if phase == "ovulation" else phase
    usual = {p["tag"]: p["phase"] for p in patterns}
    for t in logged:
        label = LABELS.get(t, t)
        if usual.get(t) == phase:
            return f"{label} {PHASE_WORDS.get(phase, '')} matches your usual pattern. " + SYMPTOM_TIPS.get(t, "")
    t = logged[0]
    return SYMPTOM_TIPS.get(t) and f"{LABELS.get(t, t)}: {SYMPTOM_TIPS[t]}"
