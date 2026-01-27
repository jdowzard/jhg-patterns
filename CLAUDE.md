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
│   │   │   ├── auth.py               # Databricks Apps + MS Graph authentication
│   │   │   ├── graph.py              # MS Graph API client (email, users, groups)
│   │   │   ├── sharepoint.py         # SharePoint REST API (lists, files)
│   │   │   ├── api.py                # API response helpers, error handlers
│   │   │   ├── retry.py              # Retry decorator with exponential backoff
│   │   │   ├── config.py             # Pydantic-based configuration management
│   │   │   ├── logging.py            # Custom logging formatters (color, JSON)
│   │   │   ├── blueprints/           # Flask blueprints (health, cache)
│   │   │   ├── databricks/           # Databricks utilities
│   │   │   │   ├── connector.py      # SQL connector wrapper
│   │   │   │   ├── audit.py          # Audit logging to Delta tables
│   │   │   │   └── cache.py          # TTL cache
│   │   │   ├── testing/              # Test utilities
│   │   │   │   ├── fixtures.py       # Flask and Databricks test fixtures
│   │   │   │   └── integration.py    # Integration test base classes
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
│   │       ├── github-actions/       # CI/CD workflow templates
│   │       │   ├── databricks-validate.yml
│   │       │   ├── python-test.yml
│   │       │   └── flask-deploy.yml
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
{% from "macros/cards.html" import card, summary_card, list_card %}
{% from "macros/alerts.html" import alert, flash_messages %}
{% from "macros/forms.html" import input, select, textarea, filter_buttons, filter_or_select %}
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
- Filters: `ds-filter-group`, `ds-filter-btn`, `ds-filter-btn-active` (use for ≤6 options)
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

## Authentication

### Databricks Apps Auth

Works automatically in Databricks Apps (extracts user from `X-Forwarded-Preferred-Username` header) and locally with Databricks SDK.

```python
from jhg_patterns.ds import init_auth, login_required, require_role, get_current_user

# Initialize auth
init_auth(app)

# Protect routes
@app.route('/protected')
@login_required
def protected():
    user = get_current_user()
    return f"Hello {user}"

# Role-based access
@app.route('/admin')
@require_role('admin')
def admin():
    return "Admin only"
```

### MS Graph API

```python
from jhg_patterns.ds.graph import GraphClient

# From environment (GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET, GRAPH_TENANT_ID)
client = GraphClient.from_env()

# Send email
client.send_email(
    to=["user@example.com"],
    subject="Test",
    body_html="<p>Hello</p>"
)

# Get user info
user = client.get_user("user@example.com")
groups = client.get_user_groups("user@example.com")
```

### SharePoint

```python
from jhg_patterns.ds.sharepoint import SharePointClient

# Initialize
sp = SharePointClient(graph_client, site_id="contoso.sharepoint.com:/sites/MySite")

# List operations
items = sp.get_list_items("Tasks", select=["Title", "Status"])
sp.create_list_item("Tasks", {"Title": "New Task"})
sp.update_list_item("Tasks", item_id, {"Status": "Complete"})

# File operations
files = sp.list_folder("Shared Documents/Reports")
content = sp.download_file("Shared Documents/report.xlsx")
sp.upload_file("Shared Documents/new.xlsx", content)
```

## API Utilities

Standardized JSON response format for Flask APIs.

```python
from jhg_patterns.ds.api import api_success, api_error, register_api_error_handlers

# Register error handlers (400, 401, 403, 404, 500, 503)
register_api_error_handlers(app)

# Success response
@app.route('/api/users')
def list_users():
    users = get_users()
    return api_success(users, message="Users retrieved")
    # Returns: {"success": true, "data": [...], "message": "Users retrieved"}

# Error response
@app.route('/api/users/<id>')
def get_user(id):
    user = find_user(id)
    if not user:
        return api_error("User not found", status=404)
        # Returns: {"success": false, "error": "User not found", "errors": null}
    return api_success(user)
```

## Retry Patterns

Automatic retry with exponential backoff for transient failures.

```python
from jhg_patterns.ds.retry import with_retry, DATABRICKS_RETRY, GRAPH_RETRY, REQUEST_RETRY

# Custom retry
@with_retry(max_attempts=5, base_delay=0.5, max_delay=30,
            retryable_exceptions=(ConnectionError, TimeoutError))
def flaky_operation():
    return api_call()

# Pre-configured strategies
@DATABRICKS_RETRY  # 3 attempts, 1-30s backoff, retries DatabricksError/Connection/Timeout
def query_databricks():
    return connector.query("SELECT * FROM table")

@GRAPH_RETRY  # Same as above for GraphError
def send_email():
    return graph_client.send_email(...)

@REQUEST_RETRY  # 5 attempts, 0.5-60s backoff for HTTP requests
def fetch_json(url):
    return requests.get(url).json()
```

## Configuration (Pydantic)

Type-safe configuration with environment variable support.

```python
from jhg_patterns.ds.config import AppSettings, load_config

# Load from environment
settings = AppSettings()  # Reads DATABRICKS_HOST, DATABRICKS_TOKEN, etc.

# Load from YAML with env override
settings = load_config("config.yaml", AppSettings)

# Custom settings class
from pydantic import BaseModel, Field

class MySettings(BaseModel):
    app_name: str = Field(default="app")
    debug: bool = False
    databricks_host: str = ""
    api_timeout: int = Field(default=30, ge=1, le=300)

settings = load_config("config.yaml", MySettings)
```

Built-in settings classes: `AppSettings`, `DatabaseSettings`, `AuthSettings`, `CORSSettings`

## Logging

Color-coded console logging and JSON logging for production.

```python
from jhg_patterns.ds.logging import get_logger, get_json_logger, configure_flask_logging

# Console logger with colors
logger = get_logger(__name__, level="DEBUG", use_colors=True)
logger.info("Application started")  # Green
logger.error("Something failed")    # Red

# JSON logger for production
logger = get_json_logger(__name__)
logger.info("Event", extra={"user_id": 123})
# Output: {"timestamp": "...", "level": "INFO", "message": "Event", "user_id": 123}

# Configure Flask app logging
configure_flask_logging(app, level="INFO", use_colors=True)
```

## Testing

### Test Fixtures

```python
from jhg_patterns.ds.testing.fixtures import (
    app, client, mock_databricks,
    make_user, make_databricks_config, make_app_config
)

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200

def test_with_mock_db(mock_databricks):
    mock_databricks.return_value.query.return_value = [{"id": 1}]
    # Test code that uses DatabricksConnector

# Factory functions
user = make_user(id=1, name="Test", role="admin")
config = make_databricks_config(catalog="test_catalog")
```

### Integration Tests

```python
from jhg_patterns.ds.testing.integration import (
    requires_databricks, requires_graph,
    DatabricksTestCase, GraphAPITestCase
)

@requires_databricks  # Skips if DATABRICKS_HOST not set
def test_real_query():
    connector = DatabricksConnector.from_env()
    result = connector.query("SELECT 1")
    assert result

class TestDatabricks(DatabricksTestCase):
    def test_query(self):
        result = self.connector.query("SELECT 1")
        assert result
```

## CI/CD Templates

Copy from `examples/github-actions/` to your `.github/workflows/`:

| Template | Description |
|----------|-------------|
| `databricks-validate.yml` | Validate DAB on PR |
| `python-test.yml` | Run pytest with coverage |
| `flask-deploy.yml` | Deploy Flask app to Databricks Apps |

Required secrets: `DATABRICKS_HOST`, `DATABRICKS_TOKEN`

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABRICKS_HOST` | Databricks workspace hostname |
| `DATABRICKS_TOKEN` | Databricks access token |
| `DATABRICKS_SQL_PATH` | SQL warehouse HTTP path |
| `DATABRICKS_CATALOG` | Unity Catalog name (default: main) |
| `DATABRICKS_SCHEMA` | Schema name (default: default) |
| `GRAPH_CLIENT_ID` | MS Graph app client ID |
| `GRAPH_CLIENT_SECRET` | MS Graph app client secret |
| `GRAPH_TENANT_ID` | Azure AD tenant ID (default: common) |
| `FLASK_SECRET_KEY` | Flask session secret (auto-generated if not set) |

## Namespace Packages

Uses PEP 420 namespace packages. The `jhg_patterns/` directory in each package has NO `__init__.py`, allowing separate installation:

```python
from jhg_patterns.ds import create_app      # design-system package
from jhg_patterns.flask import TTLCache     # flask package (legacy)
```
