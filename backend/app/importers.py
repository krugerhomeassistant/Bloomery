"""Import history from other apps. Flo/Clue/CSV: periods only. Apple Health: periods + symptoms + BBT + tests.

Supported (auto-detected):
* Flo "Download my data" JSON: operationalData.cycles[] with period_start_date / period_end_date
* Clue backup (.cluedata JSON): {"data": [{"day": "YYYY-MM-DD", "period": "light|medium|heavy|spotting", ...}]}
* Apple Health: the browser pre-extracts relevant <Record>s from export.xml (can be GBs) and sends
  {"format": "apple_health", "records": [[type, "YYYY-MM-DD", value, unit], ...]}
* CSV with a date column + a flow column (period/flow/bleeding/menstruation; words or drip's 0-3),
  or CSV with start/end columns (one row per period)
"""
from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime, timedelta

FLOWS = ("spotting", "light", "medium", "heavy")
WORDS = {"spotting": "spotting", "light": "light", "medium": "medium", "normal": "medium", "heavy": "heavy",
         "very heavy": "heavy", "0": "spotting", "1": "light", "2": "medium", "3": "heavy",
         "yes": "medium", "true": "medium", "x": "medium"}
FLOW_COLS = ("period", "flow", "bleeding", "bleeding.value", "menstruation", "menstrual flow")
DATE_COLS = ("date", "day")
START_COLS, END_COLS = ("start", "period start", "start date", "period_start_date"), ("end", "period end", "end date", "period_end_date")


class ImportFormatError(ValueError):
    pass


# Apple HealthKit type (without HKCategoryTypeIdentifier prefix) -> Bloomery tag
APPLE_SYMPTOMS = {
    "AbdominalCramps": "symptoms:cramps", "BreastPain": "symptoms:tender_breasts", "Headache": "symptoms:headache",
    "Acne": "symptoms:acne", "LowerBackPain": "symptoms:backache", "Fatigue": "symptoms:fatigue",
    "SleepChanges": "symptoms:insomnia", "HotFlashes": "symptoms:hot_flashes", "Dizziness": "symptoms:dizziness",
    "PelvicPain": "symptoms:abdominal_pain", "AppetiteChanges": "symptoms:cravings", "Bloating": "digestion:bloating",
    "Nausea": "digestion:nausea", "Constipation": "digestion:constipation", "Diarrhea": "digestion:diarrhea",
    "MoodChanges": "mood:mood_swings",
}
APPLE_MUCUS = {"Dry": "none", "Sticky": "sticky", "Creamy": "creamy", "Watery": "watery", "EggWhite": "egg_white"}


def _apple(records: list) -> dict[date, dict]:
    days: dict[date, dict] = {}
    for rec in records:
        typ, day, value = rec[0], _d(rec[1]), str(rec[2] or "")
        unit = rec[3] if len(rec) > 3 else ""
        e = days.setdefault(day, {})
        tag = None
        if typ == "MenstrualFlow":  # value ends Light/Medium/Heavy/Unspecified/None (…MenstrualFlow… or …VaginalBleeding…)
            f = next((w.lower() for w in ("Light", "Medium", "Heavy") if value.endswith(w)), "medium" if value.endswith("Unspecified") else None)
            if f:
                e["flow"] = f
        elif typ == "IntermenstrualBleeding":
            e.setdefault("flow", "spotting")
        elif typ == "BasalBodyTemperature":
            t = float(value)
            e["temperature"] = round((t - 32) * 5 / 9, 2) if unit.lower() == "degf" else t
        elif typ == "CervicalMucusQuality":
            m = next((v for k, v in APPLE_MUCUS.items() if value.endswith(k)), None)
            tag = m and f"discharge:{m}"
        elif typ == "OvulationTestResult":
            tag = "ovulation_test:negative" if value.endswith("Negative") else None if value.endswith("Indeterminate") else "ovulation_test:positive"
        elif typ == "PregnancyTestResult":
            tag = {"Positive": "pregnancy_test:positive", "Negative": "pregnancy_test:negative"}.get(next((w for w in ("Positive", "Negative") if value.endswith(w)), ""))
        elif typ in APPLE_SYMPTOMS and not value.endswith("NotPresent"):
            tag = APPLE_SYMPTOMS[typ]
        if tag:
            cat, v = tag.split(":")
            e.setdefault("tags", {}).setdefault(cat, set()).add(v)
    return {d: e for d, e in days.items() if e}


def _d(v) -> date:
    s = str(v).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ImportFormatError(f"Unrecognised date: {v!r}")


def _span(start, end) -> list[date]:
    a, b = _d(start), _d(end or start)
    if b < a or (b - a).days > 15:  # ponytail: >15-day "period" is almost surely bad data; clip to start day
        b = a
    return [a + timedelta(days=i) for i in range((b - a).days + 1)]


def _flow(v) -> str | None:
    if isinstance(v, dict):  # some exports nest {"value": "heavy"}
        v = v.get("value")
    if v is None or v == "":
        return None
    return WORDS.get(str(v).strip().lower())


def parse(content: str) -> tuple[str, dict[date, dict]]:
    """Returns (source name, {day: {"flow"?, "tags"?: {cat: set}, "temperature"?}})."""
    src, days = _parse(content)
    return src, {d: (v if isinstance(v, dict) else {"flow": v}) for d, v in days.items()}


def _parse(content: str):
    content = content.lstrip("﻿")
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = None

    if isinstance(data, dict) and data.get("format") == "apple_health":
        return "Apple Health", _apple(data.get("records") or [])

    if isinstance(data, dict) and isinstance(data.get("operationalData"), dict):
        days: dict[date, str] = {}
        for c in data["operationalData"].get("cycles") or []:
            if c.get("period_start_date"):
                for d in _span(c["period_start_date"], c.get("period_end_date")):
                    days[d] = "medium"
        return "Flo", days

    if isinstance(data, dict) and isinstance(data.get("data"), list):
        days = {}
        for e in data["data"]:
            f = _flow(e.get("period"))
            if f and (e.get("day") or e.get("date")):
                days[_d(e.get("day") or e.get("date"))] = f
        return "Clue", days

    if data is not None:
        raise ImportFormatError("This JSON file isn't a Bloomery, Flo or Clue export.")

    rows = list(csv.DictReader(io.StringIO(content)))
    if not rows:
        raise ImportFormatError("The file is empty or not a CSV/JSON export.")
    cols = {k.strip().lower(): k for k in rows[0] if k}
    pick = lambda names: next((cols[n] for n in names if n in cols), None)  # noqa: E731
    dcol, fcol, scol, ecol = pick(DATE_COLS), pick(FLOW_COLS), pick(START_COLS), pick(END_COLS)
    days = {}
    if scol:
        for r in rows:
            if r.get(scol):
                for d in _span(r[scol], r.get(ecol) if ecol else None):
                    days[d] = "medium"
        return "CSV", days
    if dcol and fcol:
        for r in rows:
            f = _flow(r.get(fcol))
            if f and r.get(dcol):
                days[_d(r[dcol])] = f
        return "CSV", days
    raise ImportFormatError("CSV needs a date column plus a period/flow column, or start/end columns.")


if __name__ == "__main__":  # self-check
    flo = json.dumps({"operationalData": {"cycles": [{"period_start_date": "2024-01-01T00:00:00", "period_end_date": "2024-01-04T00:00:00"}]}})
    assert parse(flo) == ("Flo", {date(2024, 1, d): {"flow": "medium"} for d in range(1, 5)})
    apple = json.dumps({"format": "apple_health", "records": [
        ["MenstrualFlow", "2024-04-01", "HKCategoryValueVaginalBleedingHeavy", ""],
        ["AbdominalCramps", "2024-04-01", "HKCategoryValueSeverityModerate", ""],
        ["Headache", "2024-04-01", "HKCategoryValueSeverityNotPresent", ""],
        ["BasalBodyTemperature", "2024-04-02", "97.7", "degF"],
        ["CervicalMucusQuality", "2024-04-12", "HKCategoryValueCervicalMucusQualityEggWhite", ""]]})
    src, d = parse(apple)
    assert src == "Apple Health" and d[date(2024, 4, 1)] == {"flow": "heavy", "tags": {"symptoms": {"cramps"}}}
    assert d[date(2024, 4, 2)] == {"temperature": 36.5} and d[date(2024, 4, 12)]["tags"] == {"discharge": {"egg_white"}}
    clue = json.dumps({"data": [{"day": "2024-02-01", "period": "heavy"}, {"day": "2024-02-02", "pain": ["cramps"]}]})
    assert parse(clue) == ("Clue", {date(2024, 2, 1): {"flow": "heavy"}})
    assert parse("date,bleeding.value\n2024-03-01,3\n2024-03-02,\n")[1] == {date(2024, 3, 1): {"flow": "heavy"}}
    assert len(parse("Start,End\n05/04/2024,08/04/2024\n")[1]) == 4
    print("ok")
