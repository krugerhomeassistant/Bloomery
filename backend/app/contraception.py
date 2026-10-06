"""Birth control: where you are in your pack / ring / patch / injection schedule, and what to do today.

Config per user in Setting "bc:<uid>" as JSON: {method, start, pill_type, expires}. Pure functions, no AI.
Schedules follow standard product labelling; the app always defers to the user's clinician/leaflet.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

HORMONAL = {"pill", "ring", "patch", "injection", "iud_hormonal", "implant"}
METHODS = ("none", "pill", "ring", "patch", "injection", "iud_hormonal", "iud_copper", "implant", "condom", "other")
PILL_TYPES = {"21_7": (21, 7), "24_4": (24, 4), "28": (28, 0), "pop": (28, 0)}  # active, break days
INJECTION_WEEKS = 13


def _d(d: date, year: bool = False) -> str:
    return f"{d:%a} {d.day} {d:%b}" + (f" {d.year}" if year else "")


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
            return card("💊", "Take your pill", "Progestin-only pill: same time every day, no break.", True)
        if day <= active:
            left = active - day
            text = f"Active pill {day} of {active}." + (f" Break starts in {left} days." if gap and left <= 3 else "")
            if not gap and day == active:
                text += " Start a new pack tomorrow."
            return card("💊", f"Pill day {day}", text, True)
        restart = today + timedelta(days=active + gap - day + 1)
        return card(
            "💊", f"Break day {day - active} of {gap}", f"Start your next pack on {_d(restart)}.", day == active + gap
        )

    if m in ("ring", "patch") and start:
        day = (today - start).days % 28 + 1
        if m == "ring":
            if day <= 21:
                if day == 21:
                    return card("⭕", "Remove your ring tomorrow", "It has been in for 3 weeks tomorrow.", True)
                return card("⭕", f"Ring week {(day - 1) // 7 + 1}", f"Remove it in {22 - day} days.", False)
            if day == 22:
                return card("⭕", "Remove your ring today", "Ring-free week until a new ring in 7 days.", True)
            if day == 28:
                return card("⭕", "Insert a new ring tomorrow", "Your ring-free week ends tomorrow.", True)
            return card("⭕", f"Ring-free day {day - 21}", f"Insert a new ring in {29 - day} days.", False)
        if day in (8, 15):
            return card("🩹", "Change your patch today", f"Patch {(day - 1) // 7 + 1} of 3 this cycle.", True)
        if day == 22:
            return card("🩹", "Take your patch off today", "Patch-free week; new patch in 7 days.", True)
        if day == 28:
            return card("🩹", "New patch tomorrow", "Your patch-free week ends tomorrow.", True)
        if day > 22:
            return card("🩹", f"Patch-free day {day - 21}", f"New patch in {29 - day} days.", False)
        nxt = 8 if day < 8 else 15 if day < 15 else 22
        return card("🩹", f"Patch {(day - 1) // 7 + 1} of 3", f"Next change in {nxt - day} days.", False)

    if m == "injection" and start:
        due = start + timedelta(weeks=INJECTION_WEEKS)
        left = (due - today).days
        if left < 0:
            return card(
                "💉",
                "Injection overdue",
                f"Due {-left} days ago. Contact your clinic; you may need backup protection.",
                True,
            )
        if left == 0:
            return card("💉", "Injection due today", "Book or confirm your appointment.", True)
        return card("💉", f"Next injection in {left} days", f"Due {_d(due)}.", left in (14, 7, 1))

    if m in ("iud_hormonal", "iud_copper", "implant"):
        name = "implant" if m == "implant" else "IUD"
        if expires and (left := (expires - today).days) <= 60:
            when = "now" if left <= 0 else f"by {_d(expires, True)}"
            return card(
                "🗓️", f"{name} replacement due", f"Book a replacement {when}.", left in (60, 30, 7, 0) or left < 0
            )
        if m != "implant" and start and today.day == start.day:
            return card(
                "🧵", "Monthly IUD string check", "After your period, gently check you can feel the strings.", True
            )
        text = f"Replace by {_d(expires, True)}." if expires else "No replacement date set."
        return card("🛡️" if m != "implant" else "💪", f"{name} in place", text, False)
    return None


def hormonal(cfg: dict[str, Any] | None) -> bool:
    return bool(cfg) and cfg.get("method") in HORMONAL
