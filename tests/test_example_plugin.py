from __future__ import annotations

from dbwarden.plugin import HookRegistry
from dbwarden_example import setup


def setup_function() -> None:
    HookRegistry.clear()


def test_setup_registers_hooks() -> None:
    class Registrar:
        def register(self, hook_name, fn) -> None:
            HookRegistry.register(hook_name, fn, plugin="dbwarden-example")

    setup(Registrar())

    assert HookRegistry.is_registered("load_model_module") is True


def test_import_has_no_side_effects() -> None:
    import dbwarden_example  # noqa: F401

    assert HookRegistry.hooks() == {}
