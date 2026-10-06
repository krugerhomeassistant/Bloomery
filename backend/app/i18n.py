"""Tiny gettext-style translation: `_("English text with {placeholders}", **values)`.

The active language lives in a ContextVar, set once per request (deps.current_user / quick-log key / share and
Home Assistant feeds) and per user in the notification scheduler, so pure functions just call `_()`.
Catalogs map the exact English source string to its translation (app/locales/<lang>.py); a missing entry falls
back to English. Run `python -m app.i18n` to list strings used in the code that a catalog doesn't cover yet.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from .locales import af

LANGS = {"en": "English", "af": "Afrikaans"}
CATALOGS: dict[str, dict[str, str]] = {"af": af.STRINGS}
LANG: ContextVar[str] = ContextVar("lang", default="en")


def _(text: str, /, **values: Any) -> str:
    lang = LANG.get()
    s = CATALOGS.get(lang, {}).get(text, text) if lang != "en" else text
    return s.format(**values) if values else s


MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "af": ["Jan", "Feb", "Mrt", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Des"],
}
WEEKDAYS = {"en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "af": ["Ma", "Di", "Wo", "Do", "Vr", "Sa", "So"]}


def fmt_date(d: Any, year: bool = False, weekday: bool = False) -> str:
    """'29 Jan', 'Thu 29 Jan', '7 Apr 2027' in the active language."""
    lang = LANG.get() if LANG.get() in MONTHS else "en"
    s = f"{d.day} {MONTHS[lang][d.month - 1]}" + (f" {d.year}" if year else "")
    return f"{WEEKDAYS[lang][d.weekday()]} {s}" if weekday else s


def N_(text: str) -> str:
    return text


def plural(n: int, one: str, many: str, /, **values: Any) -> str:
    return _(one if n == 1 else many, n=n, **values)


def user_lang(db: Any, uid: int) -> str:
    from .models import Setting

    row = db.get(Setting, f"lang:{uid}")
    return json.loads(row.value) if row else "en"


@contextmanager
def language(lang: str):
    token = LANG.set(lang if lang in LANGS else "en")
    try:
        yield
    finally:
        LANG.reset(token)


if __name__ == "__main__":  # report strings in the code without an Afrikaans entry
    import ast
    import pathlib

    used: set[str] = set()
    for f in pathlib.Path(__file__).parent.rglob("*.py"):
        if "locales" in f.parts:
            continue
        for node in ast.walk(ast.parse(f.read_text())):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") in ("_", "plural", "N_"):
                used |= {a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)}
    from .catalog import CATALOG, FLOW

    used |= {c["title"] for c in CATALOG} | {label for c in CATALOG for _i, label, _e in c["items"]}
    used |= {label for _i, label, _e in FLOW}
    missing = sorted(used - af.STRINGS.keys())
    print(f"{len(used)} strings, {len(missing)} missing in af")
    for m in missing:
        print(" ", repr(m))
