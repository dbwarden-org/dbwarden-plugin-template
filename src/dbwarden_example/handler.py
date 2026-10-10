"""Example object handler.

Replace this with a handler for your own object type. The handler participates
in the extract -> diff -> emit pipeline that DBWarden uses to generate migration
SQL for every registered object type.

See https://dbwarden.emiliano-go.com/plugins/developing/object-plugins/
"""

from __future__ import annotations

from typing import Any

from dbwarden.engine.core.ordering import Anchor, OrderingConstraint
from dbwarden.engine.core.protocol import Op, RunPhase
from dbwarden.engine.core.statement_order import MigrationStatement, StatementOrder


class WidgetHandler:
    """Example object handler for a ``widget`` object type.

    Attributes:
        object_type: Registration key. Must be unique across all handlers.
        run_phase: PREAMBLE runs before table extraction, DIFF runs after.
        statement_order: Where emitted statements appear in the migration.
        ordering: Anchors that control when this handler runs.
    """

    object_type = "widget"
    run_phase = RunPhase.DIFF
    statement_order = StatementOrder.ADD_COLUMN
    ordering = OrderingConstraint(
        after=(Anchor.AFTER_TABLES,),
        before=(Anchor.AFTER_CONSTRAINTS,),
    )

    def extract(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Extract widget specs from the live database snapshot."""
        # TODO: read widget state from snapshot["widgets"] or similar
        return {}

    def model_spec_from_config(self, config: Any) -> dict[str, Any]:
        """Build widget spec from configuration (PREAMBLE handlers only)."""
        return {}

    def model_spec_from_tables(self, model_tables: list[Any]) -> dict[str, Any]:
        """Build widget spec from SQLAlchemy model tables."""
        # TODO: read widget declarations from model_tables
        return {}

    def canonicalize(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Normalize a spec for comparison."""
        return spec

    def diff(
        self,
        snap_spec: dict[str, Any],
        model_spec: dict[str, Any],
    ) -> tuple[list[Op], list[Op]]:
        """Compare snapshot and model specs to produce upgrade and rollback ops."""
        # TODO: implement your diff logic
        return [], []

    def emit(
        self,
        op: Op,
        db_name: str | None = None,
        **kwargs: Any,
    ) -> list[MigrationStatement]:
        """Convert an Op into executable migration statements."""
        # TODO: implement your SQL emission
        return []
