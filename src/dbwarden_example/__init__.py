from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


def load_model_module(path: Path, base_dir: Path) -> Any:
    # Example hook: load a Python module from a file path. This is self-contained
    # so the template runs anywhere. A real hook typically imports what it needs
    # from DBWarden (or an optional dependency) lazily, inside the function body,
    # so importing this package has no side effects and pulls in nothing heavy.
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def setup(registrar) -> None:
    # Replace load_model_module with the hooks your plugin actually provides.
    # Value hooks are listed in the hook catalog:
    #   docs/plugins/reference/hook-catalog.md
    # For an object plugin, add a handler.py and call
    #   registrar.register_object_handler(YourHandler())
    # instead. See docs/plugins/developing/object-plugins.md.
    registrar.register("load_model_module", load_model_module)


__all__ = ["load_model_module", "setup"]
