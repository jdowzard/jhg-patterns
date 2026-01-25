# jhg-patterns

Reusable patterns for JHG projects - Flask caching, web styling, Databricks utilities.

## Structure

```
jhg-patterns/
├── pyproject.toml              # uv workspace root
├── packages/
│   ├── flask/                  # jhg-patterns-flask
│   │   └── src/jhg_patterns/flask/
│   │       ├── __init__.py
│   │       └── cache.py        # TTLCache
│   ├── web/                    # jhg-patterns-web
│   │   └── src/jhg_patterns/web/
│   │       ├── __init__.py
│   │       ├── brand.py        # Colors, design tokens
│   │       ├── templates.py    # Flask integration
│   │       └── assets/         # Static CSS/JS
│   └── databricks/             # jhg-patterns-databricks
│       └── src/jhg_patterns/databricks/
│           ├── __init__.py
│           ├── unity.py        # Unity Catalog helpers
│           └── sql.py          # SQL connector wrapper
└── tests/
```

## Development

Uses uv for dependency management:

```bash
# Install all packages
uv sync

# Run tests
uv run pytest

# Install specific package
uv sync --package jhg-patterns-flask
```

## Namespace Packages

This repo uses Python namespace packages (PEP 420). The `jhg_patterns/` directory in each package has NO `__init__.py`, allowing separate installation while sharing the namespace.

```python
# After pip install jhg-patterns-flask
from jhg_patterns.flask import TTLCache

# After pip install jhg-patterns-web
from jhg_patterns.web import BRAND_COLORS
```

## Adding New Patterns

1. Create new package directory: `packages/<name>/`
2. Add `pyproject.toml` with name `jhg-patterns-<name>`
3. Create `src/jhg_patterns/<name>/` (no `__init__.py` in `jhg_patterns/`)
4. Add package to root `pyproject.toml` dependencies and sources
5. Write tests in `tests/`

## JHG Brand Colors

| Color | Hex | Usage |
|-------|-----|-------|
| JH Red | `#E63946` | Primary accent, CTAs |
| JH Cyan | `#5BC0DE` | Secondary, links, info |
| JH Purple | `#8B5CF6` | Tertiary, highlights |

Signature gradient: Red (60%) → Cyan (20%) → Purple (20%)
