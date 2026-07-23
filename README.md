# dbwarden-plugin-template

A GitHub template repository for building [DBWarden](https://github.com/dbwarden/dbwarden) plugins. It ships the standardized plugin layout: a setuptools `src/` package with `setup(registrar)` in `__init__.py`, a `dbwarden.plugins` entry point, a passing test, and a CI workflow.

## Use It

Click **Use this template** on GitHub to create your own repository, then rename the placeholders:

```bash
python bootstrap.py dbwarden-yourname
```

`bootstrap.py` applies the standard naming rule, renames the package and test, and removes itself. To rename by hand instead, replace `dbwarden-example` / `dbwarden_example` / `example` and rename `src/dbwarden_example/` and `tests/test_example_plugin.py`.

Then verify:

```bash
pip install -e . pytest
pytest -q
```

## The Standard

Every DBWarden plugin follows one naming rule, derived from the distribution name:

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
│   └── __init__.py           # hook functions + setup(registrar)
└── tests/
    └── test_<name>_plugin.py
```

## What This Example Does

It is a **value plugin**: `setup()` registers a `load_model_module` hook (a stand-in you should replace). Define your own hook functions at module top level, import DBWarden internals lazily inside each function body, and register them in `setup()`. See the [hook catalog](https://github.com/dbwarden/dbwarden/blob/main/docs/plugins/reference/hook-catalog.md).

### Making an object plugin instead

To add a schema-diff object type, drop the value hook, add a `handler.py` with an `ObjectHandler`, and register it with `registrar.register_object_handler(...)`. The [`dbwarden-pgsql-extensions`](https://github.com/dbwarden/dbwarden-pgsql-extensions) plugin and the [object-plugin docs](https://github.com/dbwarden/dbwarden/blob/main/docs/plugins/developing/object-plugins.md) are the reference.
