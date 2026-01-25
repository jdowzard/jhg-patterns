# jhg-patterns

Reusable patterns for JHG projects - Design System, Flask utilities, Databricks integration.

## Project Overview

This is a Python monorepo using **uv workspaces** with pip-installable packages under the `jhg_patterns` namespace.

## Structure

```
jhg-patterns/
├── pyproject.toml                    # uv workspace root
├── packages/
│   ├── design-system/                # jhg-patterns-ds (main package)
│   │   ├── pyproject.toml
│   │   ├── src/jhg_patterns/ds/
│   │   │   ├── __init__.py           # Exports: Theme, DesignSystem, create_app, AppConfig
│   │   │   ├── theme.py              # Theme system (colors, typography, tokens)
│   │   │   ├── system.py             # DesignSystem class, CSS generation
│   │   │   ├── app.py                # Flask app factory, configs
│   │   │   ├── blueprints/           # Flask blueprints (health, cache)
│   │   │   ├── databricks/           # Databricks utilities
│   │   │   │   ├── connector.py      # SQL connector wrapper
│   │   │   │   ├── audit.py          # Audit logging to Delta tables
│   │   │   │   └── cache.py          # TTL cache
│   │   │   ├── templates/            # Jinja2 templates
│   │   │   │   ├── base.html         # Base layout template
│   │   │   │   ├── macros/           # Component macros
│   │   │   │   └── errors/           # Error page templates
│   │   │   ├── themes/               # YAML theme files
│   │   │   │   └── jhg.yaml          # JHG default theme
│   │   │   └── assets/               # Static assets
│   │   │       └── images/           # Logo, favicon
│   │   └── examples/
│   │       ├── demo_app/             # Example Flask app
│   │       │   ├── app.py
│   │       │   ├── config.yaml       # App configuration
│   │       │   ├── theme.yaml        # Theme configuration
│   │       │   └── templates/
│   │       └── schema/               # Databricks schema template
│   │           ├── create_schema.sql
│   │           └── README.md
│   ├── flask/                        # jhg-patterns-flask (legacy)
│   ├── web/                          # jhg-patterns-web (legacy)
│   └── databricks/                   # jhg-patterns-databricks (legacy)
└── tests/
```

## Installation

```bash
# Install design system
pip install jhg-patterns-ds

# With Flask extras
pip install jhg-patterns-ds[flask]

# With Databricks extras
pip install jhg-patterns-ds[databricks]

# Everything
pip install jhg-patterns-ds[all]
```

## Configuration (YAML)

All configuration uses YAML files for consistency.

### App Configuration (`config.yaml`)

```yaml
name: "My App"
theme: "theme.yaml"  # Path to theme file (relative to config)

cache:
  enabled: true
  default_ttl: 600
  ttls:
    dashboard_: 300
    users_: 120

security:
  csrf_enabled: true
  rate_limiting_enabled: true
  rate_limit_default: "200 per day, 50 per hour"
  cors_enabled: true
  cors_origins: "*"

databricks:
  catalog: "main"
  schema: "default"
  # host, token, sql_path from environment

enable_health_check: true
enable_cache_api: true
enable_error_pages: true
debug: false
```

### Theme Configuration (`theme.yaml`)

```yaml
name: my-theme

colors:
  primary:
    DEFAULT: "#E63946"
    dark: "#C5303C"
    light: "#F5A3A9"
    bg: "#FEF2F2"
  secondary:
    DEFAULT: "#5BC0DE"
    dark: "#3AA8C7"
    light: "#A8DFF0"
    bg: "#ECFEFF"
  tertiary:
    DEFAULT: "#8B5CF6"
    dark: "#7C3AED"
    light: "#C4B5FD"
    bg: "#F5F3FF"

typography:
  font_family: [Inter, system-ui, sans-serif]
  font_mono: [JetBrains Mono, Consolas, monospace]

gradient:
  - [primary, 60]
  - [secondary, 80]
  - [tertiary, 100]

components:
  navbar:
    bg: gray-700
    height: 4rem
    gradient_bar: true
```

## Quick Start

```python
from jhg_patterns.ds import create_app

# From YAML config
app = create_app("config.yaml")

# Or programmatic
from jhg_patterns.ds import AppConfig, Theme
app = create_app(AppConfig(name="my-app", theme=Theme.jhg()))
```

## Development

```bash
# Install all packages in dev mode
uv sync --all-packages

# Run example app
cd packages/design-system/examples/demo_app
uv run flask run --debug

# Run tests
uv run pytest
```

## JHG Brand

| Color | Hex | CSS Variable |
|-------|-----|--------------|
| JH Red | `#E63946` | `--primary` |
| JH Cyan | `#5BC0DE` | `--secondary` |
| JH Purple | `#8B5CF6` | `--tertiary` |

**Gradient bar:** Red 60% → Cyan 20% → Purple 20%

## Jinja2 Macros

```jinja
{% from "macros/buttons.html" import button %}
{% from "macros/badges.html" import badge, status_badge %}
{% from "macros/cards.html" import card, summary_card %}
{% from "macros/alerts.html" import alert, flash_messages %}
{% from "macros/forms.html" import input, select, textarea %}
{% from "macros/tables.html" import data_table, pagination %}
{% from "macros/modals.html" import modal, confirm_modal %}
{% from "macros/layout.html" import page_header, breadcrumb, empty_state %}
```

## CSS Classes

All classes prefixed with `ds-`:
- Buttons: `ds-btn`, `ds-btn-primary`, `ds-btn-secondary`, `ds-btn-danger`
- Cards: `ds-card`, `ds-card-header`, `ds-card-body`
- Badges: `ds-badge`, `ds-badge-success`, `ds-badge-error`
- Alerts: `ds-alert`, `ds-alert-warning`
- Forms: `ds-input`, `ds-select`, `ds-label`
- Tables: `ds-table`, `ds-table-container`
- Modals: `ds-modal`, `ds-modal-backdrop`
- Layout: `ds-page`, `ds-nav`, `ds-footer`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with Databricks status |
| `/api/cache/stats` | GET | Cache statistics |
| `/api/cache/refresh` | POST | Refresh cache key |
| `/api/cache/invalidate` | POST | Invalidate cache entries |
| `/ds/css` | GET | Generated CSS stylesheet |
| `/favicon.ico` | GET | AIJH favicon |

## Databricks Integration

```python
from jhg_patterns.ds.databricks import DatabricksConnector, AuditLogger, TTLCache

# Query
connector = DatabricksConnector(config)
rows = connector.query("SELECT * FROM users WHERE id = :id", {"id": 123})

# Audit
audit = AuditLogger(connector, app_name="my-app")
audit.log("user_login", user_id="123")

# Cache
cache = TTLCache(default_ttl=600)

@cache.cached("key", ttl=300)
def get_data():
    return connector.query("SELECT * FROM data")
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABRICKS_HOST` | Databricks workspace hostname |
| `DATABRICKS_TOKEN` | Databricks access token |
| `DATABRICKS_SQL_PATH` | SQL warehouse HTTP path |
| `DATABRICKS_CATALOG` | Unity Catalog name (default: main) |
| `DATABRICKS_SCHEMA` | Schema name (default: default) |
| `FLASK_SECRET_KEY` | Flask session secret (auto-generated if not set) |

## Namespace Packages

Uses PEP 420 namespace packages. The `jhg_patterns/` directory in each package has NO `__init__.py`, allowing separate installation:

```python
from jhg_patterns.ds import create_app      # design-system package
from jhg_patterns.flask import TTLCache     # flask package (legacy)
```
