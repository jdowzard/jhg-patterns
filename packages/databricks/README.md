# jhg-patterns-databricks

Databricks utilities for JHG projects - Unity Catalog helpers and SQL connector wrappers.

## Installation

```bash
pip install jhg-patterns-databricks

# With SQL connector
pip install jhg-patterns-databricks[sql]

# With Databricks SDK
pip install jhg-patterns-databricks[sdk]

# Everything
pip install jhg-patterns-databricks[all]
```

## Unity Catalog Utilities

```python
from jhg_patterns.databricks import get_catalog_schema, get_table_path

# Get catalog/schema from environment
catalog, schema = get_catalog_schema()

# Build table paths
users_table = get_table_path('users')  # "main.default.users"
```

### Environment Variables

```bash
DATABRICKS_CATALOG=ai_a
DATABRICKS_SCHEMA=rei
```

## SQL Connector

Requires `pip install jhg-patterns-databricks[sql]`

```python
from jhg_patterns.databricks.sql import execute_query, get_connection, check_connection

# Simple query
users = execute_query("SELECT * FROM users")

# Parameterized query
active = execute_query(
    "SELECT * FROM users WHERE active = :active",
    {"active": True}
)

# Context manager for multiple queries
with get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

# Health check
if check_connection():
    print("Databricks connected")
```

### Environment Variables

```bash
DATABRICKS_HOST=https://adb-xxxxx.azuredatabricks.net
DATABRICKS_TOKEN=dapi...
DATABRICKS_SQL_PATH=/sql/1.0/warehouses/xxxxx
```

## Combining with Flask Cache

Use with `jhg-patterns-flask` for cached Databricks queries:

```python
from jhg_patterns.flask import TTLCache
from jhg_patterns.databricks import get_table_path
from jhg_patterns.databricks.sql import execute_query

cache = TTLCache(default_ttls={'users': 1800})

def get_users():
    def fetch():
        table = get_table_path('users')
        return execute_query(f"SELECT * FROM {table}")

    return cache.get('users', fetch_fn=fetch)
```
