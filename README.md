# JHG Patterns

Reusable patterns for JHG (John Holland Group) Flask applications with Databricks integration.

## Installation

```bash
# Core design system
pip install jhg-patterns-ds

# With Flask security features
pip install jhg-patterns-ds[flask]

# With Databricks connector
pip install jhg-patterns-ds[databricks]

# With MS Graph/SharePoint support
pip install jhg-patterns-ds[graph]

# Everything
pip install jhg-patterns-ds[all]
```

## Quick Start

```python
from jhg_patterns.ds import create_app

# Create app from YAML config
app = create_app("config.yaml")

# Or programmatically
from jhg_patterns.ds import AppConfig, Theme
app = create_app(AppConfig(name="my-app", theme=Theme.jhg()))
```

## Features

### Theme System

Customizable colors, typography, and design tokens. JHG brand colors included.

```python
from jhg_patterns.ds import Theme

# Built-in JHG theme
theme = Theme.jhg()

# From YAML file
theme = Theme.from_yaml("theme.yaml")
```

### Authentication

Databricks Apps authentication with MS Graph integration.

```python
from jhg_patterns.ds import init_auth, login_required, get_current_user

init_auth(app)

@app.route('/protected')
@login_required
def protected():
    user = get_current_user()
    return f"Hello {user}"
```

### MS Graph & SharePoint

```python
from jhg_patterns.ds.graph import GraphClient
from jhg_patterns.ds.sharepoint import SharePointClient

# Send email
client = GraphClient.from_env()
client.send_email(to=["user@jhg.com.au"], subject="Test", body_html="<p>Hello</p>")

# Access SharePoint
sp = SharePointClient.from_graph(client, site_url="https://johnholland.sharepoint.com/sites/MySite")
items = sp.get_list_items("Tasks")
```

### Databricks Integration

```python
from jhg_patterns.ds.databricks import DatabricksConnector, AuditLogger, TTLCache

# Query with parameterized SQL
connector = DatabricksConnector(config)
rows = connector.query("SELECT * FROM users WHERE id = :id", {"id": 123})

# Audit logging
audit = AuditLogger(connector, app_name="my-app")
audit.log("user_login", user_id="123")

# Caching with TTL
cache = TTLCache(default_ttl=600)
data = cache.get("key", loader=lambda: connector.query("SELECT * FROM data"))
```

### API Utilities

Standardized JSON responses for Flask APIs.

```python
from jhg_patterns.ds.api import api_success, api_error, register_api_error_handlers

register_api_error_handlers(app)

@app.route('/api/users')
def list_users():
    return api_success(users, message="Users retrieved")
    # {"success": true, "data": [...], "message": "Users retrieved"}
```

### Retry Logic

```python
from jhg_patterns.ds.retry import with_retry, DATABRICKS_RETRY

@DATABRICKS_RETRY  # 3 attempts with exponential backoff
def query_databricks():
    return connector.query("SELECT * FROM table")
```

### Configuration

Pydantic-based configuration with YAML and environment variable support.

```python
from jhg_patterns.ds.config import AppSettings, load_config

# From environment
settings = AppSettings()

# From YAML with env override
settings = load_config("config.yaml", AppSettings)
```

### Logging

Color-coded console logging and JSON logging for production.

```python
from jhg_patterns.ds.logging import get_logger, configure_flask_logging

logger = get_logger(__name__, level="DEBUG")
configure_flask_logging(app, level="INFO")
```

## Jinja2 Macros

```jinja
{% from "macros/buttons.html" import button %}
{% from "macros/cards.html" import card, summary_card %}
{% from "macros/tables.html" import data_table, pagination %}
{% from "macros/forms.html" import input, select %}
{% from "macros/modals.html" import modal, confirm_modal %}
```

## Testing

```python
from jhg_patterns.ds.testing.fixtures import app, client, mock_databricks
from jhg_patterns.ds.testing.integration import requires_databricks, DatabricksTestCase

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200

@requires_databricks
def test_real_query():
    # Skipped if DATABRICKS_HOST not set
    pass
```

## CI/CD Templates

Copy workflow templates from `examples/github-actions/` to your `.github/workflows/`:

- `databricks-validate.yml` - Validate DAB on PR
- `python-test.yml` - Run pytest with coverage
- `flask-deploy.yml` - Deploy to Databricks Apps

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABRICKS_HOST` | Databricks workspace URL |
| `DATABRICKS_TOKEN` | Databricks access token |
| `DATABRICKS_SQL_PATH` | SQL warehouse HTTP path |
| `GRAPH_CLIENT_ID` | MS Graph app client ID |
| `GRAPH_CLIENT_SECRET` | MS Graph app client secret |
| `GRAPH_TENANT_ID` | Azure AD tenant ID |
| `FLASK_SECRET_KEY` | Flask session secret |

## Project Structure

```
jhg-patterns/
├── packages/
│   └── design-system/           # Main package (jhg-patterns-ds)
│       ├── src/jhg_patterns/ds/
│       │   ├── auth.py          # Databricks Apps auth
│       │   ├── graph.py         # MS Graph client
│       │   ├── sharepoint.py    # SharePoint REST API
│       │   ├── api.py           # API response helpers
│       │   ├── retry.py         # Retry decorators
│       │   ├── config.py        # Pydantic configuration
│       │   ├── logging.py       # Custom logging
│       │   ├── databricks/      # Databricks utilities
│       │   ├── testing/         # Test fixtures
│       │   └── templates/       # Jinja2 templates
│       └── examples/
│           ├── demo_app/        # Example Flask app
│           └── github-actions/  # CI/CD templates
└── tests/
```

## Development

```bash
# Install all packages in dev mode
uv sync --all-packages

# Run demo app
cd packages/design-system/examples/demo_app
uv run flask run --debug

# Run tests
uv run pytest
```

## License

MIT
