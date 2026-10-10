from __future__ import annotations

import pytest
from dbwarden.plugin import HookRegistry, ObjectPluginRegistry, PluginRegistrar

import dbwarden_example

PLUGIN_NAME = "dbwarden-example"


@pytest.fixture(autouse=True)
def register_plugin():
    """Register this plugin the way core does at CLI startup.

    Core only sees your hooks and handlers after `setup()` has run, so any test
    that exercises a code path through core needs this. Both registries are
    process global: clearing them before each test keeps ordering irrelevant and
    stops a second registration from tripping a conflict error.
    """
    HookRegistry.clear()
    ObjectPluginRegistry.clear()
    dbwarden_example.setup(PluginRegistrar(PLUGIN_NAME))
    yield
    HookRegistry.clear()
    ObjectPluginRegistry.clear()
