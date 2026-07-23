# dbwarden-plugin-template

A GitHub template repository for building [DBWarden](https://github.com/dbwarden/dbwarden) plugins. Generating a repo from this template gives you a working, tested plugin with the standardized layout: a setuptools `src/` package, `setup(registrar)` in `__init__.py`, a `dbwarden.plugins` entry point, the Verified conformance suite, and a CI workflow.

This README explains the whole plugin system as well as how to use the template.

## Contents

- [Quick start](#quick-start)
- [What DBWarden plugins are](#what-dbwarden-plugins-are)
- [Trust model](#trust-model)
- [How plugins are discovered and loaded](#how-plugins-are-discovered-and-loaded)
- [Naming rule and project structure](#naming-rule-and-project-structure)
- [Writing a value plugin](#writing-a-value-plugin)
- [Writing an object plugin](#writing-an-object-plugin)
- [The Verified conformance suite](#the-verified-conformance-suite)
- [Publishing](#publishing)
- [Installing and using a plugin](#installing-and-using-a-plugin)
- [Reference](#reference)

## Quick start

1. Click **Use this template** on GitHub to create your own repository.
2. Rename the placeholders to your plugin name:

   ```bash
   python bootstrap.py dbwarden-yourname
   ```

   `bootstrap.py` applies the naming rule below, renames the package, and removes itself. To rename by hand instead, replace `dbwarden-example`, `dbwarden_example`, and the entry key `example`, then rename `src/dbwarden_example/`.

3. Install and run the tests:

   ```bash
   pip install -e . pytest
   pytest -q
   ```

The template ships as a value plugin. To build an object plugin, see [Writing an object plugin](#writing-an-object-plugin).

## What DBWarden plugins are

A plugin is a normal Python package that extends DBWarden without touching its core. DBWarden keeps a clean core and pushes framework integrations and backend-specific schema support into plugins. There are two kinds.

**Value plugins** supply a value at a named hook point. Core calls the hook where optional behavior is needed. Examples: FastAPI session dependencies, a lifespan, health routes, seed commands, module loaders. A value plugin registers callables by name.

**Object plugins** add a database object type to DBWarden's schema diff pipeline. Examples: PostgreSQL extensions, roles, grants, policies, custom types, ClickHouse RBAC. An object plugin registers a handler that participates in extract, canonicalize, diff, and emit.

A single package may register both.

## Trust model

DBWarden classifies every plugin by its distribution name **before importing any of its code**. This is the classify-before-load guarantee: merely installing a plugin runs none of its logic.

| Tier | Loads automatically? | Basis of trust |
|------|----------------------|----------------|
| Official | Yes | DBWarden-owned package, provenance verified at install (PyPI PEP 740 attestation). |
| Approved (Verified badge) | Yes, when the installed version meets the approved minimum | Passed the conformance suite and a review. |
| Community | No, consent required | Your explicit, version-specific consent. |

A plugin's tier comes from the curated lists in core (`dbwarden/_official.py`, `dbwarden/_approved.py`), not from its name. Every plugin, community or official, is distributed as `dbwarden-<name>`.

Community plugins are installed but not loaded until you consent to the exact installed version:

```bash
dbwarden plugin trust dbwarden-yourname
```

Consent is recorded in `.dbwarden/consent.toml` and is version-specific. Trust gates whether a plugin loads, not what it can do once loaded: a loaded plugin runs with full process privileges. It is not a sandbox.

## How plugins are discovered and loaded

Discovery uses standard Python entry points. Your `pyproject.toml` declares one entry point in the `dbwarden.plugins` group pointing at a `setup` callable:

```toml
[project.entry-points."dbwarden.plugins"]
yourname = "dbwarden_yourname:setup"
```

The lifecycle:

1. DBWarden reads entry-point metadata (name, version) without importing your code.
2. It classifies the distribution into a trust tier.
3. If trust rules allow, it imports the entry point and calls `setup(registrar)`.
4. `setup(registrar)` registers value hooks and/or object handlers.

Two rules make this safe and fast, and the conformance suite enforces them:

- **No import-time side effects.** Registration happens only inside `setup()`. Importing your package registers nothing.
- **Defer heavy imports to call time.** Value hooks import their DBWarden internals (and optional dependencies like FastAPI or drivers) inside the function body. Object plugins import their `handler` module inside `setup()`.

## Naming rule and project structure

All three names derive from the distribution name by one rule:

```
slug        = distribution_name.removeprefix("dbwarden-").replace("-", "_")
import pkg  = "dbwarden_" + slug
entry key   = slug
```

For example `dbwarden-audit` gives package `dbwarden_audit` and key `audit`; `dbwarden-pgsql-rbac` gives package `dbwarden_pgsql_rbac` and key `pgsql_rbac`.

Structure:

```
<distribution>/
├── pyproject.toml            # setuptools, src layout, dbwarden>=0.15.0
├── README.md
├── LICENSE
├── .gitignore
├── .github/workflows/test.yml
├── src/<package>/
│   ├── __init__.py           # hook functions + setup(registrar)
│   └── handler.py            # object plugins only
└── tests/
    └── test_conformance.py   # Verified conformance suite
```

`setup(registrar)` lives at the bottom of `__init__.py`. There is no separate `plugin.py`.

## Writing a value plugin

Define each hook as a top-level function and register it in `setup()`. Import what the hook needs inside its body so importing the package stays side-effect-free:

```python
# src/dbwarden_yourname/__init__.py
def session_factory(database: str | None = None, *, dev: bool = False):
    from dbwarden.extensions.fastapi.engines import _async_session_factory  # deferred

    async def _dependency():
        async with _async_session_factory(database, dev=dev)() as session:
            yield session

    return _dependency


def setup(registrar) -> None:
    registrar.register("session_factory", session_factory)


__all__ = ["session_factory", "setup"]
```

`registrar.register(name, callable)` raises `ValueError` if `name` is not a known hook, so typos fail fast at load time. Each hook has a documented signature that core calls it with; matching it is part of the conformance suite.

Some hooks are single (exactly one plugin may provide them; a second provider raises a conflict when the hook runs) and some are multi (`health_routes`, `migration_routes`; core collects every provider). The full list of hook names, signatures, and single or multi status is in the [hook catalog](https://github.com/dbwarden/dbwarden/blob/main/docs/plugins/reference/hook-catalog.md).

## Writing an object plugin

An object plugin adds a database object type to the schema diff pipeline. Put the handler in `handler.py` and import it lazily in `setup()`:

```python
# src/dbwarden_yourname/handler.py
from dbwarden.engine.core import Anchor, MigrationStatement, Op, OrderingConstraint, RunPhase


class YourHandler:
    object_type = "your_object"
    op_types = ("create_your_object", "drop_your_object")
    run_phase = RunPhase.DIFF
    ordering = OrderingConstraint(after=(Anchor.AFTER_TABLES,))

    def extract(self, snapshot): ...              # live database state
    def model_spec_from_config(self, config): ... # desired state from config
    def model_spec_from_tables(self, model_tables): ...  # desired state from models
    def canonicalize(self, spec): ...             # normalize for comparison
    def diff(self, snap_spec, model_spec): ...    # -> (upgrade_ops, rollback_ops)
    def emit(self, op, db_name=None, **kwargs): ...  # Op -> list[MigrationStatement]
```

```python
# src/dbwarden_yourname/__init__.py
def setup(registrar) -> None:
    from dbwarden_yourname.handler import YourHandler

    registrar.register_object_handler(YourHandler())
```

Ordering uses public anchors, never private statement-order integers. The anchors, in order, are `PREAMBLE`, `BEFORE_TABLES`, `AFTER_TABLES`, `AFTER_CONSTRAINTS`, `AFTER_INDEXES`, `POSTAMBLE`. You can also order a handler relative to another by object type with `after_object` and `before_object`. DBWarden rejects impossible anchor pairs, unknown references, and cycles.

The [`dbwarden-pgsql-extensions`](https://github.com/dbwarden/dbwarden-pgsql-extensions) plugin is a complete worked example, and the [object-plugin docs](https://github.com/dbwarden/dbwarden/blob/main/docs/plugins/developing/object-plugins.md) walk through it step by step.

## The Verified conformance suite

`tests/test_conformance.py` runs DBWarden's shared harness (`dbwarden.plugin_conformance`), which proves your plugin respects the contract. Keeping it green in public CI is what qualifies a community plugin for the **Verified** (Approved tier) badge.

The checks:

1. `test_entry_point_is_declared`: the `dbwarden.plugins` entry point exists and resolves to a callable.
2. `test_import_has_no_side_effects`: importing the package registers nothing.
3. `test_setup_registers_hooks`: `setup()` registers the hooks or handlers it claims.
4. `test_hook_signature_compliance`: each registered hook accepts the arguments core calls it with.
5. `test_no_core_internals_imported`: only the public API is imported (`dbwarden.plugin`, `dbwarden.exceptions`, `dbwarden.engine.core`).
6. `test_object_handler_conformance` (object plugins): extract, canonicalize, diff, and emit return the right types and valid SQL.
7. `test_ordering_constraint_satisfiable` (object plugins): the ordering constraint is not statically impossible.
8. `test_idempotent_setup` (recommended): calling `setup()` twice does not raise or add duplicate registrations.

The template wires these up for a value plugin. For an object plugin, add the two object checks:

```python
def test_object_handler_conformance():
    from dbwarden_yourname.handler import YourHandler
    conformance.assert_object_handler_conformance(YourHandler(), config=SomeConfig())

def test_ordering_constraint_satisfiable():
    from dbwarden_yourname.handler import YourHandler
    conformance.assert_ordering_constraint_satisfiable(YourHandler())
```

Full details are in the [Approved Plugin Standard](https://github.com/dbwarden/dbwarden/blob/main/docs/plugins/developing/approved-standard.md).

## Publishing

The template's `pyproject.toml` already has the right shape:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "dbwarden-yourname"
version = "0.1.0"
requires-python = ">=3.12.7"
dependencies = ["dbwarden>=0.15.0"]

[project.entry-points."dbwarden.plugins"]
yourname = "dbwarden_yourname:setup"

[tool.setuptools.packages.find]
where = ["src"]
```

Depend on DBWarden with a lower bound. The plugin API is stable within the `0.x` series; you can also cap the upper bound (`dbwarden>=0.15.0,<1.0`) if you want a core update to never surprise you.

The included `.github/workflows/test.yml` runs the conformance suite on every push. Link a green run when you request the Verified badge.

Consider PyPI Trusted Publishing (publishing from GitHub Actions with OIDC), which attaches a PEP 740 attestation to your release. DBWarden verifies that attestation for official plugins during `dbwarden plugin add`. Trusted Publishing alone does not make a plugin official; the Official tier is the curated list in core.

## Installing and using a plugin

For someone consuming your plugin:

```bash
dbwarden plugin add dbwarden-yourname
```

For official plugins this verifies provenance before installing. For community plugins it installs the package, then you consent once:

```bash
dbwarden plugin trust dbwarden-yourname
```

You can also install with your package manager directly:

```bash
uv add dbwarden-yourname
# or
pip install dbwarden-yourname
```

Inspect what DBWarden discovered:

```bash
dbwarden plugin list
dbwarden plugin info dbwarden-yourname
```

There is no wiring step. Once installed and trusted, the plugin is discovered and its `setup()` registers its hooks. Core resolves them where it needs them and falls back to built-in behavior when a hook is absent.

## Reference

- [Plugin docs index](https://github.com/dbwarden/dbwarden/blob/main/docs/plugins/index.md)
- [Hook catalog](https://github.com/dbwarden/dbwarden/blob/main/docs/plugins/reference/hook-catalog.md)
- [Ordering anchors](https://github.com/dbwarden/dbwarden/blob/main/docs/plugins/reference/ordering-anchors.md)
- [Object plugins](https://github.com/dbwarden/dbwarden/blob/main/docs/plugins/developing/object-plugins.md)
- [Approved plugin standard](https://github.com/dbwarden/dbwarden/blob/main/docs/plugins/developing/approved-standard.md)
- [Plugin CLI reference](https://github.com/dbwarden/dbwarden/blob/main/docs/plugins/reference/plugin-cli.md)

## License

MIT
