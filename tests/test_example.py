"""Behavior tests for what this plugin actually does.

The conformance suite proves the plugin is a well-behaved citizen. It says
nothing about whether your hook is correct, which is what this file is for.
Replace these with tests for your own behavior.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from dbwarden.plugin import HookRegistry

import dbwarden_example


def test_hook_is_reachable_through_core(tmp_path: Path) -> None:
    """The conftest fixture registered setup(), so core can resolve the hook."""
    module_file = tmp_path / "models.py"
    module_file.write_text("VALUE = 42\n")

    module = HookRegistry.execute_single("load_model_module", module_file, tmp_path)

    assert module.VALUE == 42


def test_load_model_module_returns_the_loaded_module(tmp_path: Path) -> None:
    module_file = tmp_path / "widgets.py"
    module_file.write_text("NAME = 'widgets'\n")

    module = dbwarden_example.load_model_module(module_file, tmp_path)

    assert module.NAME == "widgets"


def test_missing_file_raises_import_error(tmp_path: Path) -> None:
    with pytest.raises((ImportError, FileNotFoundError)):
        dbwarden_example.load_model_module(tmp_path / "nope.py", tmp_path)
