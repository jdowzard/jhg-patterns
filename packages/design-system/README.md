# JHG Design System

Complete UI framework for JHG Flask applications with Databricks backend.

## Installation

```bash
# Basic installation
pip install jhg-patterns-ds

# With Flask support (CSRF, rate limiting, CORS)
pip install jhg-patterns-ds[flask]

# With Databricks support
pip install jhg-patterns-ds[databricks]

# Everything
pip install jhg-patterns-ds[all]
```

## Quick Start

```python
from jhg_patterns.ds import create_app

# Create app with JHG default theme
app = create_app("my-app")

if __name__ == "__main__":
    app.run(debug=True)
```

## Features

### Theme System

Customizable colors, typography, and design tokens.

```python
from jhg_patterns.ds import Theme, DesignSystem

# Use default JHG theme
theme = Theme.jhg()

# Load custom theme from YAML
theme = Theme.from_yaml("theme.yaml")

# Get Tailwind config
tailwind_config = theme.get_tailwind_config()

# Get CSS variables
css_vars = theme.get_css_variables()
```

### Component Library

Jinja2 macros for all UI components:

```jinja
{% from "macros/buttons.html" import button %}
{% from "macros/badges.html" import badge, status_badge %}
{% from "macros/cards.html" import card, summary_card %}
{% from "macros/alerts.html" import alert, flash_messages %}
{% from "macros/forms.html" import input, select, textarea %}
{% from "macros/tables.html" import data_table, pagination %}
{% from "macros/modals.html" import modal, confirm_modal %}
{% from "macros/layout.html" import page_header, breadcrumb, empty_state %}

{# Buttons #}
{{ button("Save", variant="primary") }}
{{ button("Cancel", variant="secondary", href="/") }}
{{ button("Delete", variant="danger", disabled=true) }}

{# Badges #}
{{ badge("New", variant="info") }}
{{ status_badge("Active", status="success") }}

{# Cards #}
{% call card(title="My Card") %}
    Card content here
{% endcall %}

{{ summary_card("Total Revenue", "$125,000", change="+12.5%") }}

{# Alerts #}
{{ alert("Success!", "Changes saved.", variant="success", dismissible=true) }}
{{ flash_messages() }}

{# Forms #}
{{ input("email", label="Email", type="email", required=true) }}
{{ select("country", label="Country", options=countries) }}

{# Tables #}
{{ data_table(rows, columns=["Name", "Email", "Status"]) }}
{{ pagination(page, total_pages, "/users") }}

{# Modals #}
{% call modal("edit-modal", title="Edit User") %}
    Modal content
{% endcall %}

{{ confirm_modal("delete-modal", title="Delete?", action="/delete") }}
```

### Flask Integration

App factory with built-in middleware:

```python
from jhg_patterns.ds import create_app, AppConfig
from jhg_patterns.ds.app import CacheConfig, SecurityConfig

app = create_app(AppConfig(
    name="my-app",
    cache=CacheConfig(
        enabled=True,
        default_ttl=600,
        ttls={"dashboard_": 300},
    ),
    security=SecurityConfig(
        csrf_enabled=True,
        rate_limiting_enabled=True,
        rate_limit_default="200 per day, 50 per hour",
    ),
    enable_health_check=True,
    enable_cache_api=True,
))
```

Built-in endpoints:
- `GET /health` - Health check with Databricks status
- `GET /api/cache/stats` - Cache statistics
- `POST /api/cache/refresh` - Refresh cache key
- `POST /api/cache/invalidate` - Invalidate cache entries

### Databricks Utilities

```python
from jhg_patterns.ds.databricks import DatabricksConnector, AuditLogger, TTLCache

# SQL Connector
connector = DatabricksConnector(config)
rows = connector.query("SELECT * FROM users WHERE id = :id", {"id": 123})
user = connector.query_one("SELECT * FROM users WHERE id = :id", {"id": 123})

# Audit Logging
audit = AuditLogger(connector, app_name="my-app")
audit.log("user_login", user_id="123", ip_address="192.168.1.1")
audit.log_request("api_call")  # From Flask request

# TTL Cache
cache = TTLCache(default_ttl=600)
data = cache.get("my_key", loader=lambda: fetch_from_db())

@cache.cached("expensive_query", ttl=1800)
def get_dashboard_data():
    return connector.query("SELECT * FROM dashboard_metrics")
```

## Theme Customization

Create a `theme.yaml`:

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
  font_family:
    - Inter
    - system-ui
    - sans-serif

gradient:
  - [primary, 60]
  - [secondary, 80]
  - [tertiary, 100]
```

## CSS Classes

All component classes are prefixed with `ds-`:

### Buttons
- `ds-btn`, `ds-btn-primary`, `ds-btn-secondary`, `ds-btn-outline`
- `ds-btn-danger`, `ds-btn-success`, `ds-btn-ghost`
- `ds-btn-sm`, `ds-btn-lg`

### Cards
- `ds-card`, `ds-card-header`, `ds-card-body`, `ds-card-footer`
- `ds-card-hover`
- `ds-summary-card`

### Badges
- `ds-badge`, `ds-badge-success`, `ds-badge-error`, `ds-badge-warning`
- `ds-badge-info`, `ds-badge-neutral`

### Alerts
- `ds-alert`, `ds-alert-success`, `ds-alert-error`, `ds-alert-warning`, `ds-alert-info`

### Forms
- `ds-form-group`, `ds-label`, `ds-input`, `ds-select`, `ds-input-error`
- `ds-helper-text`, `ds-error-text`

### Tables
- `ds-table-container`, `ds-table`, `ds-table-sortable`

### Modals
- `ds-modal-backdrop`, `ds-modal`, `ds-modal-header`, `ds-modal-body`, `ds-modal-footer`

### Layout
- `ds-page`, `ds-page-content`
- `ds-nav`, `ds-nav-brand`, `ds-nav-link`
- `ds-footer`
- `ds-gradient-bar`
- `ds-empty-state`, `ds-progress`, `ds-progress-bar`

## Example App

See `examples/demo_app/` for a complete example application demonstrating all features.

```bash
cd examples/demo_app
uv run flask run --debug
```

## Schema Template

See `examples/schema/` for a Databricks schema template with:
- Audit log table
- Cache metadata table
- User preferences table
- Feature flags table
- Session storage table

## JHG Brand Colors

| Color | Hex | Usage |
|-------|-----|-------|
| JH Red | `#E63946` | Primary accent, CTAs |
| JH Cyan | `#5BC0DE` | Secondary, links, info |
| JH Purple | `#8B5CF6` | Tertiary, highlights |

Signature gradient: Red (60%) → Cyan (20%) → Purple (20%)
