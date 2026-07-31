# dbwarden-plugin-template

[![Python](https://img.shields.io/badge/Python-3.12.7%2B-3776AB?logo=python&logoColor=white&style=for-the-badge)](https://www.python.org/downloads/)
[![CI](https://img.shields.io/github/actions/workflow/status/dbwarden-org/dbwarden-plugin-template/test.yml?logo=github&logoColor=white&style=for-the-badge)](https://github.com/dbwarden-org/dbwarden-plugin-template/actions/workflows/test.yml)

A GitHub template repository for building [DBWarden](https://dbwarden.emiliano-go.com) plugins.

Click **Use this template**, run one command, and you have a working, tested, publishable plugin with the layout every official DBWarden plugin uses: a `src/` package, `setup(registrar)` in `__init__.py`, a `dbwarden.plugins` entry point, the conformance suite, and CI that tests and publishes.

Full documentation lives at **[dbwarden.emiliano-go.com/plugins](https://dbwarden.emiliano-go.com/plugins/)**. This README is the hands-on guide; the docs are the reference.

## Contents

- [Quick start](#quick-start)
- [What you get](#what-you-get)
- [Value plugins and object plugins](#value-plugins-and-object-plugins)
- [Naming rule](#naming-rule)
- [Writing a value plugin](#writing-a-value-plugin)
- [Writing an object plugin](#writing-an-object-plugin)
- [Importing from DBWarden core](#importing-from-dbwarden-core)
- [Testing your plugin](#testing-your-plugin)
- [The conformance suite](#the-conformance-suite)
- [Trust tiers](#trust-tiers)
- [Publishing](#publishing)
- [Checklist](#checklist)
- [Reference](#reference)

## Quick start

1. Click **Use this template** on GitHub and create your repository.

2. Clone it and rename the placeholders:

   ```bash
   python bootstrap.py dbwarden-yourname
   ```

   This rewrites `pyproject.toml`, the workflows, the package, the tests, and this README, then deletes itself. To rename by hand instead, replace `dbwarden-example`, `dbwarden_example`, and the entry-point key `example`, then rename `src/dbwarden_example/`.

3. Install and run the tests:

   ```bash
   uv sync --dev
   uv run pytest -q
   ```

   Or with pip: `pip install -e . pytest && pytest -q`.

4. Set the author and URLs in `pyproject.toml`, then start replacing the example hook with your own.

You now have a green test suite. Keep it green as you work; the conformance tests catch the mistakes that make a plugin fail on a user's machine rather than in your editor.

## What you get

```
.github/workflows/test.yml       CI: pytest on 3.12 and 3.13
.github/workflows/publish.yml    Release to PyPI via Trusted Publishing
pyproject.toml                   Package metadata and the entry point
src/dbwarden_example/__init__.py setup(registrar) and the example hook
tests/conftest.py                Registers the plugin for its own tests
tests/test_conformance.py        The shared conformance suite
tests/test_example.py            Behavior tests, to replace with your own
bootstrap.py                     One-shot renamer, deletes itself
```

Every official DBWarden plugin uses exactly this layout. Matching it means a reviewer knows where to look, and it is what the approval process expects.

## Value plugins and object plugins

A plugin is a normal Python package that extends DBWarden without patching it. There are two kinds, and one package may be both.

**Value plugins** supply a value at a named hook. Core calls the hook wherever optional behavior belongs: a session dependency, a lifespan, health routes, seed commands, a module loader. You register callables by name.

**Object plugins** teach DBWarden's schema diff about a new database object type: PostgreSQL extensions, roles, grants, policies, custom types, ClickHouse RBAC. You register a handler that participates in extract, canonicalize, diff, and emit.

The template ships as a value plugin because it is the shorter of the two. Switching to an object plugin is described below.

## Naming rule

DBWarden derives everything from the distribution name, so pick it first.

| | Rule | Example |
|---|---|---|
| Distribution | `dbwarden-<name>` | `dbwarden-audit-log` |
| Slug | distribution minus `dbwarden-`, hyphens to underscores | `audit_log` |
| Import package | `dbwarden_` + slug | `dbwarden_audit_log` |
| Entry-point key | the slug | `audit_log` |

```toml
[project.entry-points."dbwarden.plugins"]
audit_log = "dbwarden_audit_log:setup"
```

`bootstrap.py` applies all of this for you.

## Writing a value plugin

A value hook is a plain function registered under a name core knows. Core calls it with a documented signature.

```python
def load_model_module(path, base_dir):
    ...


def setup(registrar) -> None:
    registrar.register("load_model_module", load_model_module)
```

The hooks core currently calls:

| Hook | Called for |
|---|---|
| `session_factory`, `sync_session_factory` | Request-scoped database sessions |
| `clickhouse_session_factory`, `clickhouse_sync_session_factory` | ClickHouse clients |
| `load_model_module`, `load_config_module` | Turning a file path into a module |
| `lifespan` | Application startup and shutdown |
| `health_routes`, `migration_routes` | HTTP routers |
| `seed_create`, `seed_apply`, `seed_list`, `seed_rollback`, `seed_export` | The `dbwarden seed` commands |

Signatures for each are in the [hook catalog](https://dbwarden.emiliano-go.com/plugins/reference/hook-catalog/). Match them exactly: `test_hook_signature_compliance` checks your function against the arguments core actually passes, so a mismatch fails in CI instead of mid-migration.

Most hooks accept exactly one provider. Two plugins registering the same single-value hook raises `HookConflictError` at call time. `health_routes` and `migration_routes` are the exceptions and accept several.

See [value plugins](https://dbwarden.emiliano-go.com/plugins/developing/value-plugins/) for the full guide.

## Writing an object plugin

An object plugin adds a type to the schema diff. Create `src/<package>/handler.py`:

```python
from dbwarden.engine.core import (
    Anchor,
    MigrationStatement,
    Op,
    OrderingConstraint,
    RunPhase,
)


class WidgetHandler:
    object_type = "widget"
    op_types = ("create_widget", "drop_widget")
    run_phase = RunPhase.PREAMBLE
    ordering = OrderingConstraint(
        after=(Anchor.PREAMBLE,),
        before=(Anchor.BEFORE_TABLES,),
    )

    def extract(self, snapshot): ...               # live database to spec
    def model_spec_from_config(self, config): ...  # config to spec
    def model_spec_from_tables(self, tables): ...  # models to spec
    def canonicalize(self, spec): ...              # normalize for comparison
    def diff(self, snap_spec, model_spec): ...     # to (upgrade_ops, rollback_ops)
    def emit(self, op, db_name=None, **kw): ...    # Op to [MigrationStatement]
```

Then in `__init__.py`:

```python
from dbwarden_example.handler import WidgetHandler

HANDLER_CLASSES = (WidgetHandler,)


def setup(registrar) -> None:
    for handler_class in HANDLER_CLASSES:
        registrar.register_object_handler(handler_class())
```

The `HANDLER_CLASSES` tuple is a convention worth keeping: the conformance suite parametrizes over it, so every handler you add is covered automatically.

Two rules that catch people out:

- **Order with anchors, never integers.** `PREAMBLE`, `BEFORE_TABLES`, `AFTER_TABLES`, `AFTER_CONSTRAINTS`, `AFTER_INDEXES`, `POSTAMBLE`. DBWarden derives the private `statement_order` from them at registration. That derivation is also why `emit()` only works on a registered handler, which is why the template's tests register before asserting.
- **Emit SQL the way core does.** `dbwarden.engine.core.plugin_api` exposes the shared helpers: `quote_pg`, `qualified_name`, the grant and policy builders, `emit_with_cluster` for ClickHouse `ON CLUSTER`, and secret redaction. Use them rather than reimplementing, so your SQL cannot drift from the SQL core generates for neighbouring objects.

`object_type` is the registration key. Two different plugins claiming the same one raises `ObjectHandlerConflictError`; a plugin claiming the same type as a core handler overrides core, which is how official plugins replace built-in fallbacks. Overriding is announced, once per plugin and type per run:

```
WARNING  dbwarden.registry - Plugin 'dbwarden-yourname' overrides the built-in
handler for object type 'role'. Migration SQL for 'role' now comes from the
plugin, not DBWarden core.
```

If you override, expect to justify it when you apply for the Approved tier: you are taking over DDL generation for that object type.

See [object plugins](https://dbwarden.emiliano-go.com/plugins/developing/object-plugins/) and [ordering anchors](https://dbwarden.emiliano-go.com/plugins/reference/ordering-anchors/).

## Importing from DBWarden core

**You may import anything from `dbwarden`.** There is no allowlist. If you want `dbwarden.output` so your command output matches the rest of the CLI, or `dbwarden.repositories.*` to read a tracking table, import them.

Three surfaces are stable and change only on a major version:

- `dbwarden.plugin` (`PluginRegistrar`, the registries, the hook errors)
- `dbwarden.exceptions`
- `dbwarden.engine.core`, including `dbwarden.engine.core.plugin_api`

Prefer those where they cover your need, because they are what you will not have to revisit on a core upgrade. Anything deeper is supported but moves faster: pin your `dbwarden` dependency to the range you test against, and run CI against those versions. `plugin_conformance.core_imports_outside_stable_api(pkg)` lists your deeper imports so an upgrade has a checklist. It reports; it does not fail.

`test_core_imports_resolve` does fail, and it is the one that matters: it checks that every `dbwarden` module you import exists in the installed core. That turns "ImportError on a user's machine" into "red CI run".

One rule is absolute: **import lazily inside functions where you can**. Merely importing your package must not pull in heavy dependencies or, worse, register anything.

### Declaring the contract version

The plugin contract is versioned separately from DBWarden's release version. Your package declares which one it targets:

```python
DBWARDEN_PLUGIN_API = 1
```

Core refuses to load a plugin declaring a version it does not provide, listing it as `incompatible` with both versions named. That is the difference between "upgrade dbwarden-yourname" and an `AttributeError` halfway through generating someone's migration. Bump it only when you rebuild against a new contract version; adding hooks or helpers does not change it.

## Testing your plugin

`tests/conftest.py` registers your plugin before each test:

```python
@pytest.fixture(autouse=True)
def register_plugin():
    HookRegistry.clear()
    ObjectPluginRegistry.clear()
    dbwarden_example.setup(PluginRegistrar(PLUGIN_NAME))
    yield
    HookRegistry.clear()
    ObjectPluginRegistry.clear()
```

This matters more than it looks. Core reaches your code only through the registries, so anything exercising a real code path (a schema diff, a CLI command, a FastAPI dependency) sees nothing until `setup()` has run. The registries are process-global class state, so the fixture clears them on both sides: ordering stops mattering, and a second registration cannot trip a conflict error.

Write your behavior tests against the real thing where you can. For an object plugin that means running a snapshot through the diff pipeline and asserting on the SQL, not just calling `emit()` directly. `tests/test_example.py` shows both styles: one test through `HookRegistry`, one calling the function directly.

To develop against a local DBWarden checkout rather than the released one:

```bash
uv pip install -e ../dbwarden -e .
```

## The conformance suite

`tests/test_conformance.py` runs DBWarden's shared harness, `dbwarden.plugin_conformance`. Green means your plugin is a well-behaved citizen and is a prerequisite for the Verified badge.

| Test | Catches |
|---|---|
| `test_entry_point_is_declared` | Packaging that leaves the plugin undiscoverable |
| `test_import_has_no_side_effects` | Registering at import time, which bypasses the consent gate |
| `test_setup_registers_hooks` | A `setup()` that installs but silently does nothing |
| `test_hook_signature_compliance` | A `TypeError` when core calls your hook |
| `test_core_imports_resolve` | Importing a core module the installed DBWarden lacks |
| `test_api_version_is_declared` | Not declaring which plugin contract you target |
| `test_idempotent_setup` | Breaking when `setup()` runs twice |
| `test_object_handler_conformance` | Handlers that return wrong types and crash the diff |
| `test_ordering_constraint_satisfiable` | Ordering that can never be satisfied |

The last two are object-plugin only; the commented block at the bottom of the file has them ready to uncomment.

The suite checks contract adherence, not correctness or security. It does not read your SQL and it grants no sandboxing: a loaded plugin runs with full process privileges. Your own tests remain your responsibility.

See the [Approved standard](https://dbwarden.emiliano-go.com/plugins/developing/approved-standard/).

## Trust tiers

DBWarden classifies every plugin by distribution name **before importing any of its code**. Installing a plugin runs none of its logic.

| Tier | Loads automatically | Basis |
|---|---|---|
| Official | Yes | DBWarden-owned, PyPI attestation verified at install |
| Approved (Verified) | Yes, at or above the approved minimum version | Passed conformance and review |
| Community | No, consent required | Your explicit, version-specific consent |

Your plugin starts as community. Users install it and run `dbwarden plugin trust dbwarden-yourname` to enable it; consent is recorded per version in `.dbwarden/consent.toml`, so a new version needs fresh consent. This is why `test_import_has_no_side_effects` exists: registering at import time would run your code before the user agreed to it.

To apply for Approved, open a Plugin Approval issue on the DBWarden repository. Alongside the repo link and a green CI run, it asks for two declarations a test cannot make for you:

- **Core imports outside the stable API**, from `core_imports_outside_stable_api("your_package")`, with a reason for each. A reason that generalises is an argument for making the helper public in `plugin_api`, so this tends to work in your favour rather than against you.
- **Object type overrides**, if any handler claims a type core already owns.

See [consent and trust](https://dbwarden.emiliano-go.com/plugins/using-plugins/consent-and-trust/).

## Publishing

`publish.yml` releases through PyPI Trusted Publishing, so no API token is stored anywhere. Before your first release:

1. Create the project on PyPI, or reserve the name.
2. Add a Trusted Publisher: your `owner/repo`, workflow `publish.yml`, environment `pypi`.
3. Create a `pypi` environment in your repository settings.
4. Publish a GitHub Release. The workflow builds and uploads.

Keep the workflow file named `publish.yml`. PyPI records the workflow filename in the attestation, and renaming it breaks the match that verification relies on.

See [publishing](https://dbwarden.emiliano-go.com/plugins/developing/publishing/).

## Checklist

Before you tag a release:

- [ ] `bootstrap.py` has been run and is gone
- [ ] Author, description, and URLs set in `pyproject.toml`
- [ ] `dbwarden` dependency pinned to the range you actually test
- [ ] `VALUE_HOOKS` or `OBJECT_TYPES` in `test_conformance.py` matches `setup()`
- [ ] `tests/test_example.py` replaced with tests for your behavior
- [ ] `uv run pytest -q` green locally and in CI
- [ ] README rewritten to describe what your plugin does
- [ ] Trusted Publishing configured on PyPI
- [ ] Any core-handler overrides are intentional and documented

## Reference

- [Plugin documentation](https://dbwarden.emiliano-go.com/plugins/)
- [Quickstart](https://dbwarden.emiliano-go.com/plugins/quickstart/)
- [Developing: overview](https://dbwarden.emiliano-go.com/plugins/developing/overview/)
- [Value plugins](https://dbwarden.emiliano-go.com/plugins/developing/value-plugins/)
- [Object plugins](https://dbwarden.emiliano-go.com/plugins/developing/object-plugins/)
- [Approved standard](https://dbwarden.emiliano-go.com/plugins/developing/approved-standard/)
- [Publishing](https://dbwarden.emiliano-go.com/plugins/developing/publishing/)
- [Hook catalog](https://dbwarden.emiliano-go.com/plugins/reference/hook-catalog/)
- [Ordering anchors](https://dbwarden.emiliano-go.com/plugins/reference/ordering-anchors/)
- [Plugin CLI](https://dbwarden.emiliano-go.com/plugins/reference/plugin-cli/)
- [FAQ](https://dbwarden.emiliano-go.com/plugins/faq/)

## License

MIT
