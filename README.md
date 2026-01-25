# JHG Patterns

Reusable patterns for JHG (John Holland Group) projects. Install individual packages or everything together.

## Installation

```bash
# Install everything
pip install jhg-patterns

# Or install individual packages
pip install jhg-patterns-flask      # TTL caching, auth helpers
pip install jhg-patterns-web        # Brand styling, CSS, templates
pip install jhg-patterns-databricks # Unity Catalog, SQL utilities

# With optional dependencies
pip install jhg-patterns-flask[databricks]  # Flask + Databricks SQL
pip install jhg-patterns-databricks[sql]    # With SQL connector
pip install jhg-patterns-databricks[sdk]    # With Databricks SDK
```

## Development

This repo uses [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
# Install all packages in development mode
uv sync

# Install specific package
uv sync --package jhg-patterns-flask

# Run tests
uv run pytest
```

## Packages

### jhg-patterns-flask

Flask utilities including TTL caching for external data sources.

```python
from jhg_patterns.flask import TTLCache

# Create cache with custom TTLs
cache = TTLCache(default_ttls={
    'users': 3600,      # 1 hour
    'projects': 1800,   # 30 min
})

# Get data (fetches if cache expired)
users = cache.get('users', fetch_fn=lambda: db.query("SELECT * FROM users"))

# Invalidate on write
cache.invalidate('users')

# Get stats for monitoring
stats = cache.stats()
```

Configuration via environment variables:
- `CACHE_ENABLED=true` - Enable/disable caching
- `CACHE_TTL_DEFAULT=600` - Default TTL in seconds
- `CACHE_TTL_<KEY>=1800` - Per-key TTL override

### jhg-patterns-web

JHG brand styling - colors, CSS utilities, Jinja2 helpers.

```python
from jhg_patterns.web import BRAND_COLORS, get_tailwind_config
from jhg_patterns.web.templates import init_flask_app, badge_classes

# Initialize Flask with brand context
app = Flask(__name__)
init_flask_app(app)

# Use in templates: {{ jhg_gradient_bar }}, {{ jhg_tailwind_config }}

# Component helpers
classes = badge_classes('success')  # "inline-flex items-center ... bg-emerald-100 ..."
```

Copy static assets to your project:
```python
from jhg_patterns.web.templates import copy_static_assets
copy_static_assets('./static')
# Creates: ./static/css/jhg-brand.css, ./static/js/jhg-brand.js
```

#### Brand Colors

| Color | Hex | Usage |
|-------|-----|-------|
| JH Red | `#E63946` | Primary accent, CTAs, headers |
| JH Cyan | `#5BC0DE` | Secondary accent, links, info states |
| JH Purple | `#8B5CF6` | Tertiary accent, highlights |

Signature gradient: Red (60%) → Cyan (20%) → Purple (20%)

### jhg-patterns-databricks

Databricks utilities for Unity Catalog and SQL.

```python
from jhg_patterns.databricks import get_table_path
from jhg_patterns.databricks.sql import execute_query

# Get fully qualified table path
path = get_table_path('users')  # "catalog.schema.users"

# Execute SQL query
users = execute_query("SELECT * FROM users WHERE active = :active", {"active": True})
```

## Structure

```
jhg-patterns/
├── pyproject.toml              # Workspace root
├── packages/
│   ├── flask/                  # jhg-patterns-flask
│   │   └── src/jhg_patterns/flask/
│   ├── web/                    # jhg-patterns-web
│   │   └── src/jhg_patterns/web/
│   └── databricks/             # jhg-patterns-databricks
│       └── src/jhg_patterns/databricks/
└── docs/
```

Uses Python namespace packages (PEP 420) - packages can be installed separately but share the `jhg_patterns` namespace.

## License

MIT
