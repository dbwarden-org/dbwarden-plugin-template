from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

__version__ = "0.1.0"

# The DBWarden plugin contract this package targets. Core refuses to load a
# plugin declaring a version it does not provide, so a mismatched pairing fails
# at load with one clear message instead of somewhere inside a migration.
DBWARDEN_PLUGIN_API = 1


def load_model_module(path: Path, base_dir: Path) -> Any:
    """Example value hook: load a Python module from a file path.

    Core calls `load_model_module` when it needs to turn a model file into a
    module. This implementation is self-contained so the template runs anywhere.

    A real hook usually imports what it needs from DBWarden inside the function
    body rather than at module scope. You may import anything from `dbwarden`,
    but deferring it keeps `import dbwarden_example` cheap and side-effect free,
    which is what the conformance suite checks.
    """
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def setup(registrar) -> None:
    """Register everything this plugin provides.

    Core calls this once, after it has classified the distribution and (for
    community plugins) after you have consented. Nothing here runs at import
    time.

    Replace `load_model_module` with the hooks you actually provide. The full
    list is in the hook catalog:
    https://dbwarden.emiliano-go.com/plugins/reference/hook-catalog/
    """
    registrar.register("load_model_module", load_model_module)


# An object plugin looks like this instead. Keep handler classes in a
# `handler.py` (or a `handlers/` package) and import them here, so `setup()`
# stays a single readable list of what the plugin contributes:
#
#     from dbwarden_example.handler import ExampleHandler
#
#     HANDLER_CLASSES = (ExampleHandler,)
#
#     def setup(registrar) -> None:
#         for handler_class in HANDLER_CLASSES:
#             registrar.register_object_handler(handler_class())
#
# See https://dbwarden.emiliano-go.com/plugins/developing/object-plugins/

__all__ = ["load_model_module", "setup"]
