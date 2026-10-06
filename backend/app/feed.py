"""Rule-based daily feed: symptom forecasts, milestones, cycle recap, phase tips, after-log notes.
Pure functions over Engine + logs; no AI needed (AI daily insight gets the forecasts as context)."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta

from .catalog import CATALOG, LABELS
from .cycles import Engine, Segment
from .i18n import N_, _, fmt_date, plural

FORECAST_CATS = {"symptoms", "mood", "digestion", "discharge"}
SKIP = {"none", "fine"}
EMOJI = {f"{c['id']}:{i}": e for c in CATALOG for i, _, e in c["items"]}
PHASE_WORDS = {
    "menstrual": N_("during your period"),
    "follicular": N_("after your period"),
    "fertile": N_("around ovulation"),
    "ovulation": N_("around ovulation"),
    "luteal": N_("before your period"),
}

PHASE_TIPS = {
    "menstrual": [
        N_("A heating pad on your lower belly relaxes the uterine muscles and can ease cramps."),
        N_("You lose iron while bleeding — lentils, spinach, red meat or beans with vitamin C help replace it."),
        N_("Gentle movement like walking or yoga can reduce cramps more than you'd expect."),
        N_("Prostaglandins peak in the first days; anti-inflammatory painkillers work best taken early."),
    ],
    "follicular": [
        N_("Rising estrogen often means more energy — a good week for tougher workouts or new projects."),
        N_("Many people find focus and mood lift now. Plan demanding tasks for this stretch."),
        N_("Your skin often looks its best in this phase as estrogen rises."),
        N_("Great time to try something new: motivation and stamina tend to be higher."),
    ],
    "fertile": [
        N_("Cervical fluid often turns clear and stretchy (like egg white) near ovulation."),
        N_("Libido often rises around ovulation — that's estrogen and testosterone peaking."),
        N_("Some people feel a brief one-sided twinge (mittelschmerz) when they ovulate."),
        N_("Sperm can survive up to 5 days, which is why the fertile window starts before ovulation."),
    ],
    "luteal": [
        N_("Progesterone rises now and can make you sleepier — an earlier bedtime helps."),
        N_(
            "Cravings are common before your period. Complex carbs and magnesium-rich foods (nuts, dark chocolate) can help."
        ),
        N_("Cutting back on salt and caffeine this week can reduce bloating and breast tenderness."),
        N_("Your body temperature is slightly higher now, so you may sleep better in a cooler room."),
    ],
}
PHASE_TIPS["ovulation"] = PHASE_TIPS["fertile"]

SYMPTOM_TIPS = {
    "symptoms:cramps": N_("Heat, gentle stretching and staying hydrated can take the edge off."),
    "symptoms:headache": N_("Hormone dips can trigger headaches — water, regular meals and rest help."),
    "symptoms:tender_breasts": N_("A soft, supportive bra and less salt/caffeine can ease tenderness."),
    "symptoms:fatigue": N_("Iron-rich food and an earlier night can help your energy recover."),
    "symptoms:insomnia": N_("Try a cooler room and no screens for the last hour before bed."),
    "symptoms:backache": N_("Heat on your lower back and gentle cat-cow stretches can help."),
    "symptoms:acne": N_("Hormonal breakouts often follow the cycle — be gentle and avoid over-scrubbing."),
    "symptoms:cravings": N_("Totally normal. Pair treats with protein or fibre to avoid energy crashes."),
    "digestion:bloating": N_("Less salt, more water and a short walk after meals can reduce bloating."),
    "digestion:nausea": N_("Small, bland meals and ginger tea can settle your stomach."),
    "mood:anxious": N_("Slow breathing (in 4, out 6) for a couple of minutes calms the nervous system."),
    "mood:irritated": N_("Hormone shifts can shorten your fuse — a short walk or some quiet time helps."),
    "mood:sad": N_(
        "Be kind to yourself today. If low mood lasts for weeks, talk to someone you trust or a professional."
    ),
    "mood:mood_swings": N_("Regular meals and sleep smooth out the hormonal rollercoaster a little."),
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
    cycles = [i for i, v in by_seg.items() if any(t for _d, t in v)]
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
        label = _(LABELS.get(tag, tag))
        sentence = (
            "You might feel {label} today: you logged it around this point in {n} of your last {total} cycles."
            if tag.startswith("mood:")
            else "You might notice {label} today: you logged it around this point in {n} of your last {total} cycles."
        )
        out.append(
            {
                **_card(
                    "forecast",
                    EMOJI.get(tag, "🔮"),
                    _("Heads-up: {label}", label=label),
                    _(sentence, label=label.lower(), n=n, total=len(cycles))
                    + (f" {_(SYMPTOM_TIPS[tag])}" if tag in SYMPTOM_TIPS else ""),
                ),
                "tag": tag,
            }
        )
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
        out.append(
            _card(
                "milestone",
                "🌺",
                _("Your period started"),
                _("Day 1 of a new cycle. Rest if you need it and keep a heat pad handy."),
            )
        )
    if today == cur.fertile_start:
        text = _("Your fertile window opens today and lasts about 6 days.") + (
            _(" These are your best days to try.")
            if goal == "conceive"
            else _(" Chance of pregnancy is higher until it closes.")
        )
        out.append(_card("milestone", "🌼", _("Fertile window starts"), text))
    if today == cur.ovulation:
        out.append(
            _card(
                "milestone",
                "✨",
                _("Estimated ovulation day"),
                _("Your egg is likely released today (confirmed by your temperature).")
                if cur.ovulation_confirmed
                else _("Your egg is likely released today."),
            )
        )
    if st.get("state") == "cycle" and nxt and 1 <= (nxt - today).days <= 3:
        n = (nxt - today).days
        out.append(
            _card(
                "milestone",
                "👜",
                plural(n, "Period in {n} day", "Period in {n} days"),
                _("Good time to pack pads, tampons or your cup."),
            )
        )
    if st.get("state") == "late":
        text = _(
            "Stress, travel, illness or sleep changes can delay a period. "
            "If pregnancy is possible, a home test is reliable from the day your period was due."
        )
        out.append(_card("milestone", "⏳", _("Period late by {days}", days=st["headline"]), text))
    return out


def recap(eng: Engine, logs: list, today: date) -> dict | None:
    """Shown during the first 4 days of a new cycle, summarising the one that just ended."""
    cur = eng.current
    if not cur or cur.predicted or (today - cur.start).days > 3:
        return None
    prev = next((s for s in reversed(eng.segments) if not s.predicted and s.end < cur.start), None)
    if not prev:
        return None
    return {
        **_card("recap", "📊", _("Last cycle recap"), cycle_summary(eng, logs, prev)),
        "start": prev.start.isoformat(),
    }


def cycle_summary(eng: Engine, logs: list, seg: Segment) -> str:
    """Rule-based one-paragraph recap of a (completed) cycle; also the AI recap fallback."""
    avg = eng.stats()["avg_cycle_length"]
    top = Counter(t for l in logs if seg.start <= l.day <= seg.end for t in _tags(l.tags)).most_common(3)
    text = _("It lasted {n} days", n=seg.length)
    if avg:
        diff = seg.length - avg
        if abs(diff) < 1.5:
            text += _(", right on your average.")
        elif diff > 0:
            text += _(", {n} days longer than your average of {avg}.", n=f"{abs(diff):.0f}", avg=f"{avg:g}")
        else:
            text += _(", {n} days shorter than your average of {avg}.", n=f"{abs(diff):.0f}", avg=f"{avg:g}")
    text += " " + _("Your period was {n} days.", n=(seg.period_end - seg.start).days + 1)
    if top:
        text += " " + _("Most logged: {items}.", items=", ".join(_(LABELS.get(t, t)).lower() for t, _n in top))
    return text


def tip(eng: Engine, today: date) -> dict | None:
    phase = eng.day_info(today)["phase"]
    tips = PHASE_TIPS.get(phase or "")
    if not tips:
        return None
    return _card("tip", "💡", _("Tip for this phase"), _(tips[today.toordinal() % len(tips)]))


TRIMESTER_TIPS = {
    1: [
        N_("Take a daily prenatal vitamin with folic acid, ideally 400 mcg."),
        N_("Nausea? Small, frequent snacks and ginger often help. Seek care if you can't keep fluids down."),
        N_("Tiredness is normal this trimester. Rest when you can."),
        N_("Book your first prenatal appointment if you haven't yet."),
    ],
    2: [
        N_("Many people feel more energetic now. A good time for gentle exercise like walking or swimming."),
        N_("Sleeping on your side gets more comfortable as your bump grows; a pillow between the knees helps."),
        N_("You may start feeling movements between weeks 16 and 22."),
        N_("Ask about the anatomy scan, usually around weeks 18 to 22."),
    ],
    3: [
        N_("Get to know your baby's movement pattern and call your provider if it changes or slows."),
        N_("Swelling, heartburn and poor sleep are common now. Smaller meals and elevating your feet help."),
        N_("Pack a hospital bag and plan your route by week 36."),
        N_("Severe headache, vision changes or sudden swelling need a call to your provider right away."),
    ],
}


def pregnancy_cards(p: dict, today: date) -> list[dict]:
    w, cards = p["week"], []
    if p["size"]:
        cards.append(
            _card(
                "milestone", "👶", _("Week {n}", n=w), _("Your baby is about the size of a {size}.", size=_(p["size"]))
            )
        )
    due = date.fromisoformat(p["due"])
    cards.append(
        _card(
            "milestone",
            "📅",
            _("{n} days to go", n=p["days_left"]),
            _(
                "Due {date} · trimester {t}. Only about 1 in 20 babies arrive on the due date itself.",
                date=fmt_date(due, year=True),
                t=p["trimester"],
            ),
        )
    )
    tips = TRIMESTER_TIPS[p["trimester"]]
    cards.append(_card("tip", "💡", _("Trimester {t} tip", t=p["trimester"]), _(tips[today.toordinal() % len(tips)])))
    return cards


def feed(eng: Engine, logs: list, today: date, goal: str) -> list[dict]:
    if p := eng.pregnancy():
        return pregnancy_cards(p, today)
    return [
        c
        for c in [*milestones(eng, today, goal), recap(eng, logs, today), *forecasts(eng, logs, today), tip(eng, today)]
        if c
    ]


def log_note(eng: Engine, patterns: list[dict], day: date, tags: dict) -> str | None:
    """Short note after saving a log: pattern match and/or a tip for the logged symptom."""
    logged = sorted(_tags(tags), key=lambda t: t not in SYMPTOM_TIPS)
    if "positive" in (tags or {}).get("pregnancy_test", []) and eng.profile.mode != "pregnancy":
        return _(
            "Positive pregnancy test logged. If this is happy news, congratulations! "
            "Switch to pregnancy mode in Profile → Life stage."
        )
    if not logged or eng.profile.mode == "pregnancy":
        return None
    phase = eng.day_info(day)["phase"]
    phase = "fertile" if phase == "ovulation" else phase
    usual = {p["tag"]: p["phase"] for p in patterns}
    for t in logged:
        label = _(LABELS.get(t, t))
        if usual.get(t) == phase:
            note = _("{label} {when} matches your usual pattern.", label=label, when=_(PHASE_WORDS.get(phase, "")))
            return f"{note} {_(SYMPTOM_TIPS[t])}" if t in SYMPTOM_TIPS else note
    t = logged[0]
    return SYMPTOM_TIPS.get(t) and f"{_(LABELS.get(t, t))}: {_(SYMPTOM_TIPS[t])}"
