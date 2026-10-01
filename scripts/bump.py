#!/usr/bin/env python3
"""Bump the version everywhere and cut the changelog section.

    python scripts/bump.py 1.3.0
    git commit -am "Release v1.3.0" && git tag v1.3.0 && git push --follow-tags

Pushing the tag makes CI test everything, publish ghcr.io/krugerhomeassistant/bloomery:1.3.0
and create the GitHub release (notes from CHANGELOG.md + bloomery.zip for HACS).
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(version: str) -> None:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        sys.exit("usage: bump.py X.Y.Z")
    (ROOT / "backend/app/__init__.py").write_text(f'VERSION = "{version}"\n')

    manifest = ROOT / "custom_components/bloomery/manifest.json"
    m = json.loads(manifest.read_text())
    m["version"] = version
    manifest.write_text(json.dumps(m, indent=2) + "\n")

    for name in ("package.json", "package-lock.json"):
        p = ROOT / "frontend" / name
        d = json.loads(p.read_text())
        d["version"] = version
        if "packages" in d:
            d["packages"][""]["version"] = version
        p.write_text(json.dumps(d, indent=2) + "\n")

    cl = ROOT / "CHANGELOG.md"
    text = cl.read_text()
    if f"## [{version}]" not in text:
        prev = re.search(r"## \[(\d+\.\d+\.\d+)\]", text)
        text = text.replace("## [Unreleased]\n", f"## [Unreleased]\n\n## [{version}] - {date.today()}\n", 1)
        repo = "https://github.com/krugerhomeassistant/Bloomery"
        text = re.sub(
            r"\[Unreleased\]: .*\n",
            f"[Unreleased]: {repo}/compare/v{version}...HEAD\n"
            f"[{version}]: {repo}/compare/v{prev.group(1) if prev else version}...v{version}\n",
            text,
        )
        cl.write_text(text)
    print(f"Bumped to {version}. Review CHANGELOG.md, then commit and tag v{version}.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
