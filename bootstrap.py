#!/usr/bin/env python3
"""Rename this template to a real DBWarden plugin.

Usage:
    python bootstrap.py dbwarden-<name>

Applies the standard naming rule:
    slug        = <dist>.removeprefix("dbwarden-").replace("-", "_")
    import pkg  = "dbwarden_" + slug
    entry key   = slug

It rewrites pyproject.toml, the workflows, the package, the tests, and the
README, then removes itself.
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

    # pyproject.toml: rewrite the entry point (key and target together) before
    # the blanket name substitution, so the key does not get renamed twice.
    pyproject = ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    text = text.replace(f'{OLD_KEY} = "{OLD_PKG}:setup"', f'{slug} = "{pkg}:setup"')
    text = text.replace(OLD_DIST, dist).replace(OLD_PKG, pkg)
    pyproject.write_text(text, encoding="utf-8")

    # Everything else: distribution and package names only, so prose that
    # happens to use the word "example" is left alone.
    targets = [
        ROOT / "README.md",
        *(ROOT / "tests").glob("*.py"),
        *(ROOT / "src" / OLD_PKG).rglob("*.py"),
        *(ROOT / ".github" / "workflows").glob("*.yml"),
    ]
    for path in targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        text = text.replace(OLD_DIST, dist).replace(OLD_PKG, pkg)
        path.write_text(text, encoding="utf-8")

    # Rename the package directory last: the rglob above still needed the old name.
    src = ROOT / "src" / OLD_PKG
    if src.exists():
        src.rename(ROOT / "src" / pkg)

    print(f"Renamed to {dist} (package {pkg}, entry key {slug}).")
    print("Next: set the author and URLs in pyproject.toml, then run:")
    print("  uv sync --dev && uv run pytest -q")
    Path(__file__).unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
