#!/usr/bin/env python3
"""Rename this template to a real DBWarden plugin.

Usage:
    python bootstrap.py dbwarden-<name>

Applies the standard naming rule:
    slug        = <dist>.removeprefix("dbwarden-").replace("-", "_")
    import pkg  = "dbwarden_" + slug
    entry key   = slug

It rewrites pyproject.toml, the package, and the test, then removes itself.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent
OLD_DIST = "dbwarden-example"
OLD_PKG = "dbwarden_example"
OLD_KEY = "example"


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].startswith("dbwarden-"):
        print(__doc__)
        return 1

    dist = sys.argv[1]
    slug = dist.removeprefix("dbwarden-").replace("-", "_")
    pkg = f"dbwarden_{slug}"

    # pyproject.toml: rewrite the entry point (key + target) atomically, then names.
    pyproject = ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    text = text.replace(f'{OLD_KEY} = "{OLD_PKG}:setup"', f'{slug} = "{pkg}:setup"')
    text = text.replace(OLD_DIST, dist).replace(OLD_PKG, pkg)
    pyproject.write_text(text, encoding="utf-8")

    # Other files: distribution and package names only (leave prose like "example" alone).
    for path in [ROOT / "README.md", *(ROOT / "tests").glob("*.py")]:
        text = path.read_text(encoding="utf-8")
        text = text.replace(OLD_DIST, dist).replace(OLD_PKG, pkg)
        path.write_text(text, encoding="utf-8")

    # Rename the package directory.
    src = ROOT / "src" / OLD_PKG
    if src.exists():
        src.rename(ROOT / "src" / pkg)

    print(f"Renamed to {dist} (package {pkg}, entry key {slug}).")
    Path(__file__).unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
