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


# Object plugin: handler classes live in handler.py (or a handlers/ package)
# and are registered here. The HANDLER_CLASSES tuple is a convention worth
# keeping: the conformance suite parametrizes over it, so every handler you
# add is covered automatically.
#
# For a value-only plugin, remove the HANDLER_CLASSES import and the
# object_types tuple below, and keep only the value hook registrations.
from dbwarden_example.handler import WidgetHandler

HANDLER_CLASSES = (WidgetHandler,)
OBJECT_TYPES = tuple(h.object_type for h in HANDLER_CLASSES)


def setup(registrar) -> None:
    """Register everything this plugin provides.

    Core calls this once, after it has classified the distribution and (for
    community plugins) after you have consented. Nothing here runs at import
    time.

    Replace the hooks and handlers below with what your plugin actually
    provides. The full hook list is in the hook catalog:
    https://dbwarden.emiliano-go.com/plugins/reference/hook-catalog/
    """
    # Value hooks
    registrar.register("load_model_module", load_model_module)

    # Object handlers
    for handler_class in HANDLER_CLASSES:
        registrar.register_object_handler(handler_class())


__all__ = ["HANDLER_CLASSES", "OBJECT_TYPES", "load_model_module", "setup"]
