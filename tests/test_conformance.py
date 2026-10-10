"""Verified (Approved) conformance suite.

These run DBWarden's shared conformance harness so a reviewer can confirm the
plugin respects the contract. Keep them green in public CI to qualify for the
Verified badge.

Reference: https://dbwarden.emiliano-go.com/plugins/developing/approved-standard/
"""

from __future__ import annotations

import pytest
from dbwarden import plugin_conformance as conformance

import dbwarden_example

DISTRIBUTION = "dbwarden-example"
PACKAGE = "dbwarden_example"

# Hooks this plugin promises to register. Keep in sync with setup().
VALUE_HOOKS = ("load_model_module",)

# Object types this plugin promises to register. Keep in sync with setup().
OBJECT_TYPES = dbwarden_example.OBJECT_TYPES


def test_entry_point_is_declared() -> None:
    conformance.assert_entry_point_declared(DISTRIBUTION)


def test_import_has_no_side_effects() -> None:
    conformance.assert_import_has_no_side_effects(PACKAGE)


def test_setup_registers_hooks() -> None:
    conformance.assert_setup_registers(
        dbwarden_example.setup,
        plugin=DISTRIBUTION,
        value_hooks=VALUE_HOOKS,
        object_types=OBJECT_TYPES,
    )


def test_hook_signature_compliance() -> None:
    conformance.assert_hook_signatures(dbwarden_example.setup)


def test_core_imports_resolve() -> None:
    conformance.assert_core_imports_resolve(PACKAGE)


def test_api_version_is_declared() -> None:
    conformance.assert_api_version_declared(PACKAGE)


def test_idempotent_setup() -> None:
    conformance.assert_idempotent_setup(dbwarden_example.setup, plugin=DISTRIBUTION)


@pytest.mark.parametrize("handler_class", dbwarden_example.HANDLER_CLASSES)
def test_object_handler_conformance(handler_class) -> None:
    conformance.assert_object_handler_conformance(handler_class())


@pytest.mark.parametrize("handler_class", dbwarden_example.HANDLER_CLASSES)
def test_ordering_constraint_satisfiable(handler_class) -> None:
    conformance.assert_ordering_constraint_satisfiable(handler_class())
