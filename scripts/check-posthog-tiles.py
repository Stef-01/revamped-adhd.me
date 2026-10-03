#!/usr/bin/env python3
"""Check every dashboard tile against PostHog's own definitions before it is sent. Exit 1 on any failure.

    python3 scripts/check-posthog-tiles.py

Two checks, neither of which needs a PostHog key:
  - each tile's query is validated against PostHog's pydantic schema (posthog/schema.py, fetched from
    PostHog's repository, which forbids unknown fields), so a misspelt field or a value PostHog does not
    accept fails here rather than as a bare 400 halfway through a dashboard run;
  - each SQL tile is parsed by PostHog's own HogQL parser (the hogql-parser package), when it is installed.

The schema files are fetched once into a cache directory (POSTHOG_SCHEMA_DIR, default ~/.cache/adhdme-posthog)
and reused; delete the directory to fetch the current ones. pydantic is required; hogql-parser is optional
locally and installed in CI (.github/workflows/posthog-sync.yml).
"""
import importlib.util
import json
import os
import pathlib
import ssl
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = pathlib.Path(os.environ.get('POSTHOG_SCHEMA_DIR', pathlib.Path.home() / '.cache' / 'adhdme-posthog'))
RAW = 'https://raw.githubusercontent.com/PostHog/posthog/master/posthog/'
# schema.py imports the two beside it; hogql-parser imports posthog.hogql.errors and nothing else from PostHog.
FILES = ['schema.py', 'schema_enums.py', 'schema_discriminators.py', 'hogql/errors.py']


def fetch():
    try:
        import certifi   # python.org builds of Python ship without a CA bundle
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()
    for name in FILES:
        target = CACHE / 'posthog' / name
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(RAW + name, context=context, timeout=60) as r:
            target.write_bytes(r.read())
    for package in (CACHE / 'posthog', CACHE / 'posthog' / 'hogql'):
        (package / '__init__.py').touch()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    fetch()
    sys.path.insert(0, str(CACHE))
    import posthog.schema as schema
    dash = load('dashboard', ROOT / 'scripts' / 'posthog-dashboard.py')
    models = {'InsightVizNode': schema.InsightVizNode, 'DataVisualizationNode': schema.DataVisualizationNode}
    try:
        import hogql_parser
    except ImportError:
        hogql_parser = None

    problems, sql_tiles = [], 0
    for name, _, query in dash.tiles():
        model = models.get(query['kind'])
        if model is None:
            problems.append(f'{name}: no schema check for a {query["kind"]} tile')
            continue
        try:
            model.model_validate(query)
        except Exception as e:   # pydantic.ValidationError, reported in full
            problems.append(f'{name}: {e}')
        if query['kind'] == 'DataVisualizationNode' and hogql_parser:
            sql_tiles += 1
            parsed = json.loads(hogql_parser.parse_select_json(query['source']['query']))
            if parsed.get('error'):
                problems.append(f'{name}: HogQL does not parse: {parsed.get("message")}')

    if problems:
        print('\n'.join(problems))
        return 1
    parsed = f', {sql_tiles} SQL tiles parsed' if hogql_parser else ' (SQL not parsed: pip install hogql-parser)'
    print(f'posthog tiles: {len(dash.tiles())} match the PostHog schema{parsed}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
