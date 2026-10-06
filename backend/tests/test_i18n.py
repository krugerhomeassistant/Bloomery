"""Translation guards: nothing may rebind `_`, and the Afrikaans catalog must cover every marked string."""

import ast
import pathlib
import string

from app.i18n import N_, _, fmt_date, language
from app.locales import af

APP = pathlib.Path(__file__).resolve().parents[1] / "app"


def _modules():
    for f in APP.rglob("*.py"):
        if "locales" not in f.parts:
            yield f, ast.parse(f.read_text())


def test_underscore_never_rebound():
    """`for _ in`, `_, x = ...` etc. silently replace the translation function in that scope."""
    bad = []
    for f, tree in _modules():
        uses_gettext = any(
            isinstance(n, ast.ImportFrom) and any(a.name == "_" for a in n.names) for n in ast.walk(tree)
        )
        if not uses_gettext:
            continue
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Assign | ast.For | ast.comprehension):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for tgt in targets:
                for n in ast.walk(tgt):
                    if isinstance(n, ast.Name) and n.id == "_" and not isinstance(node, ast.comprehension):
                        bad.append(f"{f.name}:{n.lineno}")
    assert not bad, f"`_` rebound at {bad}"


def test_afrikaans_catalog_complete_and_placeholders_match():
    from app.catalog import CATALOG, FLOW

    used: set[str] = set()
    for _f, tree in _modules():
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") in ("_", "plural", "N_"):
                used |= {a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)}
    used |= {c["title"] for c in CATALOG} | {lab for c in CATALOG for _i, lab, _e in c["items"]}
    used |= {lab for _i, lab, _e in FLOW}
    missing = sorted(used - af.STRINGS.keys())
    assert not missing, f"{len(missing)} strings missing in af: {missing[:15]}"
    fields = lambda s: {f for _t, f, _s, _c in string.Formatter().parse(s) if f}
    wrong = [k for k, v in af.STRINGS.items() if fields(k) != fields(v)]
    assert not wrong, f"placeholders differ: {wrong[:10]}"


def test_language_switch():
    from datetime import date

    assert _("Period") == "Period" and N_("x") == "x"
    with language("af"):
        assert _("Period") == af.STRINGS["Period"]
        assert fmt_date(date(2026, 3, 5), weekday=True) == "Do 5 Mrt"
    assert fmt_date(date(2026, 3, 5), year=True) == "5 Mar 2026"


def test_catalog_and_quick_log_names_in_afrikaans():
    from fastapi.testclient import TestClient

    from app.main import app
    from app.routers.quick import resolve

    cats = TestClient(app).get("/api/catalog?lang=af").json()["categories"]
    assert cats[0]["title"] == "Simptome" and any(i["label"] == "Krampe" for i in cats[0]["items"])
    assert resolve("krampe") == resolve("Cramps") == ("symptoms", "cramps")
