"""Import period history from other apps. Periods only (the part predictions need); symptoms differ too much per app.

Supported (auto-detected):
* Flo "Download my data" JSON: operationalData.cycles[] with period_start_date / period_end_date
* Clue backup (.cluedata JSON): {"data": [{"day": "YYYY-MM-DD", "period": "light|medium|heavy|spotting", ...}]}
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


def parse(content: str) -> tuple[str, dict[date, str]]:
    """Returns (source name, {day: flow})."""
    content = content.lstrip("﻿")
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = None

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
    assert parse(flo) == ("Flo", {date(2024, 1, d): "medium" for d in range(1, 5)})
    clue = json.dumps({"data": [{"day": "2024-02-01", "period": "heavy"}, {"day": "2024-02-02", "pain": ["cramps"]}]})
    assert parse(clue) == ("Clue", {date(2024, 2, 1): "heavy"})
    assert parse("date,bleeding.value\n2024-03-01,3\n2024-03-02,\n")[1] == {date(2024, 3, 1): "heavy"}
    assert len(parse("Start,End\n05/04/2024,08/04/2024\n")[1]) == 4
    print("ok")
