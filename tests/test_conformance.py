"""Verified (Approved) conformance suite.

These tests use DBWarden's shared conformance harness so a reviewer can confirm
the plugin respects the contract. Keep them green in public CI to qualify for
the Verified badge. See the DBWarden docs: plugins/developing/approved-standard.
"""
from __future__ import annotations

from dbwarden import plugin_conformance as conformance

import dbwarden_example

DISTRIBUTION = "dbwarden-example"
PACKAGE = "dbwarden_example"


def test_entry_point_is_declared() -> None:
    conformance.assert_entry_point_declared(DISTRIBUTION)


def test_import_has_no_side_effects() -> None:
    conformance.assert_import_has_no_side_effects(PACKAGE)


def test_setup_registers_hooks() -> None:
    conformance.assert_setup_registers(
        dbwarden_example.setup,
        plugin=DISTRIBUTION,
        value_hooks=("load_model_module",),
    )


def test_hook_signature_compliance() -> None:
    conformance.assert_hook_signatures(dbwarden_example.setup)


def test_no_core_internals_imported() -> None:
    conformance.assert_no_core_internals_imported(PACKAGE)


def test_idempotent_setup() -> None:
    conformance.assert_idempotent_setup(dbwarden_example.setup, plugin=DISTRIBUTION)


# For an object plugin, also add:
#
# def test_object_handler_conformance() -> None:
#     from dbwarden_example.handler import YourHandler
#     conformance.assert_object_handler_conformance(YourHandler(), config=SomeConfig())
#
# def test_ordering_constraint_satisfiable() -> None:
#     from dbwarden_example.handler import YourHandler
#     conformance.assert_ordering_constraint_satisfiable(YourHandler())
