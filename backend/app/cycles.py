"""Cycle engine: pure functions, no DB access. All dates are local calendar dates.

Model
-----
* A *period* is a run of bleeding days (light/medium/heavy); gaps of <= MERGE_GAP days are merged.
* A *cycle* runs from one period start to the day before the next period start.
* Next-cycle length = recency-weighted mean of the last 6 valid cycles (15-90 d), blended with the
  user's configured default while fewer than 3 cycles exist.
* Ovulation = BBT thermal shift ("3 over 6" rule) when detectable, else next_start - luteal_length.
  Luteal length is learned from cycles where BBT confirmed ovulation.
* Fertile window = ovulation-5 .. ovulation+1 (sperm survival + egg lifespan).
"""
from __future__ import annotations

import math
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta

MERGE_GAP = 2
MIN_CYCLE, MAX_CYCLE = 15, 90
TYPICAL_CYCLE = (21, 35)
D = timedelta


@dataclass
class Period:
    start: date
    end: date

    @property
    def length(self) -> int:
        return (self.end - self.start).days + 1


@dataclass
class Segment:
    """One cycle (actual or predicted)."""

    start: date
    length: int
    period_end: date
    ovulation: date
    predicted: bool
    ovulation_confirmed: bool = False

    @property
    def end(self) -> date:
        return self.start + D(days=self.length - 1)

    @property
    def fertile_start(self) -> date:
        return max(self.ovulation - D(days=5), self.period_end + D(days=1))

    @property
    def fertile_end(self) -> date:
        return self.ovulation + D(days=1)


@dataclass
class Profile:
    cycle_length: int = 28
    period_length: int = 5
    luteal_length: int = 14
    goal: str = "track"


@dataclass
class Engine:
    profile: Profile
    today: date
    bleeding: list[date]
    temps: dict[date, float] = field(default_factory=dict)
    periods: list[Period] = field(init=False)
    cycle_lengths: list[int] = field(init=False)
    predicted_cycle: int = field(init=False)
    predicted_period: int = field(init=False)
    luteal: int = field(init=False)
    variability: int = field(init=False)
    segments: list[Segment] = field(init=False)

    def __post_init__(self):
        self.periods = derive_periods(self.bleeding)
        self.cycle_lengths = [
            (b.start - a.start).days
            for a, b in zip(self.periods, self.periods[1:])
            if MIN_CYCLE <= (b.start - a.start).days <= MAX_CYCLE
        ]
        self.predicted_cycle = _blend(self.cycle_lengths, self.profile.cycle_length)
        done = [p.length for p in self.periods if p.end < self.today]
        self.predicted_period = max(1, min(_blend(done, self.profile.period_length), 12))
        self.luteal = self._learn_luteal()
        self.variability = (
            max(1, min(7, math.ceil(statistics.pstdev(self.cycle_lengths[-6:]))))
            if len(self.cycle_lengths) >= 2
            else 2
        )
        self.segments = self._build_segments()

    # ------------------------------------------------------------------ building
    def _ovulation_bbt(self, start: date, end: date) -> date | None:
        return detect_thermal_shift(
            [(d, t) for d, t in sorted(self.temps.items()) if start <= d <= end]
        )

    def _learn_luteal(self) -> int:
        lut = []
        for a, b in zip(self.periods, self.periods[1:]):
            ov = self._ovulation_bbt(a.start, b.start - D(days=1))
            if ov:
                lut.append((b.start - ov).days)
        lut = [x for x in lut if 9 <= x <= 18]
        return round(statistics.mean(lut)) if len(lut) >= 2 else self.profile.luteal_length

    def _ovulation_for(self, start: date, length: int) -> date:
        # never before the end of a typical period
        return max(start + D(days=length - self.luteal), start + D(days=self.predicted_period))

    def _build_segments(self) -> list[Segment]:
        segs: list[Segment] = []
        ps = self.periods
        for i, p in enumerate(ps):
            if i + 1 < len(ps):
                length = (ps[i + 1].start - p.start).days
                bbt = self._ovulation_bbt(p.start, ps[i + 1].start - D(days=1))
                ov = bbt or self._ovulation_for(p.start, length)
                segs.append(Segment(p.start, length, p.end, ov, False, bool(bbt)))
            else:  # current cycle
                length = max(self.predicted_cycle, (self.today - p.start).days + 1)
                bbt = self._ovulation_bbt(p.start, self.today)
                ov = bbt or self._ovulation_for(p.start, self.predicted_cycle)
                period_end = max(p.end, p.start + D(days=self.predicted_period - 1)) if p.end >= self.today else p.end
                segs.append(Segment(p.start, length, period_end, ov, False, bool(bbt)))
        if segs:
            nxt = segs[-1].end + D(days=1)
            for _ in range(12):
                segs.append(
                    Segment(
                        nxt,
                        self.predicted_cycle,
                        nxt + D(days=self.predicted_period - 1),
                        self._ovulation_for(nxt, self.predicted_cycle),
                        True,
                    )
                )
                nxt += D(days=self.predicted_cycle)
        return segs

    # ------------------------------------------------------------------ queries
    @property
    def current(self) -> Segment | None:
        for s in self.segments:
            if s.start <= self.today <= s.end:
                return s
        return None

    @property
    def next_period(self) -> date | None:
        for s in self.segments:
            if s.predicted:
                return s.start
        return None

    def segment_for(self, d: date) -> Segment | None:
        for s in self.segments:
            if s.start <= d <= s.end:
                return s
        return None

    def day_info(self, d: date) -> dict:
        bleeding = set(self.bleeding)
        s = self.segment_for(d)
        info: dict = {"date": d.isoformat(), "cycle_day": None, "phase": None, "kind": None, "chance": None}
        if d in bleeding:
            info["kind"] = "period"
        if not s:
            return info
        info["cycle_day"] = (d - s.start).days + 1
        in_period = d <= s.period_end
        if in_period:
            phase = "menstrual"
            if info["kind"] is None:
                # predicted (future) or unlogged-but-expected days
                if s.predicted or d > self.today:
                    info["kind"] = "predicted_period"
        elif d == s.ovulation:
            phase = "ovulation"
            info["kind"] = "ovulation"
        elif s.fertile_start <= d <= s.fertile_end:
            phase = "fertile"
            info["kind"] = "fertile"
        elif d < s.ovulation:
            phase = "follicular"
        else:
            phase = "luteal"
        info["phase"] = phase
        info["predicted"] = s.predicted or d > self.today
        delta = (s.ovulation - d).days
        info["chance"] = "high" if 0 <= delta <= 2 else "medium" if 3 <= delta <= 5 or delta == -1 else "low"
        return info

    def status(self) -> dict:
        t = self.today
        if not self.periods:
            return {"state": "empty", "label": "Welcome", "headline": "Log your period", "sub": "to get predictions"}
        s = self.current
        info = self.day_info(t)
        base = {"cycle_day": info["cycle_day"], "phase": info["phase"], "chance": info["chance"]}
        last = self.segments[len(self.periods) - 1]
        late = (t - last.start).days - self.predicted_cycle
        if s and not s.predicted and s.start <= t <= s.period_end:
            day = (t - s.start).days + 1
            return {**base, "state": "period", "label": "Period", "headline": f"Day {day}", "sub": _chance_text(info["chance"])}
        if late == 0 and s is last:
            return {**base, "state": "due", "label": "Period expected", "headline": "Today",
                    "sub": "Log your period when it starts"}
        if late > 0 and s is last:
            return {**base, "state": "late", "label": "Period late by", "headline": _days(late),
                    "sub": "Log your period when it starts"}
        if s and s.fertile_start <= t <= s.ovulation:
            n = (s.ovulation - t).days
            return {**base, "state": "fertile", "label": "Ovulation" if n == 0 else "Ovulation in",
                    "headline": "Today" if n == 0 else _days(n), "sub": _chance_text(info["chance"])}
        n = (self.next_period - t).days if self.next_period else 0
        if n <= 0:
            return {**base, "state": "due", "label": "Period expected", "headline": "Today", "sub": "Log your period when it starts"}
        return {**base, "state": "cycle", "label": "Period in", "headline": _days(n), "sub": _chance_text(info["chance"])}

    def overview(self) -> dict:
        cur = self.current
        return {
            "today": self.today.isoformat(),
            "status": self.status(),
            "predicted_cycle_length": self.predicted_cycle,
            "predicted_period_length": self.predicted_period,
            "luteal_length": self.luteal,
            "uncertainty_days": self.variability,
            "next_period": self.next_period.isoformat() if self.next_period else None,
            "current_cycle": _seg_dict(cur) if cur else None,
            "upcoming": [_seg_dict(s) for s in self.segments if s.predicted][:6],
        }

    def calendar(self, start: date, end: date) -> list[dict]:
        out, d = [], start
        while d <= end:
            out.append(self.day_info(d))
            d += D(days=1)
        return out

    def stats(self) -> dict:
        cl = self.cycle_lengths
        pl = [p.length for p in self.periods if p.end < self.today]
        history = []
        for s in [x for x in self.segments if not x.predicted]:
            done = s.end < self.today and s is not self.current
            history.append({
                "start": s.start.isoformat(),
                "length": s.length if done else None,
                "days_so_far": None if done else (self.today - s.start).days + 1,
                "period_length": (s.period_end - s.start).days + 1,
                "ovulation": s.ovulation.isoformat(),
                "ovulation_confirmed": s.ovulation_confirmed,
            })
        regularity = "unknown"
        if len(cl) >= 3:
            spread = max(cl[-6:]) - min(cl[-6:])
            regularity = "regular" if spread <= 7 else "somewhat irregular" if spread <= 9 else "irregular"
        return {
            "cycles_tracked": len(cl),
            "avg_cycle_length": round(statistics.mean(cl), 1) if cl else None,
            "avg_period_length": round(statistics.mean(pl), 1) if pl else None,
            "min_cycle": min(cl) if cl else None,
            "max_cycle": max(cl) if cl else None,
            "regularity": regularity,
            "history": list(reversed(history))[:24],
        }

    def flags(self) -> list[dict]:
        f = []
        cl, pl = self.cycle_lengths[-6:], [p.length for p in self.periods if p.end < self.today][-6:]
        if any(c < TYPICAL_CYCLE[0] for c in cl):
            f.append({"level": "info", "title": "Short cycles",
                      "text": "Some of your recent cycles were shorter than 21 days. Worth mentioning to a healthcare provider if it keeps happening."})
        if any(c > TYPICAL_CYCLE[1] for c in cl):
            f.append({"level": "info", "title": "Long cycles",
                      "text": "Some of your recent cycles were longer than 35 days. Stress, travel and hormones can cause this; talk to a professional if it persists."})
        if len(cl) >= 3 and max(cl) - min(cl) > 9:
            f.append({"level": "info", "title": "Variable cycle length",
                      "text": f"Your cycle length varied by {max(cl) - min(cl)} days recently, so predictions are less certain."})
        if any(p > 7 for p in pl):
            f.append({"level": "warn", "title": "Long periods",
                      "text": "At least one recent period lasted more than 7 days. Consider checking in with a healthcare provider."})
        st = self.status()
        if st.get("state") == "late":
            late = (self.today - self.segments[len(self.periods) - 1].start).days - self.predicted_cycle
            if late >= 7:
                f.append({"level": "warn", "title": "Period is late",
                          "text": "Your period is a week or more late. If pregnancy is possible, a test can help; otherwise stress and lifestyle changes are common causes."})
        return f


# ---------------------------------------------------------------------- helpers
def derive_periods(bleeding: list[date]) -> list[Period]:
    out: list[Period] = []
    for d in sorted(set(bleeding)):
        if out and (d - out[-1].end).days <= MERGE_GAP + 1:
            out[-1].end = d
        else:
            out.append(Period(d, d))
    return out


def detect_thermal_shift(temps: list[tuple[date, float]]) -> date | None:
    """'3 over 6': three consecutive temps above the max of the previous six, one >= +0.2°C.
    Returns the estimated ovulation day (day before the first high temp)."""
    for i in range(6, len(temps) - 2):
        cover = max(t for _, t in temps[i - 6 : i])
        trio = [t for _, t in temps[i : i + 3]]
        if all(t > cover for t in trio) and max(trio) >= cover + 0.2:
            return temps[i][0] - D(days=1)
    return None


def _blend(values: list[int], prior: int) -> int:
    vals = values[-6:]
    if not vals:
        return prior
    w = list(range(1, len(vals) + 1))
    num, den = sum(a * b for a, b in zip(vals, w)), sum(w)
    if len(vals) < 3:
        num, den = num + prior * 2, den + 2
    return round(num / den)


def _days(n: int) -> str:
    return f"{n} day" if n == 1 else f"{n} days"


def _chance_text(c: str | None) -> str:
    return {"high": "High chance of getting pregnant", "medium": "Medium chance of getting pregnant"}.get(
        c or "", "Low chance of getting pregnant")


def _seg_dict(s: Segment) -> dict:
    d = asdict(s)
    d.update(end=s.end, fertile_start=s.fertile_start, fertile_end=s.fertile_end)
    return {k: (v.isoformat() if isinstance(v, date) else v) for k, v in d.items()}


def symptom_patterns(engine: Engine, logs: list[tuple[date, dict]], catalog_labels: dict[str, str]) -> dict:
    """Which tags cluster in which phase; overall top tags."""
    by_tag: dict[str, Counter] = defaultdict(Counter)
    total: Counter = Counter()
    for d, tags in logs:
        phase = engine.day_info(d)["phase"]
        for cat, vals in (tags or {}).items():
            for v in vals if isinstance(vals, list) else []:
                key = f"{cat}:{v}"
                total[key] += 1
                if phase:
                    by_tag[key]["fertile" if phase == "ovulation" else phase] += 1
    patterns = []
    for key, c in by_tag.items():
        n = sum(c.values())
        phase, k = c.most_common(1)[0]
        if n >= 3 and k / n >= 0.6:
            patterns.append({"tag": key, "label": catalog_labels.get(key, key.split(":")[1]),
                             "phase": phase, "count": k, "share": round(k / n, 2)})
    patterns.sort(key=lambda p: (-p["count"], p["label"]))
    top = [{"tag": k, "label": catalog_labels.get(k, k.split(":")[1]), "count": n} for k, n in total.most_common(8)]
    return {"patterns": patterns[:8], "top": top}
