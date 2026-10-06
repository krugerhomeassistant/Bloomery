"""Birth control: where you are in your pack / ring / patch / injection schedule, and what to do today.

Config per user in Setting "bc:<uid>" as JSON: {method, start, pill_type, expires}. Pure functions, no AI.
Schedules follow standard product labelling; the app always defers to the user's clinician/leaflet.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .i18n import _, fmt_date

HORMONAL = {"pill", "ring", "patch", "injection", "iud_hormonal", "implant"}
METHODS = ("none", "pill", "ring", "patch", "injection", "iud_hormonal", "iud_copper", "implant", "condom", "other")
PILL_TYPES = {"21_7": (21, 7), "24_4": (24, 4), "28": (28, 0), "pop": (28, 0)}  # active, break days
INJECTION_WEEKS = 13


def _d(d: date, year: bool = False) -> str:
    return fmt_date(d, year=year, weekday=not year)


def card(emoji: str, title: str, text: str, action: bool) -> dict[str, Any]:
    return {"kind": "contraception", "emoji": emoji, "title": title, "text": text, "action": action}


def status(cfg: dict[str, Any] | None, today: date) -> dict[str, Any] | None:
    """Today's card for the configured method, or None. `action` = something to do today (reminder-worthy)."""
    if not cfg or cfg.get("method") in (None, "none", "condom", "other"):
        return None
    m = cfg["method"]
    start = date.fromisoformat(cfg["start"]) if cfg.get("start") else None
    expires = date.fromisoformat(cfg["expires"]) if cfg.get("expires") else None

    if m == "pill" and start:
        active, gap = PILL_TYPES.get(cfg.get("pill_type") or "21_7", (21, 7))
        day = (today - start).days % (active + gap) + 1
        if cfg.get("pill_type") == "pop":
            return card("💊", _("Take your pill"), _("Progestin-only pill: same time every day, no break."), True)
        if day <= active:
            left = active - day
            text = _("Active pill {day} of {total}.", day=day, total=active) + (
                " " + _("Break starts in {n} days.", n=left) if gap and left <= 3 else ""
            )
            if not gap and day == active:
                text += " " + _("Start a new pack tomorrow.")
            return card("💊", _("Pill day {n}", n=day), text, True)
        restart = today + timedelta(days=active + gap - day + 1)
        return card(
            "💊",
            _("Break day {n} of {total}", n=day - active, total=gap),
            _("Start your next pack on {date}.", date=_d(restart)),
            day == active + gap,
        )

    if m in ("ring", "patch") and start:
        day = (today - start).days % 28 + 1
        if m == "ring":
            if day <= 21:
                if day == 21:
                    return card("⭕", _("Remove your ring tomorrow"), _("It has been in for 3 weeks tomorrow."), True)
                return card(
                    "⭕", _("Ring week {n}", n=(day - 1) // 7 + 1), _("Remove it in {n} days.", n=22 - day), False
                )
            if day == 22:
                return card("⭕", _("Remove your ring today"), _("Ring-free week until a new ring in 7 days."), True)
            if day == 28:
                return card("⭕", _("Insert a new ring tomorrow"), _("Your ring-free week ends tomorrow."), True)
            return card(
                "⭕", _("Ring-free day {n}", n=day - 21), _("Insert a new ring in {n} days.", n=29 - day), False
            )
        if day in (8, 15):
            return card("🩹", _("Change your patch today"), _("Patch {n} of 3 this cycle.", n=(day - 1) // 7 + 1), True)
        if day == 22:
            return card("🩹", _("Take your patch off today"), _("Patch-free week; new patch in 7 days."), True)
        if day == 28:
            return card("🩹", _("New patch tomorrow"), _("Your patch-free week ends tomorrow."), True)
        if day > 22:
            return card("🩹", _("Patch-free day {n}", n=day - 21), _("New patch in {n} days.", n=29 - day), False)
        nxt = 8 if day < 8 else 15 if day < 15 else 22
        return card("🩹", _("Patch {n} of 3", n=(day - 1) // 7 + 1), _("Next change in {n} days.", n=nxt - day), False)

    if m == "injection" and start:
        due = start + timedelta(weeks=INJECTION_WEEKS)
        left = (due - today).days
        if left < 0:
            return card(
                "💉",
                _("Injection overdue"),
                _("Due {n} days ago. Contact your clinic; you may need backup protection.", n=-left),
                True,
            )
        if left == 0:
            return card("💉", _("Injection due today"), _("Book or confirm your appointment."), True)
        return card("💉", _("Next injection in {n} days", n=left), _("Due {date}.", date=_d(due)), left in (14, 7, 1))

    if m in ("iud_hormonal", "iud_copper", "implant"):
        implant = m == "implant"
        if expires and (left := (expires - today).days) <= 60:
            text = (
                _("Book a replacement now.")
                if left <= 0
                else _("Book a replacement by {date}.", date=_d(expires, True))
            )
            title = _("Implant replacement due") if implant else _("IUD replacement due")
            return card("🗓️", title, text, left in (60, 30, 7, 0) or left < 0)
        if not implant and start and today.day == start.day:
            return card(
                "🧵",
                _("Monthly IUD string check"),
                _("After your period, gently check you can feel the strings."),
                True,
            )
        text = _("Replace by {date}.", date=_d(expires, True)) if expires else _("No replacement date set.")
        return card("💪" if implant else "🛡️", _("Implant in place") if implant else _("IUD in place"), text, False)
    return None


def hormonal(cfg: dict[str, Any] | None) -> bool:
    return bool(cfg) and cfg.get("method") in HORMONAL
